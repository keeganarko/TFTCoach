---
type: reference
scope: evergreen
fetched: 2026-08-11
source: researched from Riot game data and high-level TFT sources
---

# Strategic rules

Rules with explicit conditions and boundaries, from high-level play. A rule without a boundary is a superstition — respect the 'does not apply' clauses.

---
type: principle
category: econ
scope: evergreen
verified: 2026-08-10
---

# Econ Decision Rules

Every rule states its CONDITION and its BOUNDARY. A rule without a boundary is a superstition.

**E-1 — The naming test. Before pressing roll, name the unit and the number of copies you need.**
CONDITION: every roll, every stage. If the answer is "I want my board to be stronger," you are not rolling, you are gambling. Roll targets look like: "I need 2 more Leona for 2-star," or "I need any 4-cost frontline."
BOUNDARY: does not apply to a stabilization roll at <30 HP, where "anything that adds combat power" is a legitimate target.

**E-2 — Gold above 50 is free. Never end a planning phase above 50 gold without a reason you can state.**
CONDITION: interest hard-caps at +5 at 50g. Holding 65g earns the same +5 as holding 50g — the extra 15g is idle capital.
BOUNDARY: banking past 50 IS correct when you are one round from a planned spend that needs the total (e.g. holding 58g at 4-1 to level to 8 AND still have 40g to roll at 4-2). State the plan; "saving" is not a plan.

**E-3 — Break 50 when any of these is true:**
  (a) You are losing ≥10 HP per round AND you can name a roll target (see E-1).
  (b) The spend buys a level that crosses an odds breakpoint your comp needs (7→8 for 4-costs; 6→7 for 3-costs).
  (c) It is 4-1 or later — from here the game is decided by board strength, and interest has too few rounds left to compound.
  (d) You are at ≤30 HP. At 30 HP you have ~2 losses left; 5 gold/round of interest cannot be spent by a dead player.
BOUNDARY: do NOT break 50 before 3-2 while your board is holding. Early gold compounds — 50g held from 2-5 to 4-1 generates ~40-50 gold of interest. Breaking 50 at stage 2 to buy a marginal 2-star is the classic Gold-elo tempo trap.

**E-4 — Streak gold beats interest until you reach 50.**
CONDITION: below 50 gold. A win streak is worth up to +4/round (+1 win gold, +3 streak) — more than the entire interest cap. Spending 8 gold to keep a win streak alive is usually correct.
BOUNDARY: above 50 gold you already have max interest, so the trade is just streak-gold vs board strength; buy the board. And never break a *loss* streak for one marginal win — a single win that resets a 5-loss streak costs you +2/round going forward and gains +1.

**E-5 — Level to raise odds; roll to convert odds into units. Never do both in the same round with the same gold.**
CONDITION: leveling changes the distribution, rolling samples from it. Rolling first then leveling wastes the gold spent at the worse distribution.
BOUNDARY: at ≤20 HP you may level AND roll in the same round because you may not get another round. This is a losing play you make because the alternative is dying.

**E-6 — Gold benchmarks (standard fast-8 line, healthy HP):**
  End of stage 1: **10g**. Entering 3-1: **20g**. At 4-1: **50g** and level 7. At 4-2: level 8 with **30-50g** left to roll.
CONDITION: standard non-reroll line, HP above ~50.
BOUNDARY: **35 gold is the hard floor for a level-8 rolldown.** Below 35g you do not have enough shops (17) to realistically hit; either delay a round to bank or accept you are rolling to stabilize, not to hit. If you arrive at 4-2 with 25g, you made an error two rounds earlier — the correction is to roll at 4-2 anyway (you cannot bank your way out at 4-2), not to wait until 4-5.

**E-7 — Contested lines roll EARLIER, not harder.**
CONDITION: scouting shows another player on your 4-cost carry. Whoever rolls first takes the copies out of the pool.
BOUNDARY: only if you can afford a real rolldown (≥35g) when you go first. Rolling early with 20g against a contester with 60g just donates your gold and leaves you both weak — in that case pivot instead (see R-3).

**E-8 — Fast 9 is a stage-5 decision, not a plan.**
CONDITION: consider level 9 at 5-1/5-2 only if HP > 60 AND you have a 2-star board that is currently winning AND you have 50g+ after leveling. Level 9 costs 68 XP and only moves 4-cost odds 30%→33%; what you are actually buying is 5-costs (3%→15%).
BOUNDARY: if you are not already winning fights, level 9 loses to a capped level-8 board. "I'm losing so I'll level" is correct at 8; it is wrong at 9.

---
type: principle
category: positioning
scope: evergreen
priority: highest  # player's #1 identified leak
verified: 2026-08-10
---

# Positioning Rules

## The mechanic everything derives from

**Every unit attacks the CLOSEST enemy unit. Melee units path toward the closest enemy.** Positioning is entirely the art of controlling what "closest" means for each enemy unit. The board is 4 rows deep per side (row 1 = front, nearest the enemy; row 4 = back) and 7 columns wide.

There is no such thing as "good positioning" in the abstract — only positioning that is correct against the specific board you are about to fight. This is why positioning and scouting are one skill, not two.

## Default shape (use when you have no scouting information)

**P-1 — Carry in row 4, one hex off the corner (column 2 or 6).**
CONDITION: ranged carry, default. Row 4 maximizes the time before melee reaches it. One-off-corner is chosen over the true corner because the corner is the single most predictable hex on the board — it is where jumpers land, where hooks aim, and where mirrored effects resolve.
BOUNDARY: a true corner IS correct when the enemy demonstrably has zero backline access and zero positioning items, and you want to maximize walk time. Never use the same corner two rounds in a row against the same opponent.

**P-2 — Bodyguard: your tankiest unit on a hex directly between the carry and the enemy approach.**
CONDITION: enemy frontline walks (normal melee). The bodyguard intercepts pathing and becomes the "closest enemy" for units that get past row 1.
BOUNDARY: useless against units that jump/dash past pathing, and against ranged carries who will just shoot over it. A bodyguard is a pathing tool, not a shield.

**P-3 — Grouping: no unit more than 2 hexes from its nearest ally; all non-frontline units within 2 hexes of the carry.**
CONDITION: default. THIS IS THE PLAYER'S NAMED LEAK. A split board fights two half-battles: the enemy focuses one cluster, kills it, then kills the other with a full team. Isolated units die for free and contribute nothing to protecting the carry.
BOUNDARY: overridden by P-7 (anti-AoE) when the enemy has heavy area damage, and by P-6 (frontline split) for the frontline specifically. The rule is about your BACKLINE and carry cluster; the frontline can and often should be split.

**P-4 — Melee carry goes in row 2, not row 1.**
CONDITION: your item-holder is melee. Row 2 lets your actual frontline absorb the opening damage; your carry walks in after the fight has started and arrives with its shields/mana intact.
BOUNDARY: if your carry's ability wants to be hit (rage/shield-on-damage mechanics) or it has a dash-to-target ability, front-row can be correct. Also inverted deliberately as an anti-assassin play (see P-5).

## Threat-specific counter-positioning

**P-5 — Against backline access (jumpers, divers, dashers): saturate, relocate, or bait. Pick ONE.**
CONDITION: scouting shows units that jump or dash to the backline.
  - *Saturate:* fill every hex adjacent to your carry so there is no landing space.
  - *Relocate:* move the carry to row 2 or 3 (jumpers that target the farthest unit will overshoot).
  - *Bait:* put a cheap tanky/expendable unit alone in the back corner to eat the jump.
BOUNDARY: **saturation directly contradicts P-7 (anti-AoE).** If the enemy has BOTH backline access and heavy AoE, prefer relocate or bait — never saturate. Also: baiting only works if the bait is actually the farthest/most-isolated unit; a bait surrounded by your team is not a bait.

**P-6 — Frontline split: 2 tanks on opposite flanks of row 1 rather than clumped center.**
CONDITION: enemy has line/cone AoE from their frontline, or you want to widen their pathing so they arrive at your carry staggered rather than together.
BOUNDARY: requires ≥3 frontline units. With 2 tanks, splitting means neither one holds the lane to your carry — clump them instead. Also do not split if your frontline has an aura/proximity trait or carries Zeke's/Locket-style adjacency items.

**P-7 — Against heavy AoE: at least 1 empty hex between the carry and any other unit; never 3+ units inside a 2x2 block.**
CONDITION: enemy board contains large AoE / wombo ults, or an obvious "one big cast" carry.
BOUNDARY: contradicts P-3 and P-5-saturate. Spread costs you protection — only spread as much as the specific AoE radius demands, and only for the units that would actually be caught. Never spread the whole board "just in case." **Board-wide casts cannot be dodged by spacing** (Set 17: Aurelion Sol's black hole hits everywhere) — never sacrifice clustering against those; counter with a Shroud on the caster's side, burst focus, or kill priority instead.

## Item-driven positioning (Set 17 mechanics, verbatim from CommunityDragon)

**P-8 — Zephyr targets the enemy CLOSEST to a whirlwind spawned on the OPPOSITE side of the arena.**
Exact text: *"Combat start: Summon a whirlwind on the opposite side of the arena that removes the closest enemy from combat for N seconds. [Ignores crowd control immunity.]"*
CONDITION: an opponent holds Zephyr. The whirlwind spawns mirrored from their holder's hex, and banishes whichever of YOUR units is nearest that spawn point.
CONSEQUENCE: the common advice "Zephyr hits the farthest unit" is WRONG. What matters is the mirror of the holder's position. Scout WHICH unit holds the Zephyr and move your carry away from the mirrored hex; when YOU hold Zephyr, place the holder at the mirror of THEIR carry.
BOUNDARY: it ignores CC immunity, so QSS/Quicksilver does not save you — only repositioning does.

**P-9 — Shroud of Stillness fires STRAIGHT AHEAD from the holder's hex.**
Exact text: *"Combat start: Shoot a beam that N% Mana Reaves enemies."* The beam travels forward along the holder's column.
CONDITION: an opponent holds Shroud. Any of your units in that column get their next cast delayed.
CONSEQUENCE: shift your carry ONE column off the enemy Shroud holder's column. A single-hex lateral move fully dodges it.
BOUNDARY: only mitigates the mana reave, not the rest of their board. Do not wreck an otherwise-correct position to dodge a Shroud on a non-threatening board.

**P-10 — Banshee's Veil / Banshee's Claw affect allies in the SAME ROW.**
Exact text (Veil): *"Combat start: Grant the holder and allies within N hexes in the same row immunity to crowd control and X% Attack Speed."*
CONDITION: you hold either item. The buff is ROW-based, not radius-based.
CONSEQUENCE: the holder must share a row with the carry. A Banshee's on your frontline in row 1 does nothing for a carry in row 4.
BOUNDARY: n/a — this is a hard mechanic.

## Process

**P-11 — Reposition every round from 4-1 onward, based on who you are about to fight.**
CONDITION: from stage 4 the matchup preview tells you your opponent. A position that is correct against a Zephyr board is wrong against an AoE board.
BOUNDARY: in stages 1-2 the marginal value is near zero and the time cost is real — a stable default shape is fine early.

**P-12 — Make your final positional adjustment in the last ~5 seconds of the planning phase.**
CONDITION: opponents can also scout you. Late movement gives them less time to counter-position.
BOUNDARY: never so late that you fail to actually place a unit or complete an item. Correctness beats timing.

**P-13 — If two positioning rules conflict, the one countering the board you are ACTUALLY fighting next wins.**
CONDITION: always. The conflicts are real and frequent (P-3 vs P-7; P-5-saturate vs P-7).
BOUNDARY: none. This is the tiebreak rule — and it is only usable if you scouted, which is why scouting is upstream of positioning.

---
type: principle
category: scouting
scope: evergreen
priority: high  # player's #2 identified leak — "not acting on scouting info"
verified: 2026-08-10
---

# Scouting Protocol

The player's leak is not "doesn't scout" — it is "scouts and then does nothing differently." Therefore every entry below is written as **observation → the specific decision it changes.** An observation that changes no decision was not worth making.

## Cadence (when)

| Round | Depth | Why |
|---|---|---|
| 2-1 (after augment) | Full lobby sweep | Read which lines the lobby's augments pushed people into |
| Every carousel X-4 | Full sweep — it's free, you're standing still | Items on boards + who is 2-starring what |
| 3-2 | Full sweep — **last cheap pivot point** | Contest check before you commit items and gold |
| 4-1 | Full sweep | Decide roll-at-4-1 vs 4-2; count copies of your carry |
| Every planning phase 4-1 onward | Targeted: your next opponent + the top-2 HP players | Positioning (P-11) and threat assessment |
| Any elimination | Full sweep | A dead player returns their units to the pool — your contest math just changed |

Minimum viable: **two boards per planning phase — the player you fight next, and the strongest player in the lobby.**

## Checklist (what to look at, in priority order)

1. **Items, not units.** Items tell the truth faster than traits do. A player can hold 9 units and only mean 1 of them. The dangerous enemy is the one with 3 completed items, not the one with the highest-cost unit.
2. **Star levels.** Which units are 2★/3★. This is board strength; unit count is not.
3. **Copies of YOUR carry visible anywhere in the lobby** — on boards AND on benches. This is the input to rolldown math (R-2/R-3).
4. **Backline access / positioning items** (jumpers, dashers, Zephyr, Shroud, hooks). This is the input to P-5/P-8/P-9.
5. **Benches.** Bench units reveal reroll intent and hidden contest that the board hides.
6. **Levels and HP.** Who can out-roll you, who is about to die (and return units to the pool).
7. **Open lines.** Which strong traits nobody in the lobby is playing.

## Observation → decision table (the part that fixes the leak)

| Observation | Decision it must change |
|---|---|
| 0-2 copies of my carry out | Stay the course. Roll at planned timing. |
| 3-4 copies out | Roll EARLIER than planned (E-7) if I have ≥35g; budget ~78g not ~56g. |
| **5+ copies out, and I have ≤1 in hand** | **Pivot now.** Cost to 2-star exceeds any realistic gold pool (R-3). |
| 5+ copies out but 2 in hand | Do NOT pivot — 1 more copy is ~45g, affordable. Commit. |
| Contester is 2 levels below me | Not a real contest at level 8. Ignore and proceed. |
| Contester holding my carry is at ≤15 HP | Temporary contest. Their copies return to the pool on death. Delay the roll one round if HP allows. |
| Opponent has a jumper/diver | Apply P-5 (relocate carry to row 2/3, or bait corner). Do NOT saturate if they also have AoE. |
| Opponent holds Zephyr | Move carry off the mirror of their Zephyr holder's hex (P-8). |
| Opponent holds Shroud of Stillness | Shift carry one column off their holder's column (P-9). |
| Opponent has 1 big AoE carry | Apply P-7: one empty hex around my carry. |
| Two+ players already on my exact trait line | Pivot at 3-2, not at 4-2. The cheap pivot window is stage 3. |
| A strong trait line has zero players on it | Candidate pivot if my items and augments fit it. Check the meta snapshot first. |
| Top-HP player is level 8 with a 3-item 2★ carry at 4-1 | I cannot win this lobby by economy. Convert gold to board now. |
| Everyone in the lobby is low level / econ-ing | Win streaking is cheap. Push tempo — level a round early. |
| Multiple players win-streaking with strong boards | Loss streaking is NOT safe here; damage will escalate faster than my gold. Exit the streak. |

## Boundary

Scouting has zero gold cost but real time cost, and time cost causes misplays (unbought units, unbuilt items, misplaced champions). BOUNDARY: **never scout during the last 8 seconds of a planning phase in which you intend to roll.** Buy first, position second, scout with leftover time — except at carousels and eliminations, where you have no competing task.

---
type: principle
category: items
scope: evergreen
verified: 2026-08-10
---

# Itemization Rules

**I-1 — Components on the bench have exactly zero value.**
CONDITION: always. Every round a component sits unbuilt is a round you fought at a disadvantage. The comparison is never "good item vs perfect item," it is "good item now vs perfect item later minus N rounds of losing."
BOUNDARY: a component you are deliberately holding for a known carousel/PvE drop you will get within 1-2 rounds is not idle — but you must be able to name the round.

**I-2 — Hard rule: never end stage 3 with more than one unbuilt component pair.**
CONDITION: always. By 3-7 you have had multiple item drops; carrying 4+ loose components into stage 4 means you have been fighting under-itemized for ~10 rounds.
BOUNDARY: none worth relying on. If you are holding many components at 4-1, slam the best available combination immediately — you are already behind on tempo.

**I-3 — Slam when ANY of these is true:**
  (a) You are losing rounds now (a slammed item that saves 10 HP beats a BIS item built 6 rounds later).
  (b) You are win-streaking and the slam protects the streak (streak gold is worth up to +4/round).
  (c) It is stage 2 or early stage 3 — early slams fight in the most rounds.
  (d) The item is universally strong / fits any carry your comp could land on.
BOUNDARY: does not apply when you are deliberately loss-streaking with a sacrificial board — a slam there wins nothing and costs you the BIS.

**I-4 — Hold only when ALL of these are true:**
  (a) You are one component from a specific named BIS item, AND
  (b) HP is comfortable (≥60) or you are actively win-streaking, AND
  (c) You have not yet committed to a carry.
BOUNDARY: failing ANY of the three means slam. "I might get the component" is not (a). "I'm at 45 HP but it's fine" is not (b).

**I-5 — Item distribution: 3 completed items on the primary carry before the frontline gets a second item.**
CONDITION: default for carry-centric comps. Concentrating items on one unit is almost always better than spreading — spread items lose to focused items because damage output is multiplicative on a single unit and additive across units.
Priority order: primary carry 3 offensive items → primary tank 2-3 defensive items → secondary carry / utility gets the rest.
BOUNDARY: reverses for tank-carry comps and for comps whose damage comes from a trait rather than a unit. Also reverses when your carry is not yet 2-star and your frontline is — items on a 1★ carry that dies at 3 seconds do nothing.

**I-6 — Item holders: put items on a unit that shares the eventual carry's item type, and never on a unit you plan to keep.**
CONDITION: you have items before you have your carry. An AD holder for an AD carry, AP for AP.
BOUNDARY: selling the holder to transfer items costs you a unit slot mid-fight-cycle; plan the transfer for a round you can afford to lose, or use a unit you were going to sell anyway.

**I-7 — Build defensive items when the lobby is burst-heavy; build offensive when the lobby is slow.**
CONDITION: scouting shows what kills you. Against burst, your carry needs to survive the opening; against sustain boards, you need to out-damage.
BOUNDARY: this is a marginal adjustment (the 5th-6th item), not a reason to change the carry's core 3. Do not build a defensive item on the carry at the cost of its first BIS offensive item.

**I-8 — Prioritize the MOST IMPACTFUL of the three BIS items first, not the cheapest to complete.**
CONDITION: you can build 2 of 3 BIS items now. Impact ordering usually = the item that fixes the carry's biggest deficiency (mana for slow casters, attack speed for on-hit, penetration into armor-stacked lobbies).
BOUNDARY: if completing the cheaper item this round wins the fight and the impactful one takes 2 more rounds, take the win (I-3a dominates).

**I-9 — Set 17 fact: there are 10 basic components (8 standard + Spatula + Frying Pan), and 55 two-component combined items in the set.**
Each of the 10 components appears in exactly 11 of them. Spatula and Frying Pan are emblem components with no combat stats — never slam a Spatula/Frying Pan item unless the emblem is on-comp, because you are spending a component that has a much higher ceiling.

---
type: principle
category: tempo
scope: evergreen
verified: 2026-08-10
---

# Tempo and HP Management

## HP is a currency with an exchange rate you can compute

Loss damage = base(stage) + surviving enemy units (see Core Game Math). Typical real costs:

| Stage | Typical loss (vs a full-ish board) |
|---|---|
| 2 | ~7-9 HP |
| 3 | ~10-13 HP |
| 4 | ~14-16 HP |
| 5 | ~17-19 HP |
| 6 | ~20-21 HP |
| 7+ | ~25-26 HP |

**T-1 — Convert HP to gold only at the stage where the exchange rate is good.**
CONDITION: a stage-2 loss costs ~8 HP and a stage-6 loss costs ~21. Deliberate HP spending belongs in stage 2 and early stage 3, where losses are cheap and the compounding runway for gold is longest.
BOUNDARY: from stage 5 the exchange rate is terrible — 20 HP for 3 gold of streak is never worth it. Deliberate loss streaking should be over by 4-1 at the absolute latest.

**T-2 — HP band → posture.**
| HP | Posture |
|---|---|
| 80-100 | Econ freely. Hit interest breakpoints. Greed is cheap. |
| 60-79 | Standard. Target 60-85 HP at 4-1. |
| 40-59 | On the clock. Roll at 4-1 instead of 4-2. Slam items (I-3a). |
| 30-39 | Commit. Spend past 50. You have ~2-3 losses left. |
| **≤30** | **30 HP is a signal to COMMIT, not to stop.** Level and roll in the same round if needed. Interest is worthless to a dead player. |

BOUNDARY on the ≤30 rule: committing means spending on things that change fights *this round*. It does not mean leveling to 9 hoping for a 5-cost — at ≤30 HP prefer 2-starring what you already have over reaching for new units.

**T-3 — A win streak is strictly better than a loss streak of the same length.**
CONDITION: win streak = streak bonus + 1 win gold + 0 HP lost. Loss streak = streak bonus only, plus 8-15 HP/round. If you can win-streak, win-streak.
BOUNDARY: loss streaking is still correct when your board genuinely cannot win (no 2-stars, off-comp items) and the alternative is spending gold on units you will sell. The choice is never "streak type I prefer" — it is "can this board actually win rounds this stage."

**T-4 — Do not hover. Pick a streak and commit.**
CONDITION: alternating win/loss earns +0 streak gold and still costs HP. The worst economic state in TFT is a 1-1-1-1 record.
BOUNDARY: you cannot always control it. If your record is mixed, the fix is board strength (buy/slam), not streak engineering.

**T-5 — Break a loss streak the moment either is true: HP < 40, OR you reach your planned exit round (3-2 / 4-1 / 4-5).**
CONDITION: the streak's value is capped at +3/round; below 40 HP a single bad matchup can cost 16+.
BOUNDARY: if your streak breaks by accident (you win a round you meant to lose), do NOT keep a deliberately weak board to re-establish it. The streak is gone; the correct move is to play the strongest board you can.

**T-6 — Never sell units down before a fight you expect to lose.**
CONDITION: damage taken = base + SURVIVING ENEMY units, so your own unit count does not directly add damage — but a weaker board kills fewer of theirs, so more of their units survive and you take MORE. Selling down to "take less damage" is backwards.
BOUNDARY: selling to fund a roll that wins the *next* fight is fine — the loss you eat is the price. Just be honest that you are paying ~5 extra HP for it.

**T-7 — Open fort (deliberately conceding with a minimal board) is a stage 2-3 tool only.**
CONDITION: only if it puts you at level 7-8 with 50g+ by 4-1 AND the lobby is not full of win-streakers.
BOUNDARY: it fails hard when 3+ players are win-streaking (their boards escalate damage faster than your gold compounds) and it is never correct from stage 4 on.

**T-8 — Tempo beats greed when the lobby is weak; greed beats tempo when the lobby is strong.**
CONDITION: if scouting shows a slow lobby (low levels, few 2-stars), a single level ahead wins rounds cheaply — push tempo. If the lobby is capped and strong, you cannot out-tempo it; bank and hit a bigger spike.
BOUNDARY: requires actually scouting (this is the payoff for the scouting protocol). Guessing at lobby strength is worse than a fixed plan.

---
type: principle
category: gameplan
scope: evergreen
verified: 2026-08-10
---

# Stage-by-Stage Checklist

What a strong player actually does at each decision round. Use as a per-round audit: if a box is unchecked, that is the coaching note.

## Leveling curves (Set 17, by streak state)

| Level | Win-streaking | Mixed / standard | Loss-streaking |
|---|---|---|---|
| 4 | 2-1 | 2-1 or 2-3 | 2-3 (needs 10g+) |
| 5 | 2-5 | 2-5 or 3-1 | 2-7 |
| 6 | 3-1 | 3-2 | 3-2 |
| 7 | 3-5 (needs 30g+) | 3-5 or 4-1 | 3-5 (needs 40g+) |
| 8 | 4-2 | 4-2 or 4-5 | 4-1 |
| 9 | 5-2 | 5-2 or 5-5 | 5-2 |

Reroll lines invert this: a 1-cost reroll does not press level at all until the 3-star lands; a 3-cost reroll wants level 7 by 3-5/4-1 (see R-4) and rolls there.

## 2-1 (first augment)
- [ ] Level 4 (or 2-3 if loss-streaking to econ)
- [ ] Pick the augment for **flexibility**, not for a comp you haven't seen units for. Econ augments are strongest here because they compound the longest.
- [ ] Full lobby scout — read what the lobby's augments pushed people into
- [ ] Slam any universally-good item (I-3c)
- [ ] Target: ~10g by end of stage 1

## 3-2 (second augment) — **the last cheap pivot point**
- [ ] Level 6
- [ ] Full lobby scout. **Count copies of your intended carry.** If 2+ players are on your line, pivot HERE — pivoting at 4-2 costs a whole rolldown.
- [ ] Augment choice can now be comp-specific — you know your items and your board
- [ ] Have a named carry and a named item plan
- [ ] Target: ~20g entering 3-1, and no more than 1 unbuilt component pair by end of stage 3 (I-2)

## 4-1 — the pivotal round
- [ ] Level 7 (or 8 if loss-streaking / low HP)
- [ ] Target 50g and 60-85 HP
- [ ] Full scout: count carry copies, identify positioning threats, find the strongest board
- [ ] **Decide: roll at 4-1 or 4-2?** Roll at 4-1 if contested (E-7) or HP < 50. Otherwise level at 4-2 and roll after.
- [ ] If HP < 40 → you are on the clock; level 8 now

## 4-2 (third augment) — the standard spike
- [ ] Level 8. **Never roll at 7 for 4-costs (R-5).**
- [ ] Have ≥35g AFTER leveling, or you cannot execute a real rolldown (E-6 boundary)
- [ ] Roll to a named target (E-1): the specific 4-cost and copy count
- [ ] Augment: now pick pure power for the committed comp
- [ ] Budget from the rolldown table: ~56g to 2-star an uncontested 4-cost, ~78g if 3 copies are gone

## 4-5
- [ ] Board should be a level-8 board with a 2★ carry holding 3 items
- [ ] If not: continue rolling. This is the last window where rolling still fixes the game.
- [ ] Reposition per opponent every round from here (P-11)
- [ ] If stable and healthy: bank toward level 9

## 5-1 / 5-2 — the fast-9 decision
- [ ] Level 9 ONLY if: HP > 60 AND currently winning fights AND 50g+ remaining after the level (E-8)
- [ ] Otherwise: cap the level-8 board — 3-star a 4-cost, or perfect the items, or buy a better 2★
- [ ] Remember level 9 buys 5-costs (3%→15%), not 4-costs (30%→33%)
- [ ] Positioning is now worth more than gold. Re-scout and re-position every single round.

## Universal per-round audit (every planning phase)
- [ ] Did I scout at least 2 boards (next opponent + strongest)?
- [ ] Did anything I saw change a decision? If no, I did not really scout.
- [ ] Is every unit within 2 hexes of an ally (P-3)?
- [ ] Are there loose components on my bench (I-1)?
- [ ] Am I above 50 gold with no stated plan (E-2)?
