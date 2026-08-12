---
type: reference
scope: set-bound
set: 17
fetched: 2026-08-12
source: Riot map data + web-verified tables; audited 2026-08-11
---

# TFT game math — Set 17

Shop odds, pools, round structure, damage and roll math. Mechanics, not opinions — they settle roll/level questions outright. Set-bound: regenerate from official 18.1 patch notes at rollover; until then any Set 18 math is unverified.

# Shop Odds — Set 17

Probability a single shop slot rolls each cost tier. Five slots per shop, sampled independently.

| Level | 1-cost | 2-cost | 3-cost | 4-cost | 5-cost |
|------:|-------:|-------:|-------:|-------:|-------:|
| 1  | 100% |   0% |   0% |   0% |   0% |
| 2  | 100% |   0% |   0% |   0% |   0% |
| 3  |  75% |  25% |   0% |   0% |   0% |
| 4  |  55% |  30% |  15% |   0% |   0% |
| 5  |  45% |  33% |  20% |   2% |   0% |
| 6  |  30% |  40% |  25% |   5% |   0% |
| 7  |  19% |  30% |  40% |  10% |   1% |
| 8  |  15% |  20% |  32% |  30% |   3% |
| 9  |  10% |  17% |  25% |  33% |  15% |
| 10 |   5% |  10% |  20% |  40% |  25% |
| 11 |   1% |   2% |  12% |  50% |  35% |

Coaching consequences:
- 3-cost odds PEAK at level 7 (40%), not level 8. A 3-cost reroll comp rolls at 7, never levels to 8 to "hit better".
- 4-cost odds triple from level 7 to level 8 (10% -> 30%). This is the single largest odds jump in the game and is why "level 8 then roll" is the default 4-cost line.
- 5-cost odds are 3% at 8 and 15% at 9 — a 5x jump. Do not roll for a 5-cost at level 8.
- At level 10, 4-costs (40%) still out-roll 5-costs (25%) per slot; level 10 is where 5-costs first become realistically rollable, not where they dominate.

Source: Riot game data, map22.bin.json, `Maps/Shipping/Map22/Sets/TFTSet17 -> DropRateTables.Shop -> {1ee21754}.mDropRatesByLevel`. Set 14 references the same table object, i.e. Riot has not changed base odds between those sets.

Copies per champion in the shared pool: 1-cost 30, 2-cost 25, 3-cost 18, 4-cost 10, 5-cost 9. (Two independent sources agree; the '29/22' figures in the older half of Game Math.md are wrong.) Consequences that survive the correction: 3-star 4-cost needs 9 of 10 copies — effectively dead while contested; 3-star 3-cost needs 9 of 18; a 1-cost reroll is nearly uncontestable-by-depletion (30 copies) — 1-cost contests are about shop odds, not pool exhaustion. CONDITION: denominators for all rolldown math. BOUNDARY: unique-champion counts per tier are still unreconciled across sources (roster file says 14/13/13/14/8 and is missing Zed at 5-cost; tft.ninja says 15/13/13/13/10) — regenerate the roster from CommunityDragon before recomputing per-shop hit rates, since tier totals shift the denominator.

# Round Structure — Set 17

Extracted from `Maps/Shipping/Map22/Sets/TFTSet17 -> StageRoundData -> {11d7f30e}.stages[][]`.

| Round | Type |
|-------|------|
| 1-1 | Shared carousel (`TFT_Round_Carousel`) |
| 1-2, 1-3, 1-4 | Minion rounds (`TFT17_Round_Intro1/2/3`) |
| 2-1 | **Augment 1** (`AugmentEarly`) |
| 2-4 | Shared carousel (`TFT17_Round_CarouselMarket`) |
| 2-7 | Krugs |
| 3-2 | **Augment 2** (`AugmentMid`) |
| 3-4 | Shared carousel |
| 3-7 | Wolves |
| 4-2 | **Augment 3** (`AugmentLate`) |
| 4-4 | Shared carousel — **the LAST one** |
| 4-7 | God Blessing (`TFT17_Round_GodBlessing`) |
| 5-4 … 11-4 | **Item Armory**, NOT a carousel (`TFT17_Round_PostBlessingItemArmory`) |
| 5-7 … 11-7 | Dragon (`TFT17_Round_Dragon`) |
| all other x-1/2/3/5/6 | Standard PvP combat |


## Coaching consequences
- "Scout the carousel" only applies four times a game, and the last chance to grab a specific component off a carousel is **4-4**. Component planning must be finished by then.
- After 4-4 the only new items come from armories (5-4+), PVE drops and augments — so a component you are missing at 4-4 is probably never coming. Commit the item build at 4-4, do not hold components hoping for a carousel.
- The armory rounds have only 15 s of planning (vs 30 s), so the coach must fire early and briefly on x-4 from stage 5 on.


*(triggers.py round classification verified against map data — fixed 2026-08-11.)*

# Phase Timings — Set 17 (seconds)

| Round type | Planning | Combat arrival | Combat (max) | Combat departure |
|------------|---------:|---------------:|-------------:|-----------------:|
| Standard PvP combat (`TFT_Round_Combat`) | **30.0** | 6.0 | 30.0 | 3.0 |
| Augment rounds (2-1 / 3-2 / 4-2) | **30.0** | 6.0 | 30.0 | 3.0 |
| Carousel round (`TFT17_Round_CarouselMarket`, x-4 stages 2-4) | 30.0 | 6.0 | 30.0 | 3.0 |
| PVE — Krugs / Wolves / Dragon | **20.0** | 3.0 | 30.0 | 1.0 |
| Item Armory (x-4, stages 5-11) | **15.0** | 10.0 | 30.0 | 3.0 |
| Intro rounds 1-2/1-3/1-4 | 6.0 | 3.0 | 30.0 | 1.0 |

A full standard round is at most 30 + 6 + 30 + 3 = 69 s, and typically ~50 s because combat resolves early.

## Budget rule
Advice must land inside the planning window or it is useless: the board locks the moment planning ends. Target **wall-clock from frame-grab to on-screen advice <= 12 s** on a 30 s round and **<= 7 s** on an armory round, leaving the player 18 s / 8 s to actually execute.

Budget allocation for a 30 s planning phase:
- 0.0-0.3 s screen grab + crop
- 0.3-2.5 s local extraction (tesseract on HUD numerics + template matching on board/bench/shop icons) — all CPU-local, parallelisable across regions
- 2.5-11 s one Claude call with the pre-extracted structured state
- remaining ~19 s player execution

Corollary: any added extraction must be **local and parallel**. A second network/model round-trip does not fit. Extraction that costs more than ~2.5 s of CPU must run in a background thread and be allowed to arrive as "unknown" for that tick.

Source: map22.bin.json, `Maps/Shipping/Map22/Rounds/<RoundName>.mPlanning.mDuration` etc.


## Gold income

| Source | Amount |
|---|---|
| Base income 1-2, 1-3 | +2 |
| Base income 1-4 | +3 |
| Base income 2-1 | +4 |
| Base income 2-2 onward | +5 (capped) |
| PvP win | +1 |
| PvP loss | +0 |

**Interest:** +1 gold per full 10 gold held, capped at +5.

| Gold held | Interest |
|---|---|
| 0-9 | 0 |
| 10-19 | +1 |
| 20-29 | +2 |
| 30-39 | +3 |
| 40-49 | +4 |
| 50+ | +5 (HARD CAP) |

**Consequence: every gold above 50 earns literally nothing.** Gold 51+ is free to spend. Sitting at 62 gold is identical in income to sitting at 50 gold, minus 12 gold of board strength you chose not to buy.


Streak bonuses (win OR loss streaks, identical amounts): streak of 2 = +0, streak of 3-4 = +1, streak of 5 = +2, streak of 6+ = +3. A PvP win additionally pays +1, so a max win streak earns +4/round vs +3 for a max loss streak — win streaking still strictly out-earns loss streaking. Streaks persist through PvE/carousel rounds (you still collect the bonus). CONDITION: applies to the round's income calculation every round. BOUNDARY: a 2-round streak pays nothing — do not spend gold to 'protect' a 2-streak; the earliest round worth protecting is the 3rd consecutive result. Interest is calculated BEFORE passive income lands (you must already hold the breakpoint at income time, so ending combat at 49g pays +4, not +5).

## XP / leveling (3 independent sources agree: tft-lab, op.gg, LoL wiki)

Game starts at level 2. Max level 10. **2 free XP per round. Buy 4 XP for 4 gold (1 gold = 1 XP).**

| Level up | XP needed | Cumulative XP | Max gold to buy outright |
|---|---|---|---|
| 2 → 3 | 2 | 2 | 2 |
| 3 → 4 | 6 | 8 | 6 |
| 4 → 5 | 10 | 18 | 10 |
| 5 → 6 | 20 | 38 | 20 |
| 6 → 7 | 36 | 74 | 36 |
| 7 → 8 | **60** | 134 | 60 |
| 8 → 9 | 68 | 202 | 68 |
| 9 → 10 | 68 | 270 | 68 |

Each round you wait refunds 2 gold of that cost (2 free XP). Waiting one extra round to level = 2 gold saved but one round of weaker board.


On a PvP loss: damage = base(stage) + 1 per surviving enemy unit. Star level and cost do NOT change per-unit damage (a 3-star 5-cost costs the same 1 as a 1-star 1-cost). Base by stage: 2 → 2, 3 → 5, 4 → 8, 5 → 10, 6 → 12, 7+ → 17. Worked: stage 5 loss vs 7 survivors = 17 HP; stage 7 vs 9 survivors = 26 HP. CONDITION: PvP rounds only; PvE/carousel/augment rounds deal no player damage. BOUNDARY: verified against patch 17.3 guide text; the vault's map-data extract claims stage 2 = 3, stage 4 = 7 and a stage-8 sudden-death (any loss lethal) — reverify both against 17.8 patch notes before trusting either at the margin. The coaching consequences (never sell down before a losing fight; each extra surviving ally saves ~1-3 HP; stage-5+ losses cost 15-25 HP vs 5g/round max interest) hold under both tables.

# Rolldown Math — gold per copy

Computed from the verified Set 17 odds + pool tables. Model: each shop slot independently picks a cost tier by level odds, then a uniform champion from that tier's remaining pool. "N gone" = copies of YOUR target already owned by other players (what scouting tells you).

**These are expected values. Variance is brutal — treat "gold for 2-star" as the median-ish budget, not a guarantee.**

| Situation | % per shop slot | E[copies] per 10g | Gold for 1 copy | Gold for 3 copies (0→2★) | Gold for 6 more (2★→3★) |
|---|---|---|---|---|---|
| **L8, 4-cost, uncontested** | 2.14% | 0.54 | 19g | **56g** | 112g |
| **L8, 4-cost, 3 copies gone** | 1.53% | 0.38 | 26g | **78g** | 157g |
| **L8, 4-cost, 6 copies gone** | 0.90% | 0.22 | 45g | **134g** | 268g |
| L9, 4-cost, uncontested | 2.36% | 0.59 | 17g | 51g | 102g |
| **L7, 3-cost, uncontested** | 3.08% | 0.77 | 13g | 39g | **78g** |
| L7, 3-cost, 9 gone | 1.60% | 0.40 | 25g | 75g | 150g |
| **L6, 3-cost, uncontested** | 1.92% | 0.48 | 21g | 62g | **125g** |
| L6, 3-cost, 9 gone | 1.00% | 0.25 | 40g | 120g | 240g |
| L5, 2-cost, uncontested | 2.54% | 0.63 | 16g | 47g | 95g |
| **L6, 2-cost, uncontested** | 3.08% | 0.77 | 13g | 39g | **78g** |

## Rules this table produces

**RULE R-1 — The 50g rolldown is one 4-cost 2-star.** CONDITION: level 8, uncontested. 50 gold buys 25 shops / 125 slots and yields ~2.7 expected copies of a specific 4-cost. Plan for ONE hit, not two. BOUNDARY: does not hold at level 7 (odds are 1/3), and does not hold if you are also spending that gold on other units — the 56g figure assumes you buy nothing else.

**RULE R-2 — Contest doubles your cost, then doubles it again.** CONDITION: scouting shows N copies of your carry on other boards. 0 gone → 56g to 2★. 3 gone → 78g (+39%). 6 gone → 134g (+139%). BOUNDARY: copies held by a player who is about to be eliminated return to the pool — a contested carry on a 12 HP player is temporarily contested, not permanently.

**RULE R-3 — Pivot threshold: 5+ copies gone.** CONDITION: you have not yet committed items. At 5-6 copies gone the expected cost to 2-star exceeds any realistic gold pool, so the line is dead. Pivot to an uncontested 4-cost in the same item family. BOUNDARY: does not apply if you already have 2 copies in hand (you need only 1 more, ~45g, which is affordable) or if the contesting players are 2+ levels below you and will not out-roll you.

**RULE R-4 — 3-cost reroll wants level 7, not level 6.** CONDITION: your comp's 3-star target is a 3-cost. At L7 a 3-cost is 40% of the shop vs 25% at L6; gold to 3-star drops from ~125g to ~78g (-38%). BOUNDARY: level 7 costs 36 XP AND raises your unit cap, which raises your board strength requirement; only do it if you can hold ~30g at L7 to actually roll. If you can only afford the level, stay 6 and roll.

**RULE R-5 — Never roll gold at level 7 looking for a 4-cost.** CONDITION: always, for 4-cost-centric comps. 4-cost odds are 10% at L7 vs 30% at L8. Every 2 gold spent at L7 buys one-third of the 4-costs it would buy at L8. Leveling to 8 costs at most 60g; that 60g is repaid the moment you roll. BOUNDARY: you may roll at level 7 for 3-costs (40% — the peak) or to complete a 2-star frontline that keeps you alive; that is not "rolling for 4-costs."


*(Note: 1/2-cost rows computed with corrected pool sizes 30/25 copies; differences from the earlier 29/22 figures are within a few gold.)*

E-9 — Go for level 10 when stable at 9; it is the single biggest placement delta in my measured data (L10 avg 2.52 over 58 games vs L9 avg 5.08 over 97). Cost: 68 XP = at most 68g, refunded 2g/round by free XP. At 10, per-slot odds are 4-cost 40% / 5-cost 25% — level 10 is where 5-cost 2-stars become buyable (9 copies each, ~14g/copy expected). CONDITION: at stage 5-3 onward, when (a) HP > ~45 or top-3 HP in lobby, (b) the level-9 board is already 2★-capped (rolling at 9 has a named target or none), and (c) gold after leveling >= 20 to fill the 10th slot with a real unit. Trigger for the coach: any planning phase at level 9 with 60+ gold and no named roll target = buy XP now (this is the exact 'died with 30+ banked' signature). BOUNDARY: do NOT force 10 while bleeding out (<40 HP: 2-star what you have instead — T-2), and never level 10 leaving <10g with an empty 10th slot; a 9-board + 40g of upgrades beats a 10-board + benchwarmer.

B-1 — Hold pairs of units your comp can use; sell pairs your comp cannot. CONDITION: stages 2-3, bench slack available. A pair is a free option on a 2-star (the pool rewards holding: each copy you hold both advances you and denies contesters). Priority to hold: pairs of your likely carry/tank line > pairs of units sharing your items' type > contested-line pairs held purely to deny (only if bench space is free). BOUNDARY: (a) never hold a pair through an interest breakpoint you would otherwise hit — selling a 1-cost pair to reach 20/30/40g pays compounding interest, the pair usually does not; (b) sell all speculative pairs at your committed rolldown (4-2): bench slots are needed for the roll and gold-in-pairs is gold not rolling; (c) 4-cost pairs are exempt — always hold (10 copies each makes re-finding expensive). B-2 — Never roll with a full bench: you cannot buy what you hit. Empty >=2 bench slots before any planned rolldown.
