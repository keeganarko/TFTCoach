"""Live meta feed — replaces v1's hardcoded tier list for good.

Pulls current-patch comp statistics from MetaTFT's public API and renders
vault/Meta/Current Patch.md. Nothing about the meta is ever written into code
or prompts: the coach reads the vault file, and this module keeps it true.

Run manually:   python3 -m tftcoach.meta_feed
Or before a game via run_coach.py's startup check (it refreshes when stale).
"""

from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config
except ImportError:  # allow direct execution
    import config  # type: ignore

COMPS_URL = "https://api-hc.metatft.com/tft-comps-api/comps_data?queue=1100"
PATCH_URL = "https://api-hc.metatft.com/tft-stat-api/patch"
UNITS_URL = "https://api-hc.metatft.com/tft-stat-api/units"
ITEMS_URL = "https://api-hc.metatft.com/tft-stat-api/items"
AUGMENTS_URL = "https://api-hc.metatft.com/tft-stat-api/augments_tiers"

# A unit/item needs this many games before its average means anything.
MIN_STAT_GAMES = 20000
UA = "Mozilla/5.0 (TFTCoach personal coaching tool)"

# A comp needs this many recorded games before we trust its average placement.
MIN_GAMES = 300
# How many comps to render into the vault note.
TOP_N = 18


def _get(url: str, timeout: int = 30) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# -- name cleanup -----------------------------------------------------------
_SET_PREFIX = re.compile(r"^TFT\d*_+")
_ITEM_PREFIX = re.compile(r"^TFT\d*_?Item_+")
_AUG_PREFIX = re.compile(r"^TFT\d*_?Augment_+")
_TRAIT_SUFFIX = re.compile(r"_\d+$")


def clean_name(raw: str) -> str:
    """TFT17_Jax -> Jax, TFT_Item_Bloodthirster -> Bloodthirster,
    TFT17_Stargazer_Wolf_1 -> Stargazer Wolf."""
    if not raw:
        return ""
    s = raw.strip()
    s = _AUG_PREFIX.sub("", s)
    s = _ITEM_PREFIX.sub("", s)
    s = _SET_PREFIX.sub("", s)
    s = _TRAIT_SUFFIX.sub("", s)
    s = s.replace("_", " ").strip()
    # split CamelCase into words, but keep known runs together
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    return s


def _clean_list(raw: str, limit: int = 12) -> List[str]:
    if not raw:
        return []
    out = [clean_name(p) for p in raw.split(",")]
    return [p for p in out if p][:limit]


def fetch_patch() -> Dict[str, Any]:
    data = _get(PATCH_URL, timeout=15) or {}
    return {"patch": data.get("patch"), "sample_size": data.get("count"),
            "since": data.get("start")}


def fetch_comps() -> Optional[Dict[str, Any]]:
    """Returns {'set': 'TFTSet17', 'updated': ts, 'comps': [...]} sorted best-first."""
    raw = _get(COMPS_URL, timeout=45)
    if not isinstance(raw, dict):
        return None
    try:
        details = raw["results"]["data"]["cluster_details"]
    except (KeyError, TypeError):
        return None

    comps: List[Dict[str, Any]] = []
    for _cid, c in details.items():
        if not isinstance(c, dict):
            continue
        overall = c.get("overall") or {}
        count = overall.get("count") or 0
        avg = overall.get("avg")
        if not count or avg is None or count < MIN_GAMES:
            continue
        items = []
        for it in (c.get("top_itemNames") or [])[:4]:
            if isinstance(it, dict) and it.get("itemNames"):
                items.append({"item": clean_name(it["itemNames"]),
                              "avg": it.get("avg"),
                              "pick_rate": it.get("pcnt")})
        comps.append({
            "name": " / ".join(_clean_list(c.get("name_string", ""), 3)) or "Unnamed",
            "units": _clean_list(c.get("units_string", "")),
            "traits": _clean_list(c.get("traits_string", "")),
            "carries": [clean_name(u) for u in (c.get("stars") or [])[:3]],
            "avg_placement": round(float(avg), 2),
            "games": int(count),
            "level_plan": c.get("levelling") or "",
            "difficulty": c.get("difficulty"),
            "top_items": items,
        })
    comps.sort(key=lambda x: x["avg_placement"])
    return {"set": raw.get("tft_set"), "updated": raw.get("updated"), "comps": comps}


def assign_tiers(comps: List[Dict[str, Any]]) -> None:
    """Percentile tiers — robust across patches where absolute averages drift."""
    n = len(comps)
    for i, c in enumerate(comps):
        pct = i / float(n) if n else 1.0
        if pct < 0.12:
            c["tier"] = "S"
        elif pct < 0.35:
            c["tier"] = "A"
        elif pct < 0.65:
            c["tier"] = "B"
        else:
            c["tier"] = "C"


def render_markdown(patch: Dict[str, Any], data: Dict[str, Any]) -> str:
    comps = data["comps"]
    assign_tiers(comps)
    today = datetime.date.today().isoformat()
    set_raw = data.get("set") or ""
    set_num = re.sub(r"\D", "", set_raw) or "?"
    patch_str = patch.get("patch") or "unknown"

    lines = [
        "---",
        "type: meta-snapshot",
        "set: {0}".format(set_num),
        'patch: "{0}"'.format(patch_str),
        "fetched: {0}".format(today),
        "source: MetaTFT api-hc.metatft.com (ranked, queue 1100)",
        "sample_size: {0}".format(patch.get("sample_size") or "unknown"),
        "comps_ranked: {0}".format(len(comps)),
        "generated_by: tftcoach.meta_feed",
        "---",
        "",
        "# Current Meta — Set {0}, patch {1}".format(set_num, patch_str),
        "",
        "Auto-generated {0}. Do not hand-edit — rerun `python3 -m tftcoach.meta_feed`."
        .format(today),
        "Ranked by average placement across {0} ranked games; comps with fewer than "
        "{1} recorded games are excluded.".format(
            patch.get("sample_size") or "?", MIN_GAMES),
        "",
    ]

    for tier in ("S", "A", "B"):
        tier_comps = [c for c in comps if c.get("tier") == tier][:TOP_N]
        if not tier_comps:
            continue
        lines.append("## {0} tier".format(tier))
        lines.append("")
        for c in tier_comps:
            lines.append("### {0}  ·  avg {1}  ·  {2} games".format(
                c["name"], c["avg_placement"], c["games"]))
            if c["carries"]:
                lines.append("- **Carries:** {0}".format(", ".join(c["carries"])))
            if c["units"]:
                lines.append("- **Board:** {0}".format(", ".join(c["units"])))
            if c["traits"]:
                lines.append("- **Traits:** {0}".format(", ".join(c["traits"])))
            if c["top_items"]:
                its = ", ".join("{0} ({1})".format(i["item"], i["avg"])
                                for i in c["top_items"] if i.get("item"))
                lines.append("- **Best items:** {0}".format(its))
            if c["level_plan"]:
                lines.append("- **Plan:** {0}".format(c["level_plan"]))
            lines.append("")
        lines.append("")

    lines += [
        "## How to read this",
        "",
        "Average placement is the only ranking signal here: lower is better, 4.5 is",
        "break-even in an 8-player lobby. A comp with a great average and few games is",
        "noise, which is why the sample floor exists. Item averages are the placement",
        "of games where that item was on the carry, not a win rate.",
        "",
    ]
    return "\n".join(lines)


def _avg_placement(places: List[int]) -> Tuple[Optional[float], int]:
    """MetaTFT gives a placement histogram [#1sts, #2nds, ... #8ths]."""
    total = sum(places or [])
    if not total:
        return None, 0
    return sum((i + 1) * c for i, c in enumerate(places)) / float(total), total


def _playable_units() -> Dict[str, int]:
    """apiName -> cost, for real playable champions only.

    The stats feed also contains PVE monsters, enemy clones and summoned
    followers (TFT17_PVE_ElderDragon, TFT17_Enemy_Aatrox, tft17_bardfollower)
    whose averages are meaningless — a 1.34 avg on a boss is not a hot pick.
    """
    try:
        from . import entities as ent_mod
    except ImportError:
        import entities as ent_mod  # type: ignore
    data = ent_mod.load_entities() or {}
    out: Dict[str, int] = {}
    for champ in (data.get("champions") or []):
        if not isinstance(champ, dict):
            continue
        api = champ.get("apiName") or champ.get("api_name")
        cost = champ.get("cost")
        if api and isinstance(cost, int) and 1 <= cost <= 5:
            out[api.lower()] = cost
    return out


def fetch_unit_stats() -> List[Dict[str, Any]]:
    raw = _get(UNITS_URL, timeout=25) or {}
    playable = _playable_units()
    rows: List[Dict[str, Any]] = []
    for entry in (raw.get("results") or []):
        api = str(entry.get("unit", ""))
        cost = playable.get(api.lower())
        if cost is None:            # PVE / summon / enemy clone -> drop
            continue
        avg, games = _avg_placement(entry.get("places") or [])
        if avg is None or games < MIN_STAT_GAMES:
            continue
        rows.append({"name": clean_name(api), "cost": cost,
                     "avg": round(avg, 3), "games": games})
    rows.sort(key=lambda r: r["avg"])
    return rows


def fetch_item_stats() -> List[Dict[str, Any]]:
    raw = _get(ITEMS_URL, timeout=25) or {}
    rows: List[Dict[str, Any]] = []
    for entry in (raw.get("results") or []):
        avg, games = _avg_placement(entry.get("places") or [])
        if avg is None or games < MIN_STAT_GAMES:
            continue
        rows.append({"name": clean_name(str(entry.get("itemName", ""))),
                     "avg": round(avg, 3), "games": games})
    rows.sort(key=lambda r: r["avg"])
    return rows


def fetch_augment_tiers() -> Dict[str, List[str]]:
    """Curated S/A/B/C/D tiers. Riot bans DISPLAYING augment win rates in tools
    shown during gameplay; a curated tier list is the safer shape, and this is
    a private personal tool either way."""
    raw = _get(AUGMENTS_URL, timeout=25) or {}
    try:
        tiers = raw["content"]["content"]["tierList"]
    except (KeyError, TypeError):
        return {}
    out: Dict[str, List[str]] = {}
    for tier in tiers:
        label = str(tier.get("label") or "?")
        names = [clean_name(str(c.get("id", "")))
                 for c in (tier.get("content") or []) if isinstance(c, dict)]
        out[label] = [n for n in names if n]
    return out


def render_stats_markdown(patch: Dict[str, Any], units: List[Dict[str, Any]],
                          items: List[Dict[str, Any]],
                          augments: Dict[str, List[str]]) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        "type: meta-stats",
        'patch: "{0}"'.format(patch.get("patch") or "unknown"),
        "fetched: {0}".format(today),
        "source: MetaTFT api-hc.metatft.com (ranked)",
        "generated_by: tftcoach.meta_feed",
        "---",
        "",
        "# Unit, item and augment performance — patch {0}".format(
            patch.get("patch") or "?"),
        "",
        "Average placement, lower is better; 4.5 is break-even in an 8-player lobby.",
        "PVE/summon entries are filtered out. Minimum {0:,} games per row."
        .format(MIN_STAT_GAMES),
        "",
    ]

    if units:
        lines += ["## Units by average placement", ""]
        by_cost: Dict[int, List[Dict[str, Any]]] = {}
        for row in units:
            by_cost.setdefault(row["cost"], []).append(row)
        for cost in sorted(by_cost):
            entries = by_cost[cost]
            lines.append("**{0}-cost:** ".format(cost) + ", ".join(
                "{0} {1}".format(r["name"], r["avg"]) for r in entries))
            lines.append("")
        lines.append("")

    if items:
        lines += ["## Items by average placement (top 40)", ""]
        for row in items[:40]:
            lines.append("- {0} — {1} ({2:,} games)".format(
                row["name"], row["avg"], row["games"]))
        lines.append("")
        worst = [r for r in items if r["games"] > MIN_STAT_GAMES * 3][-8:]
        if worst:
            lines += ["**Worst performers (avoid unless the comp demands it):** "
                      + ", ".join("{0} {1}".format(r["name"], r["avg"])
                                  for r in worst), ""]

    for label in ("S", "A"):
        names = augments.get(label) or []
        if names:
            lines += ["## {0}-tier augments".format(label), "",
                      ", ".join(sorted(names)), ""]
    if augments.get("D"):
        lines += ["**D-tier (avoid):** " + ", ".join(sorted(augments["D"])), ""]

    return "\n".join(lines)


def refresh_stats(verbose: bool = True) -> Tuple[bool, str]:
    """Write vault/Meta/Unit Item Augment Stats.md."""
    patch = fetch_patch()
    units = fetch_unit_stats()
    items = fetch_item_stats()
    augments = fetch_augment_tiers()
    if not units and not items and not augments:
        return False, "no stat endpoints reachable — skipped stats refresh"
    md = render_stats_markdown(patch, units, items, augments)
    out_dir = os.path.join(config.VAULT_DIR, "Meta")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Unit Item Augment Stats.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md)
    msg = ("Wrote {0} units, {1} items, {2} augment tiers to {3}"
           .format(len(units), len(items), len(augments), path))
    if verbose:
        print(msg)
    return True, msg


def refresh(verbose: bool = True) -> Tuple[bool, str]:
    """Fetch and write vault/Meta/Current Patch.md. Returns (ok, message)."""
    patch = fetch_patch()
    data = fetch_comps()
    if not data or not data.get("comps"):
        return False, ("Could not reach the MetaTFT API — keeping the existing "
                       "snapshot. Check your connection, or paste a tier list "
                       "manually into vault/Meta/Current Patch.md.")
    md = render_markdown(patch, data)
    out_dir = os.path.join(config.VAULT_DIR, "Meta")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Current Patch.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md)
    msg = "Wrote {0} comps for patch {1} to {2}".format(
        len(data["comps"]), patch.get("patch"), path)
    if verbose:
        print(msg)
    return True, msg


def snapshot_age_days() -> Optional[int]:
    """How stale is the vault snapshot? None if missing/unparseable."""
    path = os.path.join(config.VAULT_DIR, "Meta", "Current Patch.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            head = fh.read(600)
    except OSError:
        return None
    m = re.search(r"^fetched:\s*(\d{4}-\d{2}-\d{2})", head, re.M)
    if not m:
        return None
    try:
        d = datetime.date.fromisoformat(m.group(1))
    except ValueError:
        return None
    return (datetime.date.today() - d).days


def is_available() -> Tuple[bool, str]:
    p = fetch_patch()
    if p.get("patch"):
        return True, "MetaTFT reachable (patch {0})".format(p["patch"])
    return False, "MetaTFT API unreachable — meta snapshot will not auto-refresh"


if __name__ == "__main__":
    ok, message = refresh()
    print(("OK: " if ok else "FAILED: ") + message)
    ok2, message2 = refresh_stats()
    print(("OK: " if ok2 else "SKIPPED: ") + message2)
    age = snapshot_age_days()
    if age is not None:
        print("Snapshot age: {0} day(s)".format(age))
