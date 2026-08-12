"""Pool and contest tracking — counting what better players count in their heads.

The shared pool is the invisible resource that separates Master from Diamond:
if the copies you need are on other boards or already burned through your shops,
"keep rolling" is the wrong advice no matter what the comp tier list says.

Three evidence streams, in order of hardness:
  1. OWNED   — my board+bench copies. Exact.
  2. SCOUTED — copies seen on opponents' boards (when a scout capture happens).
     Exact at the moment of scouting, decays as they sell/upgrade.
  3. SHOPS   — every shop seen. A unit that keeps NOT appearing when the odds
     say it should is being held by someone; a statistical contest signal.

The output is honest about which stream each number comes from. No stream is
memory-read; everything derives from what the extractor legitimately saw.
Python 3.9, stdlib only, imports clean with nothing installed.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config
    from .state import GameState
except ImportError:                      # direct execution
    import config                        # type: ignore
    from state import GameState          # type: ignore

# Set 17 pool constants (mirrors vault/Reference/Game Math.md; regenerate on a
# set change). copies = per champion; champs = distinct champions in the tier.
POOL = {1: {"copies": 29, "champs": 14},
        2: {"copies": 22, "champs": 13},
        3: {"copies": 18, "champs": 13},
        4: {"copies": 10, "champs": 14},
        5: {"copies": 9,  "champs": 8}}

# Shop odds per slot by level (Set 17; % chance the slot is each cost tier).
SHOP_ODDS = {
    1: (100, 0, 0, 0, 0), 2: (100, 0, 0, 0, 0), 3: (75, 25, 0, 0, 0),
    4: (55, 30, 15, 0, 0), 5: (45, 33, 20, 2, 0), 6: (30, 40, 25, 5, 0),
    7: (19, 30, 40, 10, 1), 8: (15, 20, 32, 30, 3), 9: (10, 17, 25, 33, 15),
    10: (5, 10, 20, 40, 25), 11: (1, 2, 12, 50, 35),
}

# A contest flag needs this much statistical separation before we say it.
CONTEST_Z = 1.6          # ~90% one-sided
MIN_EXPECTED_SIGHTINGS = 2.5   # below this, silence — not enough shops seen


def _star_copies(star: Optional[int]) -> int:
    """Copies consumed by a unit at a star level: 1★=1, 2★=3, 3★=9."""
    return {1: 1, 2: 3, 3: 9}.get(star or 1, 1)


class PoolTracker:
    """Per-game accumulator. Feed it every tick; ask it before rolldowns."""

    def __init__(self, entities: Any = None):
        self.costs: Dict[str, int] = {}
        if entities:
            for champ in (entities.get("champions") or []):
                if isinstance(champ, dict) and champ.get("name"):
                    cost = champ.get("cost")
                    if isinstance(cost, int) and 1 <= cost <= 5:
                        self.costs[str(champ["name"]).lower()] = cost
        # sightings[name] = number of shop slots that showed this champ
        self.shop_sightings: Dict[str, int] = {}
        # shops_at_level[level] = number of SHOPS (5 slots each) seen there
        self.shops_at_level: Dict[int, int] = {}
        self._last_shop: Optional[Tuple[str, ...]] = None
        # champ -> copies I hold (refreshed every tick from board+bench)
        self.owned: Dict[str, int] = {}
        # champ -> max copies ever seen on scouted enemy boards
        self.scouted: Dict[str, int] = {}

    # ── feeding ──────────────────────────────────────────────────────────
    def observe(self, state: GameState) -> None:
        """Call once per tick with the extracted state."""
        level = state.level.value if state.level.known else None
        shop = state.shop.value if state.shop.known else None
        if isinstance(shop, list) and shop:
            key = tuple(str(s).lower() for s in shop)
            if key != self._last_shop:      # same shop re-read is not new evidence
                self._last_shop = key
                if isinstance(level, int) and level in SHOP_ODDS:
                    self.shops_at_level[level] = self.shops_at_level.get(level, 0) + 1
                    for name in key:
                        if name in self.costs:
                            self.shop_sightings[name] = \
                                self.shop_sightings.get(name, 0) + 1

        held: Dict[str, int] = {}
        for field in (state.board, state.bench):
            if not field.known or not isinstance(field.value, list):
                continue
            for unit in field.value:
                name = getattr(unit, "name", None) or (
                    unit.get("name") if isinstance(unit, dict) else None)
                star = getattr(unit, "star", None) or (
                    unit.get("star") if isinstance(unit, dict) else None)
                if name:
                    key = str(name).lower()
                    held[key] = held.get(key, 0) + _star_copies(
                        star if isinstance(star, int) else 1)
        if held:
            self.owned = held

    def observe_scout(self, units: List[Dict[str, Any]]) -> None:
        """Feed a scouted enemy board (from a scout capture)."""
        counts: Dict[str, int] = {}
        for unit in units or []:
            name = str(unit.get("name", "")).lower()
            if name:
                counts[name] = counts.get(name, 0) + _star_copies(
                    unit.get("star") if isinstance(unit.get("star"), int) else 1)
        for name, copies in counts.items():
            self.scouted[name] = max(self.scouted.get(name, 0), copies)

    # ── asking ───────────────────────────────────────────────────────────
    def known_gone(self, name: str) -> Tuple[int, List[str]]:
        key = name.lower()
        gone, why = 0, []
        if self.owned.get(key):
            gone += self.owned[key]
            why.append("I hold %d" % self.owned[key])
        if self.scouted.get(key):
            gone += self.scouted[key]
            why.append("scouted %d on enemy boards" % self.scouted[key])
        return gone, why

    def contest_signal(self, name: str) -> Optional[str]:
        """Statistical read from shop frequency. None = not enough evidence.

        Expected sightings of champ c at cost t over the shops I saw:
          sum over levels L of  shops(L) * 5 slots * P(tier t at L) / champs(t)
        assuming a full pool. Seeing far fewer implies depletion. This is a
        one-sided signal: seeing MORE than expected is normal variance.
        """
        key = name.lower()
        cost = self.costs.get(key)
        if cost is None:
            return None
        expected = 0.0
        for level, shops in self.shops_at_level.items():
            tier_p = SHOP_ODDS.get(level, (0,) * 5)[cost - 1] / 100.0
            expected += shops * 5 * tier_p / POOL[cost]["champs"]
        if expected < MIN_EXPECTED_SIGHTINGS:
            return None
        seen = self.shop_sightings.get(key, 0)
        # Poisson approx: z = (seen - expected) / sqrt(expected)
        z = (seen - expected) / math.sqrt(expected)
        if z <= -CONTEST_Z:
            return ("%s: saw %d in shops where a full pool predicts %.1f — "
                    "likely contested/depleted" % (name, seen, expected))
        return None

    def prompt_block(self, watch: Optional[List[str]] = None) -> str:
        """Compact block for the coaching prompt. Empty string when silent."""
        lines: List[str] = []
        names = set(watch or [])
        names.update(self.owned)
        names.update(self.scouted)
        flagged: List[str] = []
        for name in sorted(names):
            signal = self.contest_signal(name)
            if signal:
                flagged.append(signal)
        for name in sorted(self.scouted):
            gone, why = self.known_gone(name)
            cost = self.costs.get(name)
            if cost and gone >= POOL[cost]["copies"] * 0.3:
                flagged.append("%s: %d of %d copies accounted for (%s)"
                               % (name, gone, POOL[cost]["copies"], "; ".join(why)))
        if flagged:
            lines.append("POOL/CONTEST (counted from shops seen and scouts — "
                         "hard evidence, factor into roll advice):")
            lines.extend("- " + f for f in flagged[:6])
        total_shops = sum(self.shops_at_level.values())
        if total_shops >= 8 and not flagged:
            lines.append("POOL: %d shops observed, no contest signals yet."
                         % total_shops)
        return "\n".join(lines)

    # ── persistence (timeline sidecar) ───────────────────────────────────
    def save(self, path: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"shop_sightings": self.shop_sightings,
                           "shops_at_level": {str(k): v for k, v in
                                              self.shops_at_level.items()},
                           "owned": self.owned, "scouted": self.scouted},
                          fh)
        except OSError:
            pass


if __name__ == "__main__":
    # Self-test with synthetic evidence: at level 8, after 20 shops, a 4-cost
    # we never see once should flag; one appearing at the expected rate should not.
    try:
        from tftcoach import entities as ent
    except ImportError:
        import entities as ent  # type: ignore
    tracker = PoolTracker(ent.load_entities())
    from tftcoach.state import GameState, Field

    shops = [["Kindred", "Rhaast", "Briar", "Akali", "Belveth"],
             ["Morgana", "Nami", "Karma", "Akali", "Maokai"],
             ["Riven", "Corki", "Akali", "Gnar", "Gwen"],
             ["Nami", "Kindred", "Zoe", "Jax", "Milio"]] * 5
    for i, shop in enumerate(shops):
        s = GameState()
        s.level = Field(8, 0.95)
        s.shop = Field(shop + [str(i)], 0.9)   # suffix makes each shop distinct
        tracker.observe(s)
    print("shops seen:", sum(tracker.shops_at_level.values()))
    for probe in ("Xayah", "Kindred", "Akali"):
        print(" ", probe, "->", tracker.contest_signal(probe) or "no signal")
    tracker.observe_scout([{"name": "Xayah", "star": 2}, {"name": "Shen", "star": 2}])
    print(tracker.prompt_block(watch=["Xayah", "Kindred"]))
