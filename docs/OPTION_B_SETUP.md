# Option B — setup and use

Local OCR extracts exact game state; Claude does the strategy. Verified working on
macOS 2026-08-10 except calibration, which needs a real TFT frame.

## What changed vs. the whole-screenshot coach

| | v2 (`tft_coach_v2.py`) | Option B (`run_coach.py`) |
|---|---|---|
| State | Claude guesses from one JPEG | tesseract reads exact gold/level/stage/HP/shop |
| Meta | manual paste | live MetaTFT feed, 69 comps, patch-stamped |
| Cadence | every 45 s, blind to the game | fires on round change / augment / carousel |
| Names | model may invent units | validated against CommunityDragon (73 champs) |
| Cost | frontier model every tick | fast model per tick, strong model on demand |

If calibration is missing it falls back to exactly v2's behaviour, so it is never worse.

## Setup

Dependencies are already installed on this Mac (tesseract 5.5.3, mss, pillow, numpy,
pytesseract). On the Windows box: `pip install mss pillow numpy pytesseract` and install
tesseract (`choco install tesseract`).

```bash
python3 run_coach.py --check
```

Every line should read OK except `regions`. Then, with TFT open on a **planning phase**:

```bash
python3 -m tftcoach.calibrate
```

Drag a box around each field it names (gold, level, stage, HP, shop, board, bench, traits).
Verify the crops are right:

```bash
python3 -m tftcoach.calibrate --verify
```

That writes each cropped region as a PNG so you can eyeball them. Re-run `--check`; it should
now say **All green — structured extraction active**.

## Playing

```bash
python3 run_coach.py
```

START begins the trigger loop. TIP NOW forces a call on the strong model and bypasses the
rate limit — use it at 3-2, 4-1, and augment picks. END GAME asks for your placement and
writes the vault game note, the advice audit, and lesson evidence updates.

Refresh the meta before a session (takes a few seconds):

```bash
python3 -m tftcoach.meta_feed
```

## Recalibration

Coordinates are per-resolution and per-client. Recalibrate when you change resolution or
monitor, when you switch between the Mac and the Windows box, and **on August 26, 2026**,
when Set 18 "Enchanted Wilds" moves TFT to Unreal Engine and the HUD renders differently.
That is a five-minute chore by design — no coordinates live in code.

## Troubleshooting

- **Black frames / capture fails on macOS** — System Settings → Privacy & Security →
  Screen Recording → enable your terminal, then restart it.
- **`tesseract not found`** — `brew install tesseract` (macOS) or `choco install tesseract`.
- **One field reads nonsense** — recalibrate just that region; OCR reports low confidence and
  the coach is told the field is unknown rather than being fed a wrong number.
- **"regions calibrated" but reads are wrong** — check the resolution warning in `--check`.
  Scaled rects are best effort; Riot's HUD is not a strict proportional scale.
- **Usage burning too fast** — `FAST_MODEL` / `STRONG_MODEL` in `tftcoach/coach.py`.
