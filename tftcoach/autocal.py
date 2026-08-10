"""Auto-calibration — Claude proposes the HUD regions, you confirm them.

Manual box-drawing is accurate but tedious, and it has to be redone on every
resolution change and again when Set 18's Unreal client re-renders the HUD.
This asks a vision model to locate each HUD element on a real TFT frame and
writes regions.json from its answer.

It deliberately does NOT trust the model blindly: every proposed box is range
checked, and the crops are written out for eyeballing. A silently wrong region
is the worst failure mode this project has (it looks healthy and feeds garbage
to the coach), so "auto" means "auto-proposed", not "auto-accepted".

    python3 -m tftcoach.calibrate --auto --image ~/Desktop/tft.png
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config, coach
except ImportError:  # direct execution
    import config      # type: ignore
    import coach       # type: ignore


# What we ask the model to find, in its own words. Keyed to config.REGION_SPECS.
LOCATION_HINTS: Dict[str, str] = {
    "gold": "the player's current GOLD amount — the gold-coloured number in the "
            "centre bar just above the shop, next to a coin icon",
    "level": "the player's LEVEL — shown as 'Lv. N' or a number beside the XP "
             "bar at the left end of the centre bar above the shop",
    "stage": "the STAGE-ROUND indicator like '3-2', in the top-left HUD area "
             "near the round icons",
    "hp": "THIS player's health number in the player list down the right side "
          "(the row belonging to the player whose board is shown)",
    "shop": "the entire SHOP bar along the bottom — the strip containing all 5 "
            "champion cards with their names and costs",
    "board": "the hex battlefield where the player's units are deployed — the "
             "player's own half of the hexes, not the opponent's",
    "bench": "the horizontal BENCH row of 9 slots directly below the hex board "
             "and above the shop",
    "traits": "the TRAIT / synergy list stacked vertically down the left edge",
}

PROMPT = """You are calibrating a screen-reading tool for Teamfight Tactics.

Look at the attached screenshot of a TFT game and locate each HUD element listed
below. Return the bounding box of each as NORMALISED coordinates: fractions of
image width/height, where [0,0] is the top-left corner and [1,1] the bottom-right.

Elements to locate:
{elements}

Rules:
- Return ONLY a JSON object, no prose, no markdown fences.
- Shape: {{"gold": [x, y, w, h], "level": [x, y, w, h], ...}}
- x, y = top-left of the box; w, h = width/height. All four are 0..1 floats.
- Box the VALUE, not its label: for gold/level/hp include the number and a few
  pixels of padding, not the surrounding panel or the word.
- For shop/board/bench/traits, box the whole region containing all the items.
- If an element is genuinely not visible in this screenshot (for example the
  shop is hidden during combat), OMIT that key entirely. Do NOT guess a
  location for something you cannot see — a wrong box is far worse than a
  missing one.

Image: {path}"""


def _norm_to_px(box: List[float], width: int, height: int) -> Optional[List[int]]:
    """Normalised [x,y,w,h] -> pixel rect, or None if implausible."""
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return None
    try:
        x, y, w, h = (float(v) for v in box)
    except (TypeError, ValueError):
        return None
    # Reject anything outside the frame or degenerate. A box covering nearly the
    # whole screen means the model gave up and guessed; treat that as a miss.
    if not (0.0 <= x < 1.0 and 0.0 <= y < 1.0):
        return None
    if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        return None
    if x + w > 1.02 or y + h > 1.02:
        return None
    if w > 0.95 and h > 0.95:
        return None
    px = [int(round(x * width)), int(round(y * height)),
          max(1, int(round(w * width))), max(1, int(round(h * height)))]
    if px[2] < 6 or px[3] < 6:      # too small to OCR anything
        return None
    return px


# Vision models box text tightly around the glyphs they can see. That clips the
# moment the value gets wider — gold 54 -> 100, hp 78 -> 8, stage 3-2 -> 10-4.
# Numeric/short-text regions therefore get grown around their centre.
_KIND_PAD = {"number": (0.90, 0.60), "text": (0.60, 0.50)}


def _pad_rect(rect: List[int], kind: str, width: int, height: int) -> List[int]:
    grow_w, grow_h = _KIND_PAD.get(kind, (0.0, 0.0))
    if not grow_w and not grow_h:
        return rect
    x, y, w, h = rect
    # Only pad boxes that are actually small; a full-width strip needs no help.
    if w > width * 0.25:
        grow_w = 0.0
    if h > height * 0.15:
        grow_h = 0.0
    dx, dy = int(w * grow_w / 2.0), int(h * grow_h / 2.0)
    nx, ny = max(0, x - dx), max(0, y - dy)
    nw = min(width - nx, w + 2 * dx)
    nh = min(height - ny, h + 2 * dy)
    return [nx, ny, nw, nh]


def propose(image_path: str, keys: Optional[List[str]] = None,
            model: Optional[str] = None) -> Tuple[Dict[str, List[int]], List[str], str]:
    """Ask Claude to locate the HUD regions in image_path.

    Returns (rects_in_pixels, warnings, raw_reply).
    """
    warnings: List[str] = []
    if not os.path.exists(image_path):
        return {}, ["image not found: " + image_path], ""

    try:
        from PIL import Image
        with Image.open(image_path) as im:
            width, height = im.size
    except Exception as exc:
        return {}, ["could not read image ({0})".format(exc.__class__.__name__)], ""

    wanted = keys or [k for k, _, _ in config.REGION_SPECS]
    elements = "\n".join(
        "- {0}: {1}".format(k, LOCATION_HINTS.get(k, k)) for k in wanted)
    prompt = PROMPT.format(elements=elements, path=os.path.abspath(image_path))

    session = coach.ClaudeSession()
    reply = session.call(prompt, model=model)
    if coach.is_error(reply):
        return {}, ["Claude call failed: " + reply[:160]], reply

    data = coach.extract_json_object(reply)
    if not data:
        return {}, ["model did not return usable JSON"], reply

    kinds = {k: kind for k, _, kind in config.REGION_SPECS}
    rects: Dict[str, List[int]] = {}
    for key in wanted:
        if key not in data:
            warnings.append("{0}: not located (element may not be visible)".format(key))
            continue
        px = _norm_to_px(data[key], width, height)
        if px is None:
            warnings.append("{0}: rejected implausible box {1}".format(key, data[key]))
            continue
        rects[key] = _pad_rect(px, kinds.get(key, "image"), width, height)
    return rects, warnings, reply


def run(image_path: str, keys: Optional[List[str]] = None,
        model: Optional[str] = None, merge: bool = True) -> int:
    """CLI entry: propose regions, save them, write verification crops."""
    print("Asking Claude to locate the HUD in {0} ...".format(
        os.path.basename(image_path)))
    rects, warnings, _raw = propose(image_path, keys=keys, model=model)

    for warning in warnings:
        print("  ! " + warning)
    if not rects:
        print("\nNo usable regions. Fall back to manual:\n"
              "  python3 -m tftcoach.calibrate --image {0}".format(image_path))
        return 1

    try:
        from PIL import Image
        with Image.open(image_path) as im:
            size = list(im.size)
    except Exception:
        size = list(config.DEFAULT_TARGET_RES)

    existing = config.Regions.load()
    merged = dict(existing.rects) if (merge and existing.resolution == size) else {}
    merged.update(rects)
    config.Regions(merged, size).save()

    print("\nSaved {0} region(s) at {1}x{2} to {3}".format(
        len(rects), size[0], size[1], config.REGIONS_PATH))
    for key in sorted(rects):
        print("   {0:<7} {1}".format(key, rects[key]))

    written = _write_crops(image_path, merged)
    if written:
        print("\nCrops written to {0}".format(written))
        print("OPEN THEM AND CHECK before you trust this — a wrong box reads\n"
              "garbage while everything still reports healthy.")
        print("Fix any bad one manually with:\n"
              "  python3 -m tftcoach.calibrate --image {0} --only <region>"
              .format(image_path))
    missing = [k for k, _, _ in config.REGION_SPECS if k not in merged]
    if missing:
        print("\nStill missing: {0}".format(", ".join(missing)))
    return 0


def _write_crops(image_path: str, rects: Dict[str, List[int]]) -> Optional[str]:
    try:
        from PIL import Image
    except ImportError:
        return None
    out_dir = os.path.join(config.CAPTURE_DIR, "calib_check")
    os.makedirs(out_dir, exist_ok=True)
    try:
        with Image.open(image_path) as im:
            for key, (x, y, w, h) in rects.items():
                im.crop((x, y, x + w, y + h)).save(
                    os.path.join(out_dir, "{0}.png".format(key)))
    except Exception:
        return None
    return out_dir
