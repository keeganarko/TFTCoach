---
type: reference
scope: set-bound
fetched: 2026-08-12
source: researched from named pro sources (attributed per section)
---

# Set 18 rollover — what breaks Aug 26 and the day-1 runbook

---
type: ops
scope: set-bound
set: 18
---

# What breaks on Aug 26 (Set 18 + Unreal), and the day-1 runbook

## What breaks
1. **Entity whitelist** (tftcoach/entities.py): apiName prefix rolls TFT17_ → TFT18_. The module is set-agnostic (derives set = max key from CommunityDragon) and has a built-in rollover detector that flags loudly until acknowledged — but it only fires AFTER a refresh. CommunityDragon may lag patch-day by hours; if the blob still says set 17 on the morning of Aug 26, retry later.
2. **OCR + regions** (regions.json, tftcoach/calibrate.py, autocal.py): the Unreal client re-renders the HUD — positions, fonts, and scaling all suspect. Rule #1 of the project (no hardcoded pixels) was built for this day; recalibration is a 5-minute chore, not a code change. Also NEW: every other shop, the rightmost slot is a **Wisp card, not a champion** — shop OCR will read wisp names that are not in any champion whitelist.
3. **Meta feeds — the stats blackout** (tftcoach/meta_feed.py): MetaTFT queue-1100 stats for 18.1 start near zero. MIN_GAMES=300 and MIN_STAT_GAMES=20000 floors mean Meta/Current Patch.md and Unit Item Augment Stats.md may render EMPTY or near-empty for ~24-72h. highelo.py (Challenger/Master+ stratified) needs longer, ~3-7 days. During the blackout the coach must lean on: this Set 18 primer pack + Strategy Rules.md + launch-week doctrine.
4. **Vault set-bound notes go stale**: Reference/Set Traits and Item Recipes.md (frontmatter set:17), Champion Ranges and Mana.md, High Elo Playbook.md (Set 17 comps), Comps/, Meta/. Game Math.md contains Set 17 shop-odds/pool tables inside an otherwise evergreen note — those tables must not be trusted for Set 18 until re-verified against 18.1 notes.
5. **October, second break**: the standalone Unreal PC client ships — capture window target and HUD may move AGAIN. Plan a second recalibration.

## Day-1 runbook (Aug 26)
1. `python3 -m tftcoach.entities --refresh` — confirm output says set 18 / prefix TFT18_. Expect the SET ROLLOVER banner; leave it unacknowledged until steps 2-5 are done. If still set 17, CommunityDragon hasn't updated — retry in a few hours.
2. `python3 -m tftcoach.reference` — regenerates the set-bound Reference notes (trait breakpoints, item recipes, ranges/mana) from the fresh blob.
3. Play/observe one Set 18 game, screenshot the full HUD, then `python3 -m tftcoach.calibrate --auto --image <frame.png>` and `--verify` — eyeball every crop; a silently wrong region is the worst failure mode. Check specifically: gold, level, stage, hp, shop strip (now sometimes 4 champions + 1 Wisp).
4. `python3 -m tftcoach.meta_feed` — expect sparse output; re-run daily through week 1. Treat any comp under the sample floor as noise.
5. Read the official 18.1 patch notes; update Game Math.md's shop-odds/pool/XP tables from them (NOT from PBE numbers).
6. Quarantine Set 17 content: mark High Elo Playbook.md and Comps/ stale (or move to an archive folder) so no prompt cites Space Gods lines.
7. Acknowledge the rollover (entities.acknowledge_rollover()) only after 1-6 pass, then `python3 run_coach.py --check`.
8. First ranked session: earliest day 2, after 2-3 normals for Wisp/mechanic reps (see launch-week doctrine).
