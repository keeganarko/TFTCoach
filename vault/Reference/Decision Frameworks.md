---
type: reference
scope: evergreen
fetched: 2026-08-12
source: researched from named pro sources (attributed per section)
---

# Decision frameworks — augments, caps, pivots, rolldowns, streaks, lobby

Rule IDs: AUG- (augments), CAP- (board capping), PV- (pivots), RD- (rolldown execution), SK- (streaks), LR- (lobby reading). Each rule has a CONDITION and a BOUNDARY; cite the ID when applying one.

---
type: principle
category: augments
scope: evergreen
verified: 2026-08-11
---

# Augment Selection — decision tree

Run this tree top-down at every augment round (2-1, 3-2, 4-2). First rule that fires decides. Complements the stage checklist (which says WHAT slot wants: 2-1 flexible/econ, 4-2 pure power); this is HOW to choose between the actual three options.

**AUG-1 — HP gate first. Below 30 HP, combat augments only.**
CONDITION: any augment round at <30 HP. Econ and scaling picks are traps — gold generated over 6+ future rounds is worthless to a player with 2 losses left. HP is harder to recover than gold (it never recovers).
BOUNDARY: does not apply above 30 HP. At 30-60 HP take balanced picks (immediate + some future value). At 60+ HP you can afford the greedy pick.

**AUG-2 — The portfolio rule: over three augments, aim for roughly 1 econ + 1 item/utility + 1 combat.**
CONDITION: default shape across a game. Econ at 2-1 (compounds longest — typically the difference between upgrading your 4-cost carry at 4-5 vs 5-2), direction/items at 3-2, pure combat power at 4-2.
BOUNDARY: the portfolio bends to state. Already rich (augment/portal gave gold)? Skip the econ slot. Item-flooded from PvE? Skip the item slot. Never take a weak econ augment at 4-2 to "complete the portfolio" — by 4-2 there are too few rounds left for it to pay back.

**AUG-3 — First augment keeps options open; the exception is a premium comp-defining pick your OPENER already supports.**
CONDITION: at 2-1 you have seen ~10 shops. Comp-specific augments lock you into a line you have no units for. Take econ or generic combat.
BOUNDARY: take the comp-specific pick at 2-1 only when ALL of: (a) it is a top-tier/prismatic-grade pick for that line, (b) your stage-1 units/items already point there, (c) the line is not visibly contested from the 2-1 lobby sweep. Two of three is not enough — that is how you get forced into a contested line at 3-2.

**AUG-4 — Payback-window test for econ/greedy picks: the augment must pay for itself before your comp's spike round.**
CONDITION: evaluating any scaling augment. Estimate rounds-to-payback (e.g. an augment worth ~2g/round vs a combat augment that saves ~4 HP/round). An econ augment taken at 3-2 has ~8-10 rounds before the 4-2 rolldown consumes the gold; taken at 4-2 it has ~3. If payback lands after the rolldown it's a dead pick.
BOUNDARY: at 60+ HP with a winning board the window extends (you can defer the spike to a level-9 game). This test is a heuristic derived from the tft.ninja immediate-vs-long-term spectrum, not a sourced constant — treat the specific round counts as tunable.

**AUG-5 — On a winstreak, tempo/combat beats econ even at 2-1.**
CONDITION: strong opener (2+ two-stars, item start) in a lobby that scouted weak. A held winstreak is worth up to +4g/round AND ~8-12 HP/round not lost; a combat augment that preserves the streak out-earns a 1g/round econ augment on both axes.
BOUNDARY: only while the streak is real. If the lobby sweep shows 2+ stronger openers, the streak will break by 2-5 regardless — take the econ pick and play the standard line.

**AUG-6 — Contest devalues comp augments.**
CONDITION: an augment is only worth its power TIMES the chance you actually complete the comp. A trait emblem for a line two other players are on is worth a fraction of its face value (contest math: 3 copies gone = +39% rolldown cost, 6 gone = +139%, see Rolldown Math R-2).
BOUNDARY: an emblem can also be the tiebreaker that lets you WIN the contest (you hit the trait breakpoint one unit cheaper). That applies only if you are ahead on copies/items — check before, not after.

**AUG-7 — Hero-type augments (set-dependent): a CARRY hero augment is a commit, a SUPPORT/utility hero augment is flexible.**
CONDITION: sets that offer unit-tied augments. Take a carry hero augment only if you hold ≥1 copy AND your items match that carry's type — it is functionally a pivot decision, so run the pivot checklist (PV-1). Support/tank hero augments slot into many boards and can be taken on generic strength.
BOUNDARY: set-bound mechanic — verify the current set even HAS hero-type augments before the coach cites this. Robinsongz's handbook pattern: some lines are 'only play WITH the augment' (e.g. 'only with Kingslayer') — meaning the augment is the comp's entry ticket, not a bonus.

---

---
type: principle
category: board-planning
scope: evergreen
verified: 2026-08-11
---

# Capped vs Uncapped — reading room to grow

Cap = the strongest board this line can realistically reach with your remaining gold/HP/pool. A board is CAPPED when no purchasable upgrade meaningfully raises its strength. Uncapped = room to grow. The entire stage-5+ game is cap management.

**CAP-1 — Room-to-grow checklist. Your board is UNCAPPED if any is true:**
  (a) A 1-2 cost unit sits on your final board past stage 4 (replaceable by a 4/5-cost).
  (b) Your carry or main tank is 1-star and its pool is not drained.
  (c) You have completed-item components sitting idle or items on wrong units.
  (d) You are below level 9 with HP and gold to level.
  (e) A trait breakpoint is one emblem/unit away.
CONDITION: audit this at 4-5 and every round of stage 5. If none are true, you are capped — stop rolling for upgrades that do not exist and bank or level instead.
BOUNDARY: 'replaceable by a 5-cost' assumes the 5-cost is enabled (CAP-3). An audit that says 'uncapped' does not say the upgrade is affordable — that's a gold question.

**CAP-2 — Backwards planning: at 4-2, name your level-9 board. Every later purchase is judged against it.**
CONDITION: from 4-2 onward, know the 8-9 unit endgame board you are building toward (the meta snapshot / High Elo Playbook gives the template). Units on the path are keeps; units not on it are rentals you will sell — do not item them, do not 2-star them at real cost.
BOUNDARY: the named board must survive contact with the lobby — re-name it if your carry's pool drains or a counter-board is topping the lobby (LR-6). Planning backwards is a compass, not a contract.

**CAP-3 — A 1-star itemless legendary is usually WORSE than the 2-star unit it replaces.**
CONDITION: stage 5+ shopping. Legendaries need enablement — items, trait web, frontline. Dropping a 2-star 3/4-cost that holds your trait web for a naked 1-star 5-cost typically lowers board strength AND feeds enemy carries mana on its death.
BOUNDARY: utility 5-costs whose value is one cast (big CC, board-wide buff) are playable at 1-star with zero items. Damage-carry 5-costs are not.

**CAP-4 — Do not roll to zero at level 9 with high HP.**
CONDITION: healthy (50+ HP) at 9. Legendaries cost 5g each on top of roll cost; hitting the unit and being unable to buy it is the classic throw. Roll in tranches: roll ~20-30g, stop, bank interest, roll again next round.
BOUNDARY: at <40 HP at 9 the tranche plan is a luxury — roll to the stabilization target and accept the zero (T-2 already governs this).

**CAP-5 — Cap vs lives: you do not need the biggest board to win the lobby, you need more lives than the boards you can't beat.**
CONDITION: stage 5+ placement play. Count boards that outcap you and boards you beat. If 2 boards outcap you but you have 30 HP on the 4th-6th place players, your win condition is outlasting, not outcapping — preserve HP, dodge the giants via positioning, let them kill each other.
BOUNDARY: flips when playing for 1st: then you MUST outcap, which means committing gold to level 9/10 and 5-cost upgrades earlier and accepting HP risk. Decide 4th-equity vs 1st-equity explicitly at 5-1, not by drift.

**CAP-6 — Selling a capped board is only correct when the pivot target's cap is clearly higher AND you can fund the transition.**
CONDITION: capped at 8, considering a late pivot (e.g. into a 5-cost board). Requires ~40g+ AND HP to eat 1-2 transition losses AND the target units actually in the pool.
BOUNDARY: from stage 5, T-2's damage table makes each transition loss cost 15-25 HP. Below 50 HP a stage-5 full re-cap is almost always a disguised 8th — see PV-5.

---

---
type: principle
category: pivoting
scope: evergreen
verified: 2026-08-11
---

# Pivot Rules — when a line is dead and how to leave it

Extends R-3 (pivot threshold: 5+ carry copies gone) and the 3-2 checklist ('last cheap pivot point'). R-3 gives the contest trigger; this gives the full signal set and the execution protocol.

**PV-1 — A line is DEAD when any one hard signal or two soft signals fire.**
HARD signals:
  (a) Contest: 5+ copies of your carry gone with ≤1 in hand (R-3), or 2 players visibly ahead of you on the same line (more copies AND better items).
  (b) Item impossibility: your carry's BIS needs components that can no longer arrive (after 4-4 the last carousel is gone — Game Math round map).
SOFT signals:
  (c) Items drifted: your slammed items fit a different carry archetype better than your planned one.
  (d) The game paid you elsewhere: multiple natural 2-stars in an uncontested different line.
  (e) Augments point elsewhere: a taken augment is premium for another line, mediocre for yours.
  (f) HP pressure: you will not survive to your comp's spike round at current loss rate.
CONDITION: evaluate at scout rounds (3-2, 4-1). One hard OR two soft = pivot.
BOUNDARY: one soft signal alone is noise — slight contest at stage 2 self-resolves (others pivot too). And rounds already invested are sunk cost: only forward value counts. 'I've been building this since 2-1' is not a reason to stay.

**PV-2 — Pivot ladder: always try the smallest pivot that fixes the problem.**
  Step 1 — carry swap: same frontline/traits, new carry that uses your items (cheapest, most common).
  Step 2 — half pivot: keep frontline, replace backline + secondary traits.
  Step 3 — full pivot: new board (most expensive, rarest — needs a rolldown's worth of gold).
CONDITION: item compatibility decides the rung — AD items pivot between AD carries, AP between AP. This is why I-6 says hold flexible slams.
BOUNDARY: a full pivot into a line you don't know how to position/itemize converts gold into confusion. If Step 3 is required after 4-2, first check PV-5.

**PV-3 — Execute inside a rolldown you were doing anyway. Never pivot from standstill.**
CONDITION: the cheapest pivot window is a level-up rolldown (3-2 at 6, 4-2 at 8) — you are already rolling, the new units simply become the buy targets. Sequence: buy new line to BENCH while old board still fights → swap in one controlled move once replacements are ≥ equal strength → then sell the old core.
BOUNDARY: never sell the old board first to fund the search — one open-board round at stage 4+ costs 14-16 HP (T-table). Exception: at ≤25 HP the staged swap is unaffordable; sell-and-roll is the losing play you make because the alternative is dying (E-5 boundary logic).

**PV-4 — During any pivot: keep pairs, sell singles, hold items on temporary holders.**
CONDITION: mid-transition, bench is the constraint. Pairs in the new line are your upgrade equity; unpaired old-line units are dead weight. Items go on the tankiest/carry-shaped unit currently fielded (I-6), not the bench.
BOUNDARY: cap speculative pairs at ~2-3 bench slots — a bench full of 'maybe' pairs at 1g interest-equivalent each is how pivots die at 0 gold with no board.

**PV-5 — The HP budget: a pivot costs 2-3 losing rounds. Price it before starting.**
CONDITION: at stage 4 that is ~30-45 HP; at stage 5+ it is 45-60. Therefore: full pivots need ~50+ HP at stage 4, and from stage 5 on a full pivot is almost never correct (most gold spent, selling 2-stars for 1-stars). Below the budget, do not pivot — stabilize the current board (roll for its 2-stars) and take the smaller placement.
BOUNDARY: 'almost never' has one exception: a stage-5 pivot INTO strictly-better units you naturally hit (e.g. armory/PvE hands you a 5-cost pair) — that is CAP-6, not a search.

---

---
type: principle
category: rolldown
scope: evergreen
verified: 2026-08-11
---

# Rolldown Execution — the 60 seconds that decide the game

E-rules decide WHEN and with HOW MUCH gold; Rolldown Math decides the budget. This is the HOW: what pros do differently during the roll itself.

**RD-1 — Pre-roll checklist (before the first refresh, ~5 seconds):**
  (a) Named targets + copy counts (E-1) INCLUDING backups ('Xayah x3; else any 4-cost frontline pair').
  (b) Bench cleared: sell dead units NOW — mid-roll bench-full moments cost shops.
  (c) Stop-loss named: the gold number where you stop (default 10-20g to keep an interest tick + next-round flexibility; 0 if stabilizing at low HP).
  (d) Items and positioning already done — never do them with roll gold ticking.
CONDITION: every planned rolldown.
BOUNDARY: a stabilization roll at <30 HP skips (c) — the stop-loss is 0 by definition (T-2).

**RD-2 — Scan every shop for three things, in order: targets, pairs, board-upgrades. Do not tunnel the carry.**
CONDITION: rolling fast is correct but blind-rolling is not — the 4-cost you aren't looking for that pairs with your bench is real equity. Each shop: (1) target? buy. (2) pair to anything held? buy if a plausible fielder. (3) strict upgrade to a fielded unit? buy.
BOUNDARY: 'buy pairs' has a budget — every non-target purchase extends the rolldown's effective cost. At tight budgets (≤40g) buy targets and direct board-upgrades only.

**RD-3 — Speculative buys: during a big rolldown, hold any uncontested 4-cost that fits your ITEMS, even off-comp.**
CONDITION: this is your miss insurance. If the rolldown misses the primary carry, a pair of item-compatible 4-costs is a functioning plan B (VoidS1n: 'backup units matter — suboptimal but upgraded beats optimal but 1-star').
BOUNDARY: 2-3 bench slots maximum for speculation, and drop the insurance the moment the primary hits. Denial-holding a CONTESTER'S carry is a separate, more expensive play — only with a free slot, while rolling anyway, when one copy visibly decides their 2-star [confidence: likely — pro practice, not formally sourced].

**RD-4 — Slam mid-rolldown the moment the carry hits. Then keep rolling.**
CONDITION: an itemless 2-star carry wins nothing tonight. Hitting → pause → slam its 2-3 items → resume. Same for the main tank.
BOUNDARY: slam from what you HAVE (I-3 logic). Do not stop the rolldown to wait on a component — the armory/PvE may pay later; the fight is now.

**RD-5 — Stop conditions. Stop when ANY fires:**
  (a) Primary target hit AND board stabilized (you now beat most of the lobby's current boards).
  (b) Stop-loss reached (RD-1c).
  (c) The pool says no: you've seen enough shops to know the copies aren't there (recount — an elimination may have returned copies; scout note in protocol).
CONDITION: pre-named in RD-1.
BOUNDARY: hitting the carry is NOT automatically (a) — if you still lose fights, the roll continues for frontline 2-stars. Conversely 'one more roll' after (a) fires is how winstreaks become 30g of nothing: after stabilizing, excess gold goes to levels, not rolls (VoidS1n's under-greed mistake #2).

**RD-6 — Rolling past the stop-loss is allowed in exactly two cases:**
  (a) Death otherwise: ≤30 HP and the current board loses to everyone — keep rolling, interest is worthless to a dead player (T-2).
  (b) Contested race: the contester is also rolling THIS round — copies bought now are copies they never see; stopping mid-race donates the pool (extends E-7).
CONDITION: (b) requires scouting their gold/level during your roll.
BOUNDARY: (b) does not apply if they finished rolling already (pool damage done — stop normally) or if your budget cannot realistically finish the 2-star (Rolldown Math contest table: 6 gone = 134g. You don't have it — accept and pivot).

**RD-7 — Miss protocol: field backups, freeze the level, re-roll at the SAME level after 2-3 econ rounds.**
CONDITION: you missed at stop-loss/zero. Field the best 2-stars you found (speculative buys now start), hold target pairs, bank to ~30g, roll again at the same level — the odds that justified this rolldown haven't changed, your gold has.
BOUNDARY: level first instead only when the level itself adds a fielded unit slot or trait breakpoint that wins rounds NOW, or when the miss was caused by contest so deep (R-3) that the correct move is the pivot, not the re-roll.

---

---
type: principle
category: streaks
scope: evergreen
verified: 2026-08-11
---

# Streak Management — choosing and running a streak deliberately

T-3..T-7 give the streak laws (win>loss, don't hover, exit points, open-fort boundary). This adds the COMMIT decision, the execution mechanics, and the marginal math. Streak gold table (Game Math): 2-4 streak = +1, 5 = +2, 6+ = +3; wins add +1 more.

**SK-1 — Commit at 2-1, from the opener, not from hope. Three-way read:**
  (a) STRONG opener (2+ two-stars by 2-1, coherent item start, ideally a tanky front): commit WIN streak — level 4 at 2-1, slam items (I-3b), play strongest board every round.
  (b) TRASH opener (no 2-stars, scattered units, off-item components): commit LOSS streak / open fort — sell toward interest breakpoints, econ hard.
  (c) MIDDLE opener: play strongest board WITHOUT streak spending; let rounds 2-1..2-3 tell you which streak found you, then feed that one.
CONDITION: the 2-1 lobby sweep modifies the read — a 'strong' opener in a lobby of stronger openers is a middle opener.
BOUNDARY: never commit (b) just because streak gold sounds clever — loss streaking is the FALLBACK when winning is impossible (T-3), and BunnyMuffins' Set 17 constraint applies: a full loss-streaker must win most of stage 4 or dies — the plan must include the stabilization rolldown that makes that true.

**SK-2 — Win-streak preservation budget: up to ~8-12g per round of off-curve spending while the streak is live and real.**
CONDITION: a live 5+ winstreak pays +4g/round AND saves the 8-15 HP a loss costs. Early levels (3-1 instead of 3-2), small rolls at 3-1/3-5 to complete pairs, and streak-protecting slams all pay for themselves within ~2-3 rounds. This is why the winstreak leveling curve (High Elo Playbook timings, BunnyMuffins) runs a round ahead.
BOUNDARY: the budget exists only while the streak would actually continue — spending 12g to win a round you'd have won anyway is -12g, and spending into a lobby where 2 boards beat you regardless is burning the econ AND losing. Scout the next 2-3 opponents before spending (rotation reading, LR-4).

**SK-3 — Open-fort execution (the T-7 conditions hold: stage 2-3 tool, fails vs 3+ winstreakers):**
  Round-by-round: 2-1 sell everything not needed for interest breakpoints, field minimum legal board; hold items UNBUILT (slamming helps you win — you don't want to win, and unbuilt components keep pivot options); buy only pairs that serve the eventual board; hit every 10g interest tick; at Krugs (2-7) field enough to CLEAR PvE (PvE loss = no loot, pure disaster); target ~50g by Krugs; then convert — level aggressively at 3-2/4-1 and roll into the strongest board while the lobby's mid-tier boards are still 1-starred.
CONDITION: executed correctly you arrive at 4-1 level 7-8 with 50g+ and a fresh item pool against boards that spent theirs.
BOUNDARY: the HP bill is ~35-50 by 4-1 — the conversion rolldown is MANDATORY, not optional; an open-forter who greeds past 4-1 is an 8th. And do not open fort into a portal/set-mechanic that rewards wins [check current set].

**SK-4 — Streak-break math: breaking the ENEMY streak is worth more than the round.**
CONDITION: beating a 6+ streaker doesn't just deal them damage — it zeroes their +3-4/round income; over the next 3 rounds that's ~10-12g swing, roughly a free rolldown denied. When two boards you could counter-position are streaking, prioritize beating the longer streak.
BOUNDARY: never throw your own econ/board plan to do it — this is a tiebreaker for positioning effort and small spends, not a strategy. Your own accidental streak-break: T-5 boundary already covers it (play strongest board, don't re-engineer).

**SK-5 — Mixed-record lobbies are won on raw board strength; vertical traits are the cheapest strength.**
CONDITION: when you can't hold either streak (T-4 hover state), the efficient play is a vertical-trait board — synergy depth from cheap units — which stabilizes stage 4 without 4-cost luck, banking placement equity while streakers polarize.
BOUNDARY: vertical boards cap lower (CAP-1) — this buys stage-4 stability and top-4 equity at the cost of 1st-place equity. Re-evaluate the cap at 5-1.

---

---
type: principle
category: lobby-reading
scope: evergreen
verified: 2026-08-11
---

# Lobby Reading — the game is 8 players, not 1 board

The Scouting Protocol says what to LOOK at and its observation→decision table handles per-round calls. This is the layer above: choosing and steering your LINE by what the other seven boards are doing.

**LR-1 — A comp's value in YOUR lobby = meta strength × contest discount × counter exposure. Uncontested A-tier beats contested S-tier.**
CONDITION: the contest discount is quantified in Rolldown Math R-2: 3 copies gone = +39% rolldown cost, 6 gone = +139%. An S-tier comp split two ways costs each player ~1.4x the gold for the same board — that's worse than an A-tier comp at face cost. Meta averages (the Meta/ snapshot) assume average contest; your lobby is the real number.
BOUNDARY: uncontested is a multiplier, not a base — an uncontested C-tier line is still a C-tier line. The floor: only lines that hold up at Master+ (High Elo Playbook delta list marks the traps).

**LR-2 — The 2-1 census: bucket all 7 opponents by probable line before choosing yours.**
CONDITION: after augment 1, sweep and read units+bench+items+augment per player (bench and items tell the truth; fielded synergies mislead — flexible players slot units temporarily). Output: a rough map of where the lobby is crowding. Choose your direction to maximize distance from the crowd among the lines your opener supports.
BOUNDARY: 'your opener supports' is the binding constraint — forcing an uncontested line against your items and units is worse than sharing a line you're ahead on. At 2-1 the census is probabilistic; re-run it at 3-2 (the checklist's contest count) before committing items.

**LR-3 — Calibrate tempo TO the lobby, not to a fixed plan.**
CONDITION: read aggregate lobby tempo from levels/gold/board strength. Lobby econ-ing with weak boards → nobody pressures your HP → greed alongside them (rolling early buys pressure nobody feels — pure waste). Lobby aggressive with streaking boards → HP is being taxed now → stabilize first, econ later. elbroc's example: 3-2 with pairs but low gold, lobby greedy → hold gold, stay aligned.
BOUNDARY: this is relative positioning, not follow-the-leader — if you hold a genuine tempo advantage (strong board a level up), PUSH it precisely because the lobby is passive (T-8 already encodes the exchange; this adds: re-read every stage, tempo states flip).

**LR-4 — Endgame rotation math: from stage 5 you are not fighting 'the lobby', you are fighting a shrinking rotation of named boards.**
CONDITION: with 4-6 players alive, list who you can actually face in the next 2-3 rounds. Position and itemize for THOSE boards (P-11 does per-round; this is the 2-3-round plan). Run the HP race: at current stage damage (T-table), count who dies before you if current results repeat. If 2+ players die first, your top-4 is secured by stalling, not by beating the strongest board — spend accordingly.
BOUNDARY: rotation math degrades the moment someone spikes (level 9, 3-star hit) — recompute on every elimination and every visible spike, and remember eliminations return copies to the pool (scouting protocol note).

**LR-5 — Second on a line: be ahead or be first to roll, or leave.**
CONDITION: if the census still shows you sharing a line, you may stay ONLY if you are ahead on copies+items, or you can reach the rolldown level first with a real budget (E-7: contested lines roll earlier). Otherwise the line is theirs — take the exit at 3-2 while it's cheap (PV-1).
BOUNDARY: contest by a player 2 levels below you or at ≤15 HP is not real contest (scouting table already encodes both).

**LR-6 — Counter-exposure check at 4-5/5-1: if 2+ of the top-HP boards structurally counter you, adjust the FINAL board even at raw-strength cost.**
CONDITION: structural counters are knowable in advance — heavy AoE vs your clustered board (P-7), anti-tank/shred vs your single-tank wall, CC chains vs a single-carry board, assassin/dive vs an unprotected backline (P-5). Adjustments: the flex slot becomes a utility/CC unit, the 5th item goes defensive (I-7), the secondary carry gets the anti-armor item.
BOUNDARY: adjust the margins, never the core (I-7's boundary: not at the cost of the carry's core 3). If the counter is so hard the margins can't fix it, that is a CAP-5 lives problem: dodge them in the rotation and outlast.
