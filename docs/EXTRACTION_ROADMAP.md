---
type: reference
scope: evergreen
fetched: 2026-08-11
source: researched from Riot game data and high-level TFT sources
---

# Extraction roadmap

What the extractor cannot yet see, ranked, plus how to get it. Hex geometry is the highest-value item: unit positions are invisible today.

# Board Hex Mapping (the #1 leak, currently invisible)

## Verified result
A **projective homography** maps hex (row, col) to screen pixels accurately enough to assign every unit to a cell. Fitted against the 28 published hex centers for 1920x1080:

| Model | Mean error | Max error |
|-------|-----------:|----------:|
| 4-corner homography | **1.91 px** | **5.29 px** |
| 28-point homography | 1.99 px | 4.43 px |
| Affine (no perspective) | 8.28 px | 21.43 px |

Hex half-width is 58-64 px, so a 5.3 px max error is ~9% of a hex radius — never enough to misassign a cell. Affine is NOT good enough near the far row.

## Board-plane coordinate convention
Rows 0..3 counted from the row nearest the camera (screen-bottom) to the far row. Cols 0..6 left to right.
```
x_plane = col + (0.5 if row % 2 == 0 else 0.0)   # even rows offset half a hex right
y_plane = row
```

## Reference hex centers at 1920x1080 (row-major, row 0 = nearest, col 0 = leftmost)
```
row0 y=651: x = 581, 707, 839, 966, 1091, 1222, 1349   (pitch 128.0, half-width 64.0)
row1 y=571: x = 532, 660, 776, 903, 1022, 1147, 1275   (pitch 123.8, half-width 61.9)
row2 y=494: x = 609, 723, 841, 962, 1082, 1198, 1318   (pitch 118.2, half-width 59.1)
row3 y=423: x = 557, 673, 791, 907, 1019, 1138, 1251   (pitch 115.7, half-width 57.8)
```
Row-to-row y deltas: 80, 77, 71 px (perspective foreshortening). Row centres alternate: rows 0 and 2 centre at x~964, rows 1 and 3 at x~904.

## Homography fitted from the four corner hexes (row0col0, row0col6, row3col0, row3col6), H normalized so H[2][2]=1
```
H = [[ 1.28000e+02,  3.31306e+01,  5.17000e+02],
     [ 0.00000e+00, -6.09654e+01,  6.51000e+02],
     [ 0.00000e+00,  3.55427e-02,  1.00000e+00]]
```
Forward: `[u,v,w] = H @ [x_plane, y_plane, 1]; screen = (u/w, v/w)`.
Inverse (screen pixel -> nearest hex): apply `inv(H)` to the pixel, then round `y_plane` to the nearest integer row and `x_plane - 0.5*(row%2==0)` to the nearest integer col; reject if either residual > 0.5.

## Calibration procedure (5 clicks, resolution-independent)
Ask the user to click the centre of the four corner hexes of their own board, then solve the 4-point DLT. This replaces any hardcoded coordinate table and survives resolution changes, ultrawide, and windowed mode — unlike proportional scaling of a rect, which `tftcoach/config.py:Regions.for_resolution` already warns is unreliable.

## Detecting WHICH hex is occupied (two options, cheapest first)
1. **Health-bar anchor.** Every deployed unit renders a health bar at a fixed offset above its hex. Detect the bars (a saturated horizontal strip, easy colour threshold: team-blue vs enemy-red), take each bar's midpoint x and add a fixed downward offset to reach the unit's foot position, then inverse-homography that point. Robust because bars are 2D screen-space overlays, unaffected by champion model size or animation. Also gives you the enemy/ally split for free while scouting.
2. **Star/rarity crown anchor.** Same idea using the star pips above the bar; gives star level in the same pass.

Do not try to segment the 3D champion models — they overhang neighbouring hexes and animate.

## Why this is worth building
No external source has positioning. Riot's match API (`units[]` = character_id/itemNames/tier only), MetaTFT comps_data, and every 404'd `/positioning` endpoint all lack hex coordinates. Positions exist only on the screen. Since positioning is this player's #1 named leak, this is the highest-leverage extraction in the project.

# Extraction Gap Analysis

Currently read: stage, gold, level, HP, shop, board units+items+stars, traits (see `tftcoach/config.py:REGION_SPECS`).

| # | Missing signal | Coaching value | Effort | How to get it |
|---|----------------|----------------|--------|----------------|
| 1 | **Hex positions of own units** | Highest — the player's #1 named leak, and currently 100% invisible. Enables "your carry is on the front-left corner, move it to row 3 col 5". | Medium | 4-corner homography (see the hex-geometry note) + health-bar anchor detection. No new model calls. |
| 2 | **All-8 player HP + level list** | Very high, near-zero cost. Directly counters the over-saving leak: coach can say "you are 4th-lowest HP with 3 players above 80 — spend now". Also gives lobby tempo (is anyone at level 9 already?). | Low | The 8 player rows are a fixed HUD strip on the right. OCR the numbers. `ROUND_ENCOUNTER_ICON_POS` in jfd02/TFT-OCR-BOT locates the 8 player slots at the top for 1920x1080; add one calibration rect. |
| 3 | **Win/loss streak** | High. The state dataclass ALREADY has a `streak` field (`tftcoach/state.py:GameState.streak`) but no region feeds it — it is dead. Streak is the input to every econ decision. | Very low | The streak pip row sits under the player's own HP bar. One rect, one classifier (count pips, colour = W/L). Field already plumbed through `known_fields()` and `summary_line()`. |
| 4 | **Item components on bench** | High. Currently the coach cannot say "you have Bow + Rod, build Guinsoo's on Jinx". Needs both the bench-item strip read AND the recipe table (which is missing from entities.json). | Low-Medium | The 10 item slots are a fixed cluster (`ITEM_POS` in TFT-OCR-BOT). Template-match against `squareIconPath` sprites from tftitems.json — 9 components only, a tiny template bank, very high accuracy. |
| 5 | **Augment choices offered** | High but bursty — matters exactly 3 times per game (2-1, 3-2, 4-2), and those are the highest-EV decisions in the game. `triggers.py` already classifies the augment round. | Low | 3 fixed name rects (`AUGMENT_POS`). Plain OCR of the augment title, validated against the 271-augment whitelist already in entities.json. |
| 6 | **Opponent board while scouting** | High for the "not acting on scouting info" leak, and it is the input to contest detection. | Medium | Same board homography, applied while the camera is on an opponent. Detect the scouting state by reading the opponent-name plate (`PANEL_NAME_LOC`); when it is non-empty, the board region shows someone else. Store per-opponent last-seen board. |
| 7 | **Carousel contents** | Medium — only 4 rounds per game now (1-1, 2-4, 3-4, 4-4), and the pick window is short. | Medium | The carousel is a ring of moving units; template matching is harder than a static grid. Lower priority given only 4 occurrences. |
| 8 | **Unit pool depletion** | High value, but see the inference note — it is cheaper to INFER than to read. | n/a | Inferred, not extracted. |
| 9 | **Remaining rerolls / reroll count** | Low. Gold already tells you how many rolls you can afford (gold/2). | n/a | Skip. |

Recommendation: items 2, 3 and 5 are all single-rect OCR additions costing well under 500 ms combined and should ship before the harder CV work in items 1 and 6.

# Inference Layer — signals you get for free from the timeline

The project already has an append-only per-game `Timeline` (`tftcoach/state.py:Timeline`) with a `delta()` method. Almost none of the following is being computed from it yet.

## 1. Pool depletion from units seen
Maintain a per-game counter: every distinct copy of a champion observed on any board (yours or a scouted opponent's), weighted by star level — a 1-star is 1 copy, 2-star is 3, 3-star is 9. Subtract from the verified pool table. Feed the residual into the contest-penalty table. A 2-star 4-cost on an opponent board removes 3 of 10 copies and raises your cost per copy from 19g to 27g at level 8.

This is strictly better than not knowing, even from partial observation: observed copies are a hard lower bound on depletion.

## 2. Contested lines from shop starvation
Track, per champion you want, the number of shop slots seen versus the expected number given level and rolls. Expected appearances over N rolls at level L = `5 * N * odds(L, cost) * copies_left / tier_pool`. If you have rolled 15 times at level 8 for a 4-cost (expected ~1.5 sightings) and seen zero, that is a ~22% event — weak evidence. Twenty-five rolls with zero sightings is ~7% — strong evidence the champion is held elsewhere. This turns "I'm not hitting" into a quantified pivot signal.

## 3. Opponent comps from elimination order and HP curve
Each tick, record every opponent's HP from the player list. Deltas tell you who lost to whom without watching combat. A player whose HP is flat for three stages is the lobby's strongest board and is the one you must beat to place top 2. A player dropping 15+ per round is dying and their board's units return to the pool within a round or two — which raises YOUR hit rate on their carry.

## 4. Level/econ trajectory
From `Timeline.delta()`: gold delta per round tells you whether the player is on the econ curve (net +5 or better per round when not spending) or bleeding. Combined with the HP curve and the stage damage table, this is the leak-detection signal: "HP -22 over the last 2 rounds while gold went +11 — you are saving into a loss streak".

## 5. Item components you will never complete
Once the last carousel (4-4) is past, the component set is nearly fixed. Any component held after 4-4 that cannot pair with anything on the bench into a usable item should be flagged as a slot-in-anything (Thief's Gloves / Tactician's Crown) or a sell.

## 6. Screen/phase inference
`triggers.py` already classifies rounds by stage string. Extend it with the verified round map so it knows, without reading the screen, whether the current x-4 is a carousel (stages 2-4) or a 15-second armory (stages 5-11), and adjust both the coaching content and the response deadline accordingly.

# Prior Art

| Repo | Stars | License | Last push | What to reuse | Caution |
|------|------:|---------|-----------|---------------|---------|
| **jfd02/TFT-OCR-BOT** | 341 | GPL-3.0 | 2024-04-18 | `screen_coords.py` (4601 B) — the 28 BOARD_LOC hex centers, 9 BENCH_LOC, 10 ITEM_POS, 3 AUGMENT_POS/AUGMENT_LOC/AUGMENT_ROLL, 5 CHAMP_NAME_POS shop-name rects, 8 ROUND_ENCOUNTER_ICON_POS player slots, GOLD_POS, ROUND_POS, PANEL_NAME_LOC. All at 1920x1080. Also `arena.py` (20919 B) for bench/board bookkeeping and `ocr.py` (2458 B) for tesseract preprocessing. | **GPL-3.0 is viral.** Do not vendor the code into TFTCoach. Use the coordinates as *reference measurements* to validate your own homography and to seed calibration defaults — coordinate numbers derived from someone's screen are facts about Riot's UI, not the repo's expression. Set 8.5-era layout; re-verify against a current frame. |
| Kyrluckechuck/TFT-Bot | 44 | AGPL-3.0 | 2024-04-20 | Windows window-handle capture and DPI handling patterns. | AGPL, even more viral. Read for approach only. |
| how-do-youeven/Computer-Vision-for-TeamFight-Tactics | 1 | none | 2026-07-26 | Closest in spirit to the pool-depletion idea ("see what units are bought by everyone, then calculate chances of rolling"). Recently active. | No license = all rights reserved; do not copy. Worth reading for the depletion-tracking approach. |
| IlyaRusskikh/tft-ai-shopper | 1 | GPL-3.0 | 2024-10-12 | YOLOv8 champion detection setup — a reference for whether a learned detector beats template matching for the shop bar. | Tiny, stale, GPL. |
| Borcioo/tft-scout | 1 | none | 2026-04-20 | Confirms CommunityDragon ingest is the standard path for champion data. | Not useful beyond that. |

## Nothing exists for the thing you need most
Searches for TFT hex mapping, scouting overlays and augment detection returned nothing usable. There is no maintained open-source hex-position extractor. The homography approach in the hex-geometry note is the build.

## Licensing bottom line
Every TFT CV project of any size is GPL/AGPL. Build the extractor independently; use the published coordinates only as measurements to check your own calibration against.
