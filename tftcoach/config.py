"""Paths, tunables, and the screen-region config for TFT Coach Option B.

Region coordinates are NEVER hardcoded: they live in regions.json, produced by
`python3 -m tftcoach.calibrate` against a real frame of your client. This is
deliberate — Riot's HUD is not proportional across resolutions, and Set 18's
Unreal migration (Aug 26, 2026) changes rendering, so recalibration must be a
5-minute chore, not a code change.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_DIR = os.path.join(REPO_DIR, "vault")
DATA_DIR = os.path.join(REPO_DIR, ".data")          # gitignored: caches
CAPTURE_DIR = os.path.join(REPO_DIR, ".captures")   # gitignored: frames
GAMES_DIR = os.path.join(DATA_DIR, "games")         # gitignored: timelines
REGIONS_PATH = os.path.join(REPO_DIR, "regions.json")
ENTITIES_PATH = os.path.join(DATA_DIR, "entities.json")

CDRAGON_TFT_URL = "https://raw.communitydragon.org/latest/cdragon/tft/en_us.json"
CDRAGON_VERSION_URL = "https://raw.communitydragon.org/latest/content-metadata.json"

# Regions the calibration tool asks for, in order. (key, human prompt, kind)
# kind drives OCR preprocessing: "number", "text", "image".
REGION_SPECS: List[Tuple[str, str, str]] = [
    ("gold",   "Your GOLD counter (just the number)", "number"),
    ("level",  "Your LEVEL (the number next to your XP bar)", "number"),
    ("stage",  "The STAGE-ROUND indicator at the top (e.g. 3-2)", "text"),
    ("hp",     "YOUR health number in the player list", "number"),
    ("shop",   "The whole SHOP bar (all 5 champion cards)", "text"),
    ("board",  "The BOARD hexes (your side of the field)", "image"),
    ("bench",  "The BENCH row", "image"),
    ("traits", "The TRAIT/synergy list on the left", "text"),
]

# Which fields OCR is reliable at vs. which need a vision model.
# Board/bench/items are 3D models and tiny icons — OCR loses here, so the
# vision model gets those crops instead of the whole screen.
OCR_FIELDS = {"gold", "level", "stage", "hp", "shop", "traits"}
VISION_FIELDS = {"board", "bench"}

# Trigger tuning
POLL_INTERVAL_SEC = 2.0      # cheap stage-region poll to detect a new round
MIN_SECONDS_BETWEEN_CALLS = 20.0
FULLFRAME_FALLBACK = True    # if uncalibrated, fall back to v2 whole-screen vision

DEFAULT_TARGET_RES = (1920, 1080)

# Which display the GAME is on (mss numbering: 1 = primary). Multi-monitor
# desktops set TFTCOACH_MONITOR=2/3 when League lives on a secondary display.
try:
    GAME_MONITOR = int(os.environ.get("TFTCOACH_MONITOR", "1"))
except ValueError:
    GAME_MONITOR = 1


class Regions:
    """Loads/saves regions.json. Rects are pixel [x, y, w, h] plus the
    resolution they were calibrated at."""

    def __init__(self, rects: Optional[Dict[str, List[int]]] = None,
                 resolution: Optional[List[int]] = None):
        self.rects: Dict[str, List[int]] = rects or {}
        self.resolution: List[int] = resolution or list(DEFAULT_TARGET_RES)

    @classmethod
    def load(cls, path: str = REGIONS_PATH) -> "Regions":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return cls(data.get("rects", {}), data.get("resolution"))
        except (OSError, ValueError):
            return cls()

    def save(self, path: str = REGIONS_PATH) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"resolution": self.resolution, "rects": self.rects},
                      fh, indent=2)

    @property
    def calibrated(self) -> bool:
        return bool(self.rects)

    def missing(self) -> List[str]:
        return [k for k, _, _ in REGION_SPECS if k not in self.rects]

    def for_resolution(self, width: int, height: int) -> Dict[str, List[int]]:
        """Scale rects if the live resolution differs from calibration.

        Returns proportionally scaled rects, but callers should warn: Riot's
        HUD is not a strict proportional scale across resolutions, so scaled
        coordinates are a best effort, not a guarantee.
        """
        cw, ch = self.resolution
        if (cw, ch) == (width, height) or not cw or not ch:
            return dict(self.rects)
        sx, sy = width / float(cw), height / float(ch)
        return {k: [int(x * sx), int(y * sy), int(w * sx), int(h * sy)]
                for k, (x, y, w, h) in self.rects.items()}


def ensure_dirs() -> None:
    for d in (DATA_DIR, CAPTURE_DIR, GAMES_DIR):
        os.makedirs(d, exist_ok=True)
