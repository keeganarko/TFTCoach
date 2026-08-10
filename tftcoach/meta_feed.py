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
    age = snapshot_age_days()
    if age is not None:
        print("Snapshot age: {0} day(s)".format(age))
