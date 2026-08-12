"""High-elo playbook — what Master+/Challenger players actually do differently.

The default meta snapshot averages every ranked player, so it encodes the
average player's habits. This module pulls the same analysis stratified by rank
and keeps the parts that describe DECISIONS rather than outcomes:

  * level_stage      — the stage at which they hit each level, per comp
  * win_conditions   — quantified: "having Gargoyle Stoneplate is worth +2.43
                       placements in this comp"
  * carousel_priority— which components they take first
  * units_positions  — where they actually place each unit on the hex grid

That last one is the only source of real positioning data available without
computer vision, and positioning is the biggest hole in this coach.

    python3 -m tftcoach.highelo
"""

from __future__ import annotations

import datetime
import json
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config
    from .meta_feed import clean_name
except ImportError:
    import config                      # type: ignore
    from meta_feed import clean_name   # type: ignore

BASE = ("https://data.v2.iesdev.com/api/v1/query_objects/prod/tft/"
        "analyzed_comps?region=WORLD&mode=RANKED&portal=ALL&rank=")
UA = "Mozilla/5.0 (TFTCoach personal coaching tool)"

TOP_COMPS = 12          # how many high-elo comps to write out
MIN_GAMES = 25          # Challenger is a small population; keep this low
COMPARE_RANK = "PLATINUM%2B"    # the player's own bracket, for the delta
TARGET_RANKS = ("CHALLENGER", "MASTER%2B")


def _get(url: str, timeout: int = 60) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def fetch(rank: str) -> List[Dict[str, Any]]:
    data = _get(BASE + rank)
    return (data or {}).get("data") or []


def _comp_label(comp: Dict[str, Any]) -> str:
    """'TFT17_DRX TFT17_Akali' -> 'DRX Akali'."""
    return " ".join(clean_name(p) for p in str(comp.get("name", "")).split()) or "?"


def _levels(comp: Dict[str, Any]) -> str:
    plan = ((comp.get("strategy") or {}).get("level_stage")) or {}
    if not plan:
        return ""
    parts = []
    for lvl in sorted(plan, key=lambda k: int(k) if str(k).isdigit() else 99):
        stage = plan[lvl]
        if stage:
            parts.append("L{0}@{1}".format(lvl, str(stage).replace(".", "-")))
    return ", ".join(parts)


def _conditions(comp: Dict[str, Any], limit: int = 4) -> List[str]:
    out = []
    for cond in (comp.get("win_conditions") or [])[:limit]:
        if not isinstance(cond, dict):
            continue
        gain = cond.get("avg_placement_improvement")
        name = clean_name(str(cond.get("name", "")))
        if not name or gain is None:
            continue
        out.append("{0} (+{1:.2f} places)".format(name, gain))
    return out


def _positions(comp: Dict[str, Any]) -> List[str]:
    """board_position is a 0..27 hex index: row = idx // 7, col = idx % 7.

    Orientation verified empirically against 20 Challenger comps rather than
    assumed: row 0 holds 34 tanks to 2 carries, row 3 holds 16 carries to 1
    tank. So row 0 is the FRONT line (facing the enemy) and row 3 is the back.
    Getting this backwards would invert every positioning call the coach makes.
    """
    out = []
    seen = set()
    for entry in (comp.get("units_positions") or []):
        if not isinstance(entry, dict):
            continue
        idx = entry.get("board_position")
        unit = clean_name(str(entry.get("unit_api_name", "")))
        if not unit or not isinstance(idx, int) or not 0 <= idx <= 27:
            continue
        # The aggregation upstream sometimes lists one unit at two hexes
        # (Samira r4c1 AND r4c7) — a single copy cannot be in two places, and
        # contradictory hexes would poison positioning advice. First entry is
        # the modal placement; keep it, drop the rest.
        if unit in seen:
            continue
        seen.add(unit)
        out.append("{0} r{1}c{2}".format(unit, idx // 7 + 1, idx % 7 + 1))
    return out


def render(by_rank: Dict[str, List[Dict[str, Any]]],
           mine: List[Dict[str, Any]]) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---", "type: reference", "scope: patch-bound",
        "fetched: {0}".format(today),
        "source: Blitz analyzed_comps, rank-stratified",
        "generated_by: tftcoach.highelo",
        "---", "",
        "# High-elo playbook — what Master+/Challenger do differently", "",
        "The main meta snapshot averages every ranked player. This is the same "
        "analysis restricted to the top of the ladder. Where the two disagree, "
        "this file describes the better decision.", "",
        "Caveats: win conditions and level timings are pooled by the provider, "
        "not fully rank-stratified — only avg placement is per-bracket. Item/"
        "trait deltas are correlational (hitting an emblem is partly an effect "
        "of already winning): treat them as priority hints, never roll targets.",
        "",
    ]

    # The delta is the actual lesson: which comps survive contact with good players.
    mine_names = {_comp_label(c) for c in mine}
    for rank, comps in by_rank.items():
        good = [c for c in comps
                if ((c.get("stats") or {}).get("nb_games") or 0) >= MIN_GAMES]
        good.sort(key=lambda c: (c.get("stats") or {}).get("avg_placement") or 9)
        if not good:
            continue
        label = rank.replace("%2B", "+")
        lines += ["## {0} — top {1} comps".format(label, min(TOP_COMPS, len(good))), ""]
        for comp in good[:TOP_COMPS]:
            stats = comp.get("stats") or {}
            lines.append("### {0} — avg {1:.2f} ({2} games)".format(
                _comp_label(comp), stats.get("avg_placement") or 0,
                stats.get("nb_games") or 0))
            levels = _levels(comp)
            if levels:
                lines.append("- **Level timings:** {0}".format(levels))
            conds = _conditions(comp)
            if conds:
                lines.append("- **Win conditions:** {0}".format("; ".join(conds)))
            carousel = [clean_name(str(i)) for i in
                        (comp.get("carousel_priority") or [])[:3]]
            if carousel:
                lines.append("- **Carousel priority:** {0}".format(", ".join(carousel)))
            carries = [clean_name(str(u)) for u in (comp.get("carry_units") or [])[:3]]
            if carries:
                lines.append("- **Carries:** {0}".format(", ".join(carries)))
            pos = _positions(comp)
            if pos:
                lines.append("- **Board positions** (r1 = FRONT line facing the "
                             "enemy, r4 = my back line; c = column 1-7 left to "
                             "right): {0}".format(", ".join(pos)))
            lines.append("")
        lines.append("")

    # "The top" = anything viable in ANY high bracket. Computing the trap list
    # against Challenger alone flagged comps (e.g. Astronaut Rammus) that were
    # simultaneously listed as Master+ top-12 in the same file — a coach that
    # can justify both forcing and avoiding the same comp is worse than silent.
    top_names = {_comp_label(c)
                 for comps in by_rank.values() for c in comps
                 if ((c.get("stats") or {}).get("nb_games") or 0) >= MIN_GAMES}
    only_low = sorted(mine_names - top_names)[:14]
    only_top = sorted(top_names - mine_names)[:14]
    lines += ["## The delta — my bracket vs the top", ""]
    if only_top:
        lines += ["**Played at the top but not in my bracket** (worth learning): "
                  + ", ".join(only_top), ""]
    if only_low:
        lines += ["**Common in my bracket but absent at the top** (these do not "
                  "survive contact with good players — treat as traps): "
                  + ", ".join(only_low), ""]
    lines += ["A comp appearing only in lower brackets usually means it beats "
              "mistakes rather than beating boards. Prefer lines that hold up "
              "at the top when the choice is close.", ""]
    return "\n".join(lines)


def refresh(verbose: bool = True) -> Tuple[bool, str]:
    by_rank: Dict[str, List[Dict[str, Any]]] = {}
    for rank in TARGET_RANKS:
        if verbose:
            print("Fetching {0} comps ...".format(rank.replace("%2B", "+")))
        comps = fetch(rank)
        if comps:
            by_rank[rank] = comps
    if not by_rank:
        return False, "Blitz unreachable — high-elo playbook not refreshed"
    mine = fetch(COMPARE_RANK)

    out_dir = os.path.join(config.VAULT_DIR, "Reference")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "High Elo Playbook.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(by_rank, mine))
    msg = "Wrote high-elo playbook ({0}) to {1}".format(
        ", ".join("{0}:{1}".format(r.replace("%2B", "+"), len(c))
                  for r, c in by_rank.items()), path)
    if verbose:
        print(msg)
    return True, msg


def is_available() -> Tuple[bool, str]:
    data = _get(BASE + "CHALLENGER", timeout=30)
    n = len((data or {}).get("data") or [])
    if n:
        return True, "Blitz reachable ({0} Challenger comps)".format(n)
    return False, "Blitz unreachable — no high-elo data"


if __name__ == "__main__":
    ok, message = refresh()
    print(("OK: " if ok else "FAILED: ") + message)
