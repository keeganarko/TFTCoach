"""Regenerates vault/Profile/Player Profile.md from real ranked match history.

Uses DAK.GG's public JSON (no Riot API key needed, verified 2026-08-11). This
turns "I think I over-save" into "games ending with 30+ gold average 5.42" —
the difference between a hunch and something the coach can trigger on.

Undocumented third-party endpoint: cache hard, poll gently, expect breakage.
The Riot API path stays the documented fallback (see vault/Reference/).

    python3 -m tftcoach.player_profile --player keegancho#NA1 --games 200
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import statistics
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config
    from .meta_feed import clean_name
except ImportError:
    import config                     # type: ignore
    from meta_feed import clean_name  # type: ignore

BASE = "https://tft.dakgg.io/api/v1"
UA = "Mozilla/5.0 (TFTCoach personal coaching tool)"
RANKED_QUEUE = 1100
PAGE_SLEEP_SEC = 0.7      # be a polite guest on someone else's API


def _get(url: str, timeout: int = 25) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def current_season() -> str:
    data = _get(BASE + "/data/seasons") or {}
    return str(data.get("currentSeason") or "set17")


def stage_of(last_round: Optional[int]) -> str:
    """Cumulative round index -> 'stage-round'. Stage 1 is 4 rounds, then 7."""
    if not isinstance(last_round, int) or last_round < 1:
        return "?"
    if last_round <= 4:
        return "1-%d" % last_round
    return "%d-%d" % (2 + (last_round - 5) // 7, (last_round - 5) % 7 + 1)


def fetch_matches(player: str, season: str, want: int) -> Tuple[List[Dict[str, Any]], str]:
    """Returns (my participant rows, resolved slug). One row per game."""
    if "#" in player:
        name, tag = player.split("#", 1)
    else:
        name, tag = player, "NA1"
    slug = urllib.parse.quote("%s-%s" % (name, tag))
    rows: List[Dict[str, Any]] = []
    page = 1
    while len(rows) < want and page <= 40:
        url = "%s/summoners/na1/%s/matches?season=%s&page=%d" % (BASE, slug, season, page)
        data = _get(url, timeout=35)
        matches = (data or {}).get("matches") or []
        if not matches:
            break
        # summoners[] is a TOP-LEVEL sibling of matches[], not per-match:
        # it maps puuid -> gameName/tagLine across the whole page.
        directory = {s.get("puuid"): s for s in ((data or {}).get("summoners") or [])
                     if isinstance(s, dict)}
        for match in matches:
            row = _extract(match, name, tag, directory)
            if row:
                rows.append(row)
        page += 1
        time.sleep(PAGE_SLEEP_SEC)
    return rows[:want], slug


def _extract(match: Dict[str, Any], name: str, tag: str,
             directory: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pull MY participant out of a match.

    Note the mixed casing in this API: participant fields are camelCase
    (goldLeft, lastRound) but nested unit/trait fields are snake_case
    (character_id, tier_current). Getting this wrong silently yields zero rows.
    """
    if str(match.get("queueId")) != str(RANKED_QUEUE):
        return None
    mine = None
    for puuid, summoner in directory.items():
        if (str(summoner.get("gameName", "")).lower() == name.lower()
                and str(summoner.get("tagLine", "")).lower() == tag.lower()):
            mine = puuid
            break
    if not mine:
        return None
    me = None
    for participant in (match.get("participants") or []):
        if participant.get("puuid") == mine:
            me = participant
            break
    if me is None:
        return None

    units = me.get("units") or []
    three_item = sum(1 for u in units if len(u.get("items") or []) >= 3)
    carry = None
    best = -1
    for unit in units:
        score = len(unit.get("items") or []) * 10 + (unit.get("tier") or 0)
        if score > best:
            best, carry = score, unit
    traits = [t for t in (me.get("traits") or [])
              if isinstance(t, dict) and (t.get("tier_current") or 0) > 0]
    traits.sort(key=lambda t: t.get("tier_current") or 0, reverse=True)

    return {
        "placement": me.get("placement"),
        "gold_left": me.get("goldLeft"),
        "level": me.get("level"),
        "last_round": me.get("lastRound"),
        "patch": match.get("patchVersion") or match.get("gameVersion"),
        "board_size": len(units),
        "three_item_units": three_item,
        "carry": clean_name(str((carry or {}).get("character_id") or "")) or None,
        "top_trait": clean_name(str(traits[0].get("name", ""))) if traits else None,
        "items": [clean_name(str(i)) for u in units for i in (u.get("items") or [])],
    }


# ── aggregation ──────────────────────────────────────────────────────────────
def _avg(values: List[float]) -> Optional[float]:
    vals = [v for v in values if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals), 3) if vals else None


def _bucket(rows: List[Dict[str, Any]], key: str,
            edges: List[Tuple[str, Any, Any]]) -> List[Tuple[str, int, Optional[float]]]:
    out = []
    for label, low, high in edges:
        sel = [r for r in rows
               if isinstance(r.get(key), (int, float))
               and (low is None or r[key] >= low)
               and (high is None or r[key] <= high)]
        out.append((label, len(sel), _avg([r["placement"] for r in sel])))
    return out


def _group(rows: List[Dict[str, Any]], key: str, min_n: int
           ) -> List[Tuple[str, int, Optional[float]]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        val = row.get(key)
        if val:
            groups.setdefault(str(val), []).append(row)
    out = [(k, len(v), _avg([r["placement"] for r in v]))
           for k, v in groups.items() if len(v) >= min_n]
    out.sort(key=lambda t: (t[2] if t[2] is not None else 9))
    return out


def render(player: str, season: str, rows: List[Dict[str, Any]]) -> str:
    n = len(rows)
    places = [r["placement"] for r in rows if isinstance(r.get("placement"), int)]
    today = datetime.date.today().isoformat()
    avg = _avg(places)
    top4 = round(100.0 * sum(1 for p in places if p <= 4) / len(places), 1) if places else 0
    firsts = round(100.0 * sum(1 for p in places if p == 1) / len(places), 1) if places else 0

    lines = [
        "---", "type: player-profile", "player: {0}".format(player),
        "season: {0}".format(season),
        "sample: {0} ranked games".format(n),
        "source: tft.dakgg.io (no API key)",
        "generated: {0}".format(today),
        "generated_by: tftcoach.player_profile",
        "---", "",
        "# Player Profile — {0}".format(player), "",
        "Counted outcomes over {0} ranked games. Regenerate: "
        "`python3 -m tftcoach.player_profile`.".format(n), "",
        "| Metric | Value |", "|---|---|",
        "| Average placement | **{0}** |".format(avg),
        "| 1st rate | {0}% |".format(firsts),
        "| Top-4 rate | {0}% |".format(top4),
        "| Mean gold left | {0} |".format(_avg([r.get("gold_left") for r in rows])),
        "| Mean end level | {0} |".format(_avg([r.get("level") for r in rows])),
        "",
    ]

    def table(title: str, note: str,
              data: List[Tuple[str, int, Optional[float]]]) -> None:
        if not any(d[1] for d in data):
            return
        lines.extend(["## " + title, "", note, "",
                      "| Bucket | n | Avg place |", "|---|---|---|"])
        for label, count, average in data:
            if count:
                lines.append("| {0} | {1} | {2} |".format(label, count, average))
        lines.append("")

    table("Gold left at death",
          "Unspent gold is banked value you never converted into board strength.",
          _bucket(rows, "gold_left", [("0-4", 0, 4), ("5-9", 5, 9), ("10-19", 10, 19),
                                      ("20-29", 20, 29), ("30+", 30, None)]))
    table("Final level",
          "Levelling is the strongest lever on placement in most players' data.",
          _bucket(rows, "level", [("<=7", 0, 7), ("8", 8, 8), ("9", 9, 9),
                                  ("10", 10, 10), ("11", 11, None)]))
    table("Units holding 3 items",
          "Completed items beat spread-thin items; this is usually a bigger "
          "lever than star levels.",
          _bucket(rows, "three_item_units", [("0-1", 0, 1), ("2", 2, 2),
                                             ("3", 3, 3), ("4+", 4, None)]))
    table("Board size",
          "Board size proxies both levelling and gold conversion.",
          _bucket(rows, "board_size", [("<=8", 0, 8), ("9", 9, 9), ("10", 10, 10),
                                       ("11+", 11, None)]))
    table("Elimination stage",
          "Placement value per round is wildly non-linear — surviving one more "
          "stage is often worth several placements.",
          [(stage_of(lo) + "–" + stage_of(hi), len([r for r in rows
             if isinstance(r.get("last_round"), int) and lo <= r["last_round"] <= hi]),
            _avg([r["placement"] for r in rows
                  if isinstance(r.get("last_round"), int) and lo <= r["last_round"] <= hi]))
           for lo, hi in ((19, 25), (26, 32), (33, 39), (40, 60))])

    carries = _group(rows, "carry", 4)
    if carries:
        lines += ["## Carries (min 4 games)", "", "| Carry | n | Avg place |",
                  "|---|---|---|"]
        for name, count, average in carries:
            lines.append("| {0} | {1} | {2} |".format(name, count, average))
        lines.append("")

    traits = _group(rows, "top_trait", 4)
    if traits:
        lines += ["## Strongest active trait (min 4 games)", "",
                  "| Trait | n | Avg place |", "|---|---|---|"]
        for name, count, average in traits:
            lines.append("| {0} | {1} | {2} |".format(name, count, average))
        lines.append("")

    if avg is not None:
        best = [c for c in carries[:3]]
        worst = [c for c in carries[-3:] if c[2] and c[2] > avg]
        lines += ["## Read this as coaching triggers", ""]
        if best:
            lines.append("- Lean toward: " + ", ".join(
                "{0} ({1})".format(c[0], c[2]) for c in best))
        if worst:
            lines.append("- Avoid itemising: " + ", ".join(
                "{0} ({1})".format(c[0], c[2]) for c in worst))
        lines.append("- Baseline to beat: {0}. Anything above it is a losing "
                     "pattern for me specifically.".format(avg))
        lines.append("")
    return "\n".join(lines)


def refresh(player: str = "keegancho#NA1", games: int = 200,
            verbose: bool = True) -> Tuple[bool, str]:
    season = current_season()
    if verbose:
        print("Fetching up to {0} ranked games for {1} ({2}) ..."
              .format(games, player, season))
    rows, _slug = fetch_matches(player, season, games)
    if not rows:
        return False, ("no matches returned — the DAK.GG endpoint may have "
                       "changed, or the Riot ID/region is wrong. The existing "
                       "profile note was left untouched.")
    out_dir = os.path.join(config.VAULT_DIR, "Profile")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Player Profile.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(player, season, rows))
    msg = "Wrote profile from {0} ranked games to {1}".format(len(rows), path)
    if verbose:
        print(msg)
    return True, msg


def is_available() -> Tuple[bool, str]:
    data = _get(BASE + "/data/seasons", timeout=12)
    if data:
        return True, "DAK.GG reachable (season {0})".format(
            data.get("currentSeason"))
    return False, "DAK.GG unreachable — profile will not refresh"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python3 -m tftcoach.player_profile")
    parser.add_argument("--player", default="keegancho#NA1")
    parser.add_argument("--games", type=int, default=200)
    args = parser.parse_args()
    ok, message = refresh(args.player, args.games)
    print(("OK: " if ok else "FAILED: ") + message)
