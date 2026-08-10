---
type: reference
scope: set-bound
fetched: 2026-08-11
source: researched from Riot game data and high-level TFT sources
---

# TFT game math — Set 17

Shop odds, pool sizes, round structure, damage and roll math. These are mechanics, not opinions — they settle roll/level questions outright.

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
- Level 9 is where 4-cost (33%) and 5-cost (15%) are both live; level 10 favours 5-costs over 4-costs on a per-slot basis only marginally (40 vs 25).

Source: Riot game data, map22.bin.json, `Maps/Shipping/Map22/Sets/TFTSet17 -> DropRateTables.Shop -> {1ee21754}.mDropRatesByLevel`. Set 14 references the same table object, i.e. Riot has not changed base odds between those sets.

# Champion Pool — Set 17

| Cost | Champions in tier | Copies of EACH | Total copies in tier |
|-----:|------------------:|---------------:|---------------------:|
| 1 | 14 | 29 | 406 |
| 2 | 13 | 22 | 286 |
| 3 | 13 | 18 | 234 |
| 4 | 14 | 10 | 140 |
| 5 |  8 |  9 |  72 |

**1-cost (29 copies each):** Aatrox, Briar, Caitlyn, Cho'Gath, Ezreal, Leona, Lissandra, Nasus, Poppy, Rek'Sai, Talon, Teemo, Twisted Fate, Veigar

**2-cost (22 each):** Akali, Bel'Veth, Gnar, Gragas, Gwen, Meepsie (IvernMinion), Jax, Jinx, Milio, Mordekaiser, Pantheon, Pyke, Zoe

**3-cost (18 each):** Aurora, Diana, Fizz, Illaoi, Kai'Sa, Lulu, Maokai, Miss Fortune, Ornn, Rhaast, Samira, Urgot, Viktor

**4-cost (10 each):** Aurelion Sol, Corki, The Mighty Mech (Galio), Karma, Kindred, LeBlanc, Master Yi, Morgana, Nami, Nunu & Willump, Rammus, Riven, Tahm Kench, Xayah

**5-cost (9 each):** Bard, Blitzcrank, Fiora, Graves, Jhin, Shen, Sona, Vex

Use: a 3-star 4-cost needs 9 of 10 copies — effectively impossible while contested. A 3-star 3-cost needs 9 of 18. Scouting two other boards holding your 4-cost carry means 20-40% of its pool is gone before you roll.

Source: map22.bin.json, ScriptData.TierBagListName = 'Set17_TierBags' -> Set17_TierBag1..5.

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

## Correction to the codebase
`tftcoach/triggers.py:42-43` currently asserts "the shared carousel is round x-4 from stage 2 on". That is **wrong for Set 17 from 5-4 onward**. Carousels exist only at 1-1, 2-4, 3-4 and 4-4. From 5-4 the x-4 slot is a 15-second item armory where you pick an item from a personal selection — there is no shared board to scout and no priority order.

The augment rounds in that same comment (2-1 / 3-2 / 4-2) ARE correct and are confirmed by the same source.

## Coaching consequences
- "Scout the carousel" only applies four times a game, and the last chance to grab a specific component off a carousel is **4-4**. Component planning must be finished by then.
- After 4-4 the only new items come from armories (5-4+), PVE drops and augments — so a component you are missing at 4-4 is probably never coming. Commit the item build at 4-4, do not hold components hoping for a carousel.
- The armory rounds have only 15 s of planning (vs 30 s), so the coach must fire early and briefly on x-4 from stage 5 on.

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

# Player Damage — Set 17

Base damage taken on a loss, by stage (added to the per-surviving-unit damage the winner's board deals):

| Stage | Base damage |
|------:|------------:|
| 1 | 0 |
| 2 | 3 |
| 3 | 5 |
| 4 | 7 |
| 5 | 10 |
| 6 | 12 |
| 7 | 17 |
| 8+ | 10000 (sudden death — any loss eliminates) |

Also in the same constants block: `DamageToHealthConversion = 0.20`.

## Coaching consequences
- Damage nearly doubles from stage 4 (7) to stage 6 (12) and again to stage 7 (17). A 40 HP lead at 4-1 is roughly six free losses; at 6-1 it is barely three.
- **Direct counter to the over-saving leak:** at stage 5+ a lost round costs >= 10 base HP plus unit damage — usually 15-25 total. Holding 50 gold for interest earns 5 gold. Two losses at stage 5 cost more HP than three rounds of interest are worth. Below ~40 HP at stage 5, or ~50 HP at stage 6, the correct play is to spend down to the level/board that wins the next round.
- Stage 8 is lethal: any loss from 8-1 onward ends the game regardless of HP. Every plan must assume the game ends in stage 7.

Source: map22.bin.json, object {489202b9}.mConstants.PlayerDamageStage1..8.

# Rolldown Math — Set 17

Derived from the verified shop-odds table and pool sizes. `p_slot = tier_odds(level) * copies_of_target_left / copies_of_tier_left`; per-shop `p = 1 - (1 - p_slot)^5`; each roll costs 2 gold.

## Chance of seeing at least one copy of ONE named champion, per 2g roll, full pool

| Level | 1-cost | 2-cost | 3-cost | 4-cost | 5-cost |
|------:|-------:|-------:|-------:|-------:|-------:|
| 4  | 18.2% | 11.0% |  5.6% |  0.0% |  0.0% |
| 5  | 15.1% | 12.1% |  7.5% |  0.7% |  0.0% |
| 6  | 10.3% | 14.5% |  9.3% |  1.8% |  0.0% |
| 7  |  6.6% | 11.0% | 14.5% |  3.5% |  0.6% |
| 8  |  5.2% |  7.5% | 11.7% | 10.3% |  1.9% |
| 9  |  3.5% |  6.4% |  9.3% | 11.2% |  9.0% |
| 10 |  1.8% |  3.8% |  7.5% | 13.5% | 14.7% |
| 11 |  0.4% |  0.8% |  4.5% | 16.6% | 20.0% |

## Expected gold per copy found (2g / p)

| Level | 1c | 2c | 3c | 4c | 5c |
|------:|---:|---:|---:|---:|---:|
| 8  |  38g |  27g |  17g |  19g | 107g |
| 9  |  57g |  31g |  22g |  18g |  22g |
| 10 | 113g |  53g |  27g |  15g |  14g |

## The contest penalty (level 8, one named 4-cost, 10 copies total)

| Copies held by other players | Chance per roll | Gold per copy |
|-----------------------------:|----------------:|--------------:|
| 0 | 10.3% | 19g |
| 3 |  7.4% | 27g |
| 5 |  5.4% | 37g |
| 7 |  3.3% | 60g |

**This is the number that makes scouting actionable.** Seeing 5 copies of your intended carry on other boards triples the gold cost of your rolldown, from ~19g to ~37g per copy. If a scout at 4-1 shows two opponents already 2-starred your carry (6 copies gone), pivot; do not roll into it.

Caveat: this assumes uniform pool depletion within the tier, which is a lower bound on the penalty — the tier denominator also shrinks, which slightly helps, and it is included above.

---
type: reference
category: game-math
scope: set-bound
set: 17
patch: "17.8"
verified: 2026-08-10
expires: 2026-08-26  # Set 18 "Enchanted Wilds" launch — REGENERATE ALL OF THIS
---

# Core Game Math — Set 17

Every econ/roll recommendation must be arithmetic against these tables, not vibes.

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

## Streak gold

| Streak length | Bonus (win OR loss) |
|---|---|
| 2 | +1 |
| 3 | +1 |
| 4 | +1 |
| 5 | +2 |
| 6+ | +3 |

A win streak is worth streak bonus **+1 win gold** = up to +4/round. A loss streak of the same length is worth only the streak bonus. **Win streaking out-earns loss streaking at every streak length.** Loss streaking is a HP-for-tempo trade, never a gold-maximizing play.

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

## Shop odds by level (majority source: metabot.gg + redeemertft, corroborated by tft.ninja L8=30%/L9=33%,15%)

| Level | 1-cost | 2-cost | 3-cost | 4-cost | 5-cost |
|---|---|---|---|---|---|
| 1-2 | 100% | 0 | 0 | 0 | 0 |
| 3 | 75% | 25% | 0 | 0 | 0 |
| 4 | 55% | 30% | 15% | 0 | 0 |
| 5 | 45% | 33% | 20% | 2% | 0 |
| 6 | 30% | 40% | 25% | 5% | 0 |
| 7 | 19% | 30% | 40% | 10% | 1% |
| 8 | 15% | 20% | 32% | **30%** | 3% |
| 9 | 10% | 17% | 25% | 33% | **15%** |
| 10 | 5% | 10% | 20% | 40% | 25% |
| 11 | 1% | 2% | 12% | 50% | 35% |

**THE key breakpoint: 4-cost odds triple from L7 (10%) to L8 (30%).** This is the single largest probability jump in the game. It is also why L8→L9 barely helps your 4-cost (30%→33%) but transforms your 5-cost (3%→15%).

**3-cost peaks at level 7 (40%).** Level 6 is 25%. A 3-cost reroll board that can afford level 7 rolls 1.6x more efficiently than at level 6.

## Pool sizes (metabot.gg + esportstales agree; redeemertft's 29/22 is the outlier — ignore it)

| Cost | Copies per champion | Unique champs (CommunityDragon TFTSet17) | Total tier pool |
|---|---|---|---|
| 1 | 30 | 18 | 540 |
| 2 | 25 | 13 | 325 |
| 3 | 18 | 13 | 234 |
| 4 | 10 | 14 | 140 |
| 5 | 9 | 10 | 90 |

Shop refresh = 2 gold, 5 slots.

## Player damage on a PvP loss

**Damage = base(stage) + number of surviving enemy units.** Star level does NOT change per-unit damage — a 3-star costs you the same 1 as a 1-star.

| Stage | Base damage |
|---|---|
| 1 | 0 |
| 2 | 2 |
| 3 | 5 |
| 4 | 8 |
| 5 | 10 |
| 6 | 12 |
| 7+ | 17 |

Worked: stage 3 loss w/ 5 survivors = 10. Stage 4 w/ 6 = 14. Stage 6 w/ 9 = 21. Stage 6 clean wipe (0 survivors) = 12. Stage 7 w/ 9 = 26.

**Corollary:** losing 8-2 (barely) at stage 5 costs ~11-12 HP; losing 8-0 costs ~19. Getting one more unit to survive is worth real HP. Never sell down your board before a fight you will lose.

## Round structure

- **Augments: 2-1, 3-2, 4-2.**
- **Carousels: X-4 for stages 2 through 7.**
- **PvE: 1-2, 1-3, 1-4 (minions), 2-7 (Krugs), 3-7 (Wolves/Raptors), 4-7, 5-7/6-7/7-7 (boss).**
- PvE, carousel and augment rounds deal you no HP damage.

Stage 2 has 7 rounds; every stage 2+ follows X-1..X-7 with X-4 carousel and X-7 PvE.

---
type: reference
category: game-math
scope: derived
set: 17
method: "p(slot) = shop_odds[level][cost] x (copies_left / tier_pool_remaining); 5 slots per 2g refresh"
verified: 2026-08-10
---

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
