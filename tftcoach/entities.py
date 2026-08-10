"""CommunityDragon -> a small local whitelist of real TFT entities.

Why this exists: OCR returns noisy strings ("Kai5a", "MissFortuneJinxAatrox").
Nothing noisy is allowed downstream — every champion/trait/item/augment name is
validated against this whitelist before it reaches a prompt, so Claude never
reasons about a unit that does not exist.

Set-agnostic by construction. The current set is derived at runtime as
max(int(k)) over the blob's "sets" keys, and the augment/item pools come from
the blob's own per-set `setData` entry (mutator "TFTSet<N>") rather than from
any hardcoded list. When Set 18 lands on Aug 26 2026 this module needs a
refresh, not an edit — and is_stale() shouts about the rollover.

Stdlib only (urllib/json/difflib) so it imports and runs with zero deps
installed. Python 3.9 compatible.
"""

from __future__ import annotations

import datetime
import difflib
import json
import os
import re
import shutil
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

try:  # normal package import
    from . import config
except ImportError:  # running the file loosely / from the package dir
    import config  # type: ignore

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

# difflib ratio a fuzzy match must reach to be trusted at all. Below this we
# return (None, 0.0) — an honest "unknown" beats a plausible wrong name.
MATCH_CUTOFF = 0.70

# A whitelist entry has to be at least this long before we allow it to be
# matched by containment/segmentation (stops "Ace" eating half a shop line).
MIN_SEGMENT_LEN = 4

SHOP_SLOTS = 5

_BIG_TIMEOUT = 120.0   # 25.9 MB blob
_SMALL_TIMEOUT = 10.0  # version probe
_UA = "TFTCoach/2.0 (+local coaching tool)"

# OCR confusion classes, applied to BOTH the query and the whitelist keys so
# they stay comparable: 0/O 1/l/I 5/S 8/B.
_OCR_TABLE = {ord("0"): "o", ord("1"): "l", ord("5"): "s", ord("8"): "b"}

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_SPLIT_CHARS = re.compile(r"[\n\r\t|,;:/\\]+|\s{2,}")

_KINDS = ("champion", "trait", "item", "augment")

# Module-level caches (built lazily, cheap to rebuild).
_CACHE: Optional[Dict[str, Any]] = None
_INDEX: Dict[str, Dict[str, str]] = {}          # kind -> {normkey: canonical}
_INDEX_BY_LEN: Dict[str, List[str]] = {}        # kind -> normkeys, longest first


# ---------------------------------------------------------------------------
# Empty-but-valid fallback. Every consumer can rely on these keys existing.
# ---------------------------------------------------------------------------

def _empty(reason: str) -> Dict[str, Any]:
    return {
        "set_number": 0,
        "set_name": "unknown",
        "set_prefix": "",
        "cdragon_version": "",
        "fetched": "",
        "champions": [],
        "traits": [],
        "items": [],
        "augments": [],
        "degraded": True,
        "degraded_reason": reason,
    }


# ---------------------------------------------------------------------------
# Text normalization + fuzzy matching
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Lowercase, de-accent, fix OCR digit/letter confusions, drop everything
    that is not alphanumeric (including spaces, so "MissFortune" == "Miss
    Fortune" == "Mi55 Fortune")."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", str(text))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower().translate(_OCR_TABLE)
    return _NON_ALNUM.sub("", t)


def _build_index(kind: str) -> Dict[str, str]:
    """{normalized -> canonical display name} for one kind."""
    data = load_entities()
    names: List[str] = []
    if kind == "champion":
        names = [c.get("name", "") for c in data.get("champions", [])]
    elif kind == "trait":
        names = [t.get("name", "") for t in data.get("traits", [])]
    elif kind == "item":
        names = list(data.get("items", []))
    elif kind == "augment":
        names = list(data.get("augments", []))
    idx: Dict[str, str] = {}
    for n in names:
        k = normalize(n)
        if k:
            idx.setdefault(k, n)
    return idx


def _index(kind: str) -> Dict[str, str]:
    if kind not in _KINDS:
        return {}
    if kind not in _INDEX:
        _INDEX[kind] = _build_index(kind)
        _INDEX_BY_LEN[kind] = sorted(_INDEX[kind], key=len, reverse=True)
    return _INDEX[kind]


def _shop_index() -> Dict[str, str]:
    """Shop-only champion index: playable units, no PVE monsters or summons."""
    if "_shop" not in _INDEX:
        data = load_entities()
        idx: Dict[str, str] = {}
        for c in data.get("champions", []):
            if c.get("playable"):
                k = normalize(c.get("name", ""))
                if k:
                    idx.setdefault(k, c["name"])
        _INDEX["_shop"] = idx
        _INDEX_BY_LEN["_shop"] = sorted(idx, key=len, reverse=True)
    return _INDEX["_shop"]


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _match_key(q: str, idx: Dict[str, str], keys_by_len: List[str]
               ) -> Tuple[Optional[str], float]:
    """Core matcher over an already-normalized query."""
    if not q or len(q) < 2 or not idx:
        return (None, 0.0)
    if q in idx:
        return (idx[q], 1.0)

    # Containment: OCR often glues junk onto a real name ("2Ahri*").
    best_key, best_conf = None, 0.0
    for k in keys_by_len:
        if len(k) < MIN_SEGMENT_LEN:
            break  # sorted longest-first, everything after is shorter too
        if k in q:
            conf = 0.9 * (len(k) / float(len(q)))
            if conf > best_conf:
                best_key, best_conf = k, conf
            break  # longest containing key wins
    if best_key is not None and best_conf >= MATCH_CUTOFF:
        return (idx[best_key], min(best_conf, 0.95))

    close = difflib.get_close_matches(q, list(idx.keys()), n=1, cutoff=MATCH_CUTOFF)
    if close:
        conf = _ratio(q, close[0])
        if conf >= MATCH_CUTOFF:
            return (idx[close[0]], conf)
    return (None, 0.0)


def match_name(text: str, kind: str) -> Tuple[Optional[str], float]:
    """Fuzzy-match noisy OCR text to the whitelist.

    kind in {"champion","trait","item","augment"}.
    Returns (canonical_name, confidence) or (None, 0.0) when nothing is close
    enough — callers must map that to Field(value=None, confidence=0.0).
    """
    if kind not in _KINDS:
        return (None, 0.0)
    idx = _index(kind)
    return _match_key(normalize(text), idx, _INDEX_BY_LEN.get(kind, []))


def _segment(nkey: str, idx: Dict[str, str], keys_by_len: List[str],
             limit: int) -> List[Tuple[str, float]]:
    """Greedy longest-match segmentation of a glued OCR run.

    Unmatched runs of >= MIN_SEGMENT_LEN chars get one fuzzy attempt, so a
    single misread letter in the middle of a shop line does not lose the unit.
    """
    out: List[Tuple[str, float]] = []
    i, n = 0, len(nkey)
    pending = ""

    def flush() -> None:
        nonlocal pending
        if len(pending) >= MIN_SEGMENT_LEN and len(out) < limit:
            name, conf = _match_key(pending, idx, keys_by_len)
            if name:
                out.append((name, conf * 0.9))  # segmentation is less certain
        pending = ""

    while i < n and len(out) < limit:
        hit = None
        for k in keys_by_len:
            if len(k) < 3:
                break
            if nkey.startswith(k, i):
                hit = k
                break
        if hit:
            flush()
            out.append((idx[hit], 1.0))
            i += len(hit)
        else:
            pending += nkey[i]
            i += 1
    flush()
    return out


def match_shop_line(text: str) -> List[str]:
    """Turn one messy shop-bar OCR string into up to 5 champion names.

    The shop OCR arrives as a single blob whose separators are unreliable, so
    we try the obvious split first and fall back to greedy segmentation of the
    glued string. Duplicates are kept — the shop really can show two Jinx.
    """
    if not text:
        return []
    idx = _shop_index()
    keys = _INDEX_BY_LEN.get("_shop", [])
    if not idx:
        return []

    names: List[str] = []
    for chunk in _SPLIT_CHARS.split(str(text)):
        if len(names) >= SHOP_SLOTS:
            break
        chunk = chunk.strip()
        if not chunk:
            continue
        q = normalize(chunk)
        if not q:
            continue
        name, conf = _match_key(q, idx, keys)
        if name and conf >= MATCH_CUTOFF and q in idx:
            names.append(name)
            continue
        seg = _segment(q, idx, keys, SHOP_SLOTS - len(names))
        if seg:
            names.extend(n for n, _ in seg)
        elif name and conf >= MATCH_CUTOFF:
            names.append(name)

    if not names:  # separators were useless — segment the whole thing
        seg = _segment(normalize(text), idx, keys, SHOP_SLOTS)
        names = [n for n, _ in seg]
    return names[:SHOP_SLOTS]


def whitelist(kind: str) -> List[str]:
    """Sorted canonical names for one kind — for prompt building / debugging."""
    return sorted(_index(kind).values())


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

def _urlopen(url: str, timeout: float):
    import urllib.request  # stdlib, but keep the import local & obvious
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    return urllib.request.urlopen(req, timeout=timeout)


def fetch_version() -> Optional[str]:
    """Cheap probe of CommunityDragon's content version (a few hundred bytes)."""
    try:
        with _urlopen(config.CDRAGON_VERSION_URL, _SMALL_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8", "replace"))
        v = payload.get("version")
        return str(v) if v else None
    except Exception:
        return None


def _download_blob_to(path: str) -> None:
    """Stream the 25.9 MB blob straight to disk in chunks — we never hold the
    raw text and a parsed copy in memory at the same time."""
    with _urlopen(config.CDRAGON_TFT_URL, _BIG_TIMEOUT) as resp:
        with open(path, "wb") as fh:
            shutil.copyfileobj(resp, fh, 1024 * 1024)


# ---------------------------------------------------------------------------
# Blob -> compact whitelist
# ---------------------------------------------------------------------------

def _clean_name(name: Optional[str], allow_leading_digit: bool = True) -> bool:
    """Reject CommunityDragon's non-names: unresolved template strings
    ("@Gold@ gold"), hashed tags ("{ce1fd21c}"), embedded markup ("<rules>"),
    raw localisation keys ("tft_item_name_Hush"), and — for items only — loot
    quantities ("2 Components")."""
    if not name:
        return False
    n = name.strip()
    if not n:
        return False
    if "@" in n or "{" in n or "}" in n or "<" in n or ">" in n or "_" in n:
        return False
    if not allow_leading_digit and n[0].isdigit():
        return False
    return True


def _is_equippable_item(api_name: str, icon: str) -> bool:
    """Keep components/completed/radiant/artifact items and trait emblems;
    drop loot grants, market offerings and shop pseudo-items. Both signals are
    path/name shaped, not set-specific, so this survives a set rollover."""
    a = (api_name or "").lower()
    ic = (icon or "").lower()
    if "augment" in a:
        return False
    if "item" not in a and "consumable" not in a:
        return False
    return ("/icons/items/" in ic) or ("item_icons/" in ic)


def _extract(blob: Dict[str, Any]) -> Dict[str, Any]:
    sets = blob.get("sets") or {}
    numeric = [int(k) for k in sets.keys() if str(k).isdigit()]
    if not numeric:
        raise ValueError("CommunityDragon blob has no numeric 'sets' keys")
    set_number = max(numeric)
    set_obj = sets[str(set_number)] or {}
    set_prefix = "TFT%d_" % set_number
    set_name = str(set_obj.get("name") or ("Set%d" % set_number))

    # -- champions --------------------------------------------------------
    champions: List[Dict[str, Any]] = []
    seen_champs = set()
    for c in set_obj.get("champions") or []:
        api = c.get("apiName") or ""
        name = c.get("name") or ""
        if not api.startswith(set_prefix) or not _clean_name(name):
            continue
        if name in seen_champs:
            continue
        seen_champs.add(name)
        cost = c.get("cost")
        traits = [t for t in (c.get("traits") or []) if t]
        # Playable = buyable from the shop. PVE monsters, summons and the
        # boss-fight clones carry no traits and/or a sentinel cost.
        playable = bool(traits) and isinstance(cost, int) and 1 <= cost <= 5
        champions.append({"name": name, "apiName": api, "cost": cost,
                          "traits": traits, "playable": playable})

    # -- traits -----------------------------------------------------------
    traits_out: List[Dict[str, str]] = []
    seen_traits = set()
    for t in set_obj.get("traits") or []:
        name = t.get("name") or ""
        if not _clean_name(name) or name in seen_traits:
            continue
        seen_traits.add(name)
        traits_out.append({"name": name, "apiName": t.get("apiName") or ""})

    # -- items + augments -------------------------------------------------
    # The per-set setData entry lists the exact live pools by apiName. That
    # matters: the Set 17 augment pool legitimately contains cross-set
    # apiNames (TFT10_Augment_*), which a prefix filter would silently drop.
    by_api: Dict[str, Dict[str, Any]] = {}
    for it in blob.get("items") or []:
        api = it.get("apiName")
        if api:
            by_api[api] = it

    set_data = None
    for sd in blob.get("setData") or []:
        if sd.get("mutator") == ("TFTSet%d" % set_number):
            set_data = sd
            break

    if set_data:
        item_pool = [by_api[a] for a in (set_data.get("items") or []) if a in by_api]
        aug_pool = [by_api[a] for a in (set_data.get("augments") or []) if a in by_api]
    else:  # fallback: prefix filter over the whole item array
        item_pool = [it for api, it in by_api.items()
                     if api.startswith((set_prefix, "TFT_"))]
        aug_pool = [it for api, it in by_api.items()
                    if api.startswith((set_prefix, "TFT_"))
                    and "augment" in api.lower()]

    items: List[str] = []
    seen_items = set()
    for it in item_pool:
        name = it.get("name") or ""
        if not _clean_name(name, allow_leading_digit=False):
            continue
        if not _is_equippable_item(it.get("apiName") or "", it.get("icon") or ""):
            continue
        if name not in seen_items:
            seen_items.add(name)
            items.append(name)

    augments: List[str] = []
    seen_augs = set()
    for it in aug_pool:
        name = it.get("name") or ""
        if not _clean_name(name):  # augment names may start with a digit
            continue
        if name not in seen_augs:
            seen_augs.add(name)
            augments.append(name)

    return {
        "set_number": set_number,
        "set_name": set_name,
        "set_prefix": set_prefix,
        "champions": champions,
        "traits": traits_out,
        "items": sorted(items),
        "augments": sorted(augments),
        "degraded": False,
    }


def _read_cache() -> Optional[Dict[str, Any]]:
    try:
        with open(config.ENTITIES_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "champions" in data:
            return data
    except (OSError, ValueError):
        pass
    return None


def _invalidate() -> None:
    global _CACHE
    _CACHE = None
    _INDEX.clear()
    _INDEX_BY_LEN.clear()


def fetch_entities(force: bool = False) -> Dict[str, Any]:
    """Download CommunityDragon, derive the current set, write a compact cache.

    force=False skips the 25.9 MB download when the cached cdragon_version
    still matches the live version probe. Never raises — on failure it returns
    the previous cache if there is one, otherwise an empty degraded structure.
    """
    global _CACHE
    config.ensure_dirs()
    old = _read_cache()

    live_version = fetch_version()
    if (not force and old and live_version
            and old.get("cdragon_version") == live_version):
        _CACHE = old
        return old

    tmp_path = config.ENTITIES_PATH + ".blob.tmp"
    try:
        _download_blob_to(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as fh:
            blob = json.load(fh)   # parsed from disk, not from an in-memory str
        try:
            data = _extract(blob)
        finally:
            del blob
    except Exception as exc:  # network, disk, or shape change — all non-fatal
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        if old:
            _CACHE = old
            return old
        return _empty("fetch failed: %s: %s" % (type(exc).__name__, exc))
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    data["cdragon_version"] = live_version or (
        old.get("cdragon_version", "") if old else "")
    data["fetched"] = datetime.datetime.now().isoformat(timespec="seconds")

    # SET ROLLOVER: the champion apiName prefix moved (TFT17_ -> TFT18_).
    # This is the Aug 26 2026 Set 18 event — the meta resets, every vault note
    # about comps goes stale, and regions.json probably needs recalibrating
    # because Set 18 renders on Unreal. It must be impossible to miss.
    old_prefix = (old or {}).get("set_prefix")
    if old_prefix and old_prefix != data["set_prefix"]:
        data["set_rollover"] = {
            "from": old_prefix,
            "to": data["set_prefix"],
            "from_set": (old or {}).get("set_number"),
            "to_set": data["set_number"],
            "detected": data["fetched"],
            "acknowledged": False,
        }
    elif old and old.get("set_rollover") and not old["set_rollover"].get("acknowledged"):
        data["set_rollover"] = old["set_rollover"]  # carry it until acknowledged

    try:
        with open(config.ENTITIES_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, separators=(",", ":"))
    except OSError:
        pass

    _invalidate()
    _CACHE = data
    return data


def load_entities() -> Dict[str, Any]:
    """Cached whitelist; fetches once if the cache is missing. Never raises."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    cached = _read_cache()
    if cached is not None:
        _CACHE = cached
        return cached
    try:
        return fetch_entities()
    except Exception as exc:  # belt and braces: this module may never crash
        _CACHE = _empty("load failed: %s: %s" % (type(exc).__name__, exc))
        return _CACHE


def acknowledge_rollover() -> None:
    """Mark a detected set rollover as seen, so the loud banner stops."""
    data = load_entities()
    roll = data.get("set_rollover")
    if not roll:
        return
    roll["acknowledged"] = True
    try:
        with open(config.ENTITIES_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, separators=(",", ":"))
    except OSError:
        pass


def rollover_notice() -> Optional[str]:
    roll = load_entities().get("set_rollover")
    if not roll or roll.get("acknowledged"):
        return None
    return ("*** SET ROLLOVER: %s -> %s (set %s -> %s, detected %s). "
            "The meta reset: re-check vault/Meta/Current Patch.md, and "
            "recalibrate regions.json if the client re-rendered. ***"
            % (roll.get("from"), roll.get("to"), roll.get("from_set"),
               roll.get("to_set"), roll.get("detected")))


def is_stale() -> Tuple[bool, str]:
    """(stale?, human reason).

    Cheap: it only probes the small content-metadata.json, never the 25.9 MB
    blob. A set rollover can only be *confirmed* by an actual refresh, so the
    rollover flag recorded by the last fetch_entities() is replayed here and
    reported loudly ahead of anything else.
    """
    data = load_entities()
    notice = rollover_notice()
    if notice:
        return (True, notice)
    if data.get("degraded") or not data.get("champions"):
        return (True, "no usable entity cache (%s) — run: python3 -m tftcoach.entities --refresh"
                % data.get("degraded_reason", "empty"))

    live = fetch_version()
    cached = data.get("cdragon_version") or ""
    if live is None:
        return (False, "offline: cannot check (cached CommunityDragon %s, set %s)"
                % (cached or "unknown", data.get("set_number")))
    if live != cached:
        return (True, "CommunityDragon moved %s -> %s; refresh to pick up patch "
                      "changes (and any new set)" % (cached or "unknown", live))
    return (False, "up to date (CommunityDragon %s, set %s)"
            % (live, data.get("set_number")))


def is_available() -> Tuple[bool, str]:
    """Can this module validate names right now? Deliberately does NOT trigger
    the big download — the app calls it to render status, not to block."""
    cached = _CACHE if _CACHE is not None else _read_cache()
    if not cached or cached.get("degraded") or not cached.get("champions"):
        return (False, "no entity whitelist cached — run: python3 -m tftcoach.entities --refresh")
    return (True, "set %s (%s): %d champions, %d traits, %d items, %d augments"
            % (cached.get("set_number"), cached.get("set_name"),
               len(cached.get("champions", [])), len(cached.get("traits", [])),
               len(cached.get("items", [])), len(cached.get("augments", []))))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    force = "--refresh" in argv or "--force" in argv
    data = fetch_entities(force=True) if force else load_entities()

    if data.get("degraded"):
        print("DEGRADED: %s" % data.get("degraded_reason"))
    print("set:      %s (%s)  prefix %s"
          % (data.get("set_number"), data.get("set_name"), data.get("set_prefix")))
    print("cdragon:  %s   fetched %s"
          % (data.get("cdragon_version") or "?", data.get("fetched") or "never"))
    champs = data.get("champions", [])
    playable = [c for c in champs if c.get("playable")]
    print("counts:   champions %d (%d playable), traits %d, items %d, augments %d"
          % (len(champs), len(playable), len(data.get("traits", [])),
             len(data.get("items", [])), len(data.get("augments", []))))
    by_cost: Dict[Any, int] = {}
    for c in playable:
        by_cost[c.get("cost")] = by_cost.get(c.get("cost"), 0) + 1
    print("by cost:  %s" % ", ".join("%sg:%d" % (k, by_cost[k]) for k in sorted(
        by_cost, key=lambda x: (x is None, x))))

    stale, reason = is_stale()
    print("stale:    %s — %s" % (stale, reason))
    ok, why = is_available()
    print("available:%s — %s" % (ok, why))

    for arg in argv:
        if arg.startswith("--match="):
            print("match:    %r -> %s" % (arg[8:], match_name(arg[8:], "champion")))
        if arg.startswith("--shop="):
            print("shop:     %r -> %s" % (arg[7:], match_shop_line(arg[7:])))
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
