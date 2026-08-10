# TFT Coach v1 — Re-analysis (2026-08-10)

Honest audit of everything built so far, as the baseline for the v2 revamp.
Companion docs: [REVAMP_OPTIONS.md](REVAMP_OPTIONS.md) (where we go next),
[OBSIDIAN_BRAIN.md](OBSIDIAN_BRAIN.md) (lessons-learned vault design).

## What v1 is

A single-file Python/Tkinter overlay (`tft_coach_gemini.py`, ~470 lines) targeting
Windows (winsound, `C:\Coach\notes`, PowerShell instructions). Loop:

1. Every 30–60 s (or on F9): screenshot the left monitor, downscale to 1280 px wide, JPEG q75.
2. Send the image + one big prompt to **Gemini 2.5 Flash-Lite**.
3. Prompt = hardcoded Set 17 / patch 17.3 tier list + economy/leveling/item fundamentals
   + all `.txt` lesson files + last 3 tips.
4. Show ≤4 color-coded bullets (`[ECON]/[ITEM]/[BOARD]/[COMBAT]`) in the overlay, beep.
5. "End Game" → Gemini reflects over the session's tips → lesson `.txt` saved to the notes
   folder, auto-loaded next session.

Three real sessions were played with it (2026-05-17, 05-24, 05-25; 1–6 calls each).

## What v1 got right

These carry forward into v2:

- **The self-improvement loop exists.** Post-game reflection → saved lessons → reinjected next
  session. The 05-25 lesson ("interest breakpoints are not a rigid rule — spend to stabilize
  when weak") is exactly the kind of compounding knowledge v2's Obsidian brain formalizes.
- **Meta-in-the-prompt works.** Grounding the model with a tier list + fundamentals produced
  specific, mostly-correct advice (comp calls, Rod itemization, interest coaching). The flaw is
  that the meta is *hardcoded*, not that the approach is wrong.
- **Cadence + hotkey UX.** 30–60 s ambient tips plus on-demand F9 is the right interaction
  shape for a game with ~30 s planning phases.
- **Anti-repetition** (last 3 tips passed back) and **rank-aware framing** are cheap and effective.
- **Cost discipline.** Sessions cost fractions of a cent; a live cost tracker kept that visible.

## What's broken or limiting

Ordered by how much each caps the ceiling of the advice:

1. **The meta knowledge is frozen in May 2026.** Set 17 / patch 17.3 tier lists are hardcoded
   in the prompt. TFT ships a new set roughly every 4 months and balance patches every ~2 weeks —
   by now the tier list is not just stale, it's likely for a set that no longer exists. Stale meta
   advice is *worse* than none: it confidently recommends comps that were nerfed or removed.
2. **No structured game state.** One downscaled JPEG → the model guesses gold/level/HP/shop from
   pixels every time, with no memory of the previous frame. Consequences:
   - No opponent tracking (README promises it; the code has none).
   - No trend awareness (HP bleeding, econ curve, streak state).
   - Advice can't be validated ("save to 50g" when the player is at 50g already).
3. **The session "history" is advice history, not game history.** The model sees its own last
   3 tips, not what actually happened. Post-game lessons are therefore *reflections on the tips*,
   not on the game — the 05-17 lesson literally grades its own advice ("GOOD CALLS") with no
   ground truth (placement, final board, opponents) to grade against.
4. **No match outcome data.** Riot's match API records final placement, final board, augments,
   and every opponent's comp for free — v1 never asks. Lessons that don't know whether you went
   1st or 8th can't self-improve.
5. **Flat lesson files.** Append-only `.txt` in one folder, all concatenated into every prompt.
   No dedup/consolidation → lessons pile up instead of compounding, and prompt size grows
   linearly with games played. No structure (comp, patch, mistake-type) to retrieve against.
6. **Fixed model, fixed pipeline.** Flash-Lite does vision *and* strategy in one call. Cheap, but
   the strategic ceiling is the weakest link — the user's goal ("best advice possible, strong
   models") wants strategy on a frontier model with vision extraction kept fast/cheap.
7. **Security: a Gemini API key was hardcoded** in an error-message string and committed to the
   public repo (scrubbed from the file 2026-08-10, but it lives in git history — **the key must
   be revoked**). v2 keeps all secrets in env/keychain.
8. **Smaller issues:** screenshot downscale to 1280 px destroys small text (gold, shop costs) that
   OCR or vision models need; cost tracking uses hardcoded token estimates, not actual usage;
   the coaching loop blocks in `time.sleep` per second; `NOTES_DIR` is an absolute Windows path;
   platform mismatch (developed on macOS, runs on Windows) is unhandled.

## What the three sessions tell us

Small sample, but consistent themes the coach itself surfaced:

- **Econ vs. board-strength tension** appears in all three lessons — v1 defaulted to "save to 50g"
  and later had to walk it back. A lessons brain should have promoted "spend to stabilize when
  bleeding" to an evergreen principle after game 2.
- **Scouting/positioning** flagged twice as the improvement area — exactly what a
  screenshot-only pipeline is worst at coaching (it never sees opponent boards unless you scout
  while it captures).
- Usage was light (1–6 calls/game vs. a possible ~40 at 30 s cadence over a ~35-min game) —
  either the tool wasn't running the whole game or tips weren't worth the glance. v2's bar:
  advice good enough to check every round.

## Design principles for v2 (derived from the above)

1. **Separate perception from strategy.** Fast/cheap extraction of structured state
   (gold, level, stage, HP, shop, board, augments) feeding a strong reasoning model.
2. **Live data over hardcoded knowledge.** Current-set static data + current-patch meta tier
   lists fetched automatically; the tool should know what patch it's on.
3. **Ground truth closes the loop.** Pull the Riot match result after every game; lessons are
   written against actual placement and final boards, not against the coach's own tips.
4. **Structured, compounding memory.** Obsidian vault with per-game notes, distilled lessons,
   and evergreen principles — consolidated, deduplicated, and selectively loaded per game.
5. **State accumulates across the game.** Each analysis sees the game timeline so far, not an
   amnesiac single frame.
