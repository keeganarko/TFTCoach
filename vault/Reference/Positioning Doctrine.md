---
type: reference
scope: evergreen
fetched: 2026-08-12
source: researched from named pro sources (attributed per section)
---

# Positioning doctrine — adaptive, matchup-driven

The High Elo Playbook gives static per-comp positions; this file is what changes them: matchup counters, carry protection, tank shapes, the 15-second scout-then-move routine, and the ranked Platinum mistakes.

---
type: principle
category: positioning
scope: evergreen
priority: highest
verified: 2026-08-11
---

# Positioning Matchup Playbook

Extends P-1..P-13 (Strategy Rules). These are the ADAPTIVE responses: identify the enemy archetype during scouting, apply the matching PM rule. Board notation: r1 = my front row, r4 = my back row, c1-c7 left to right. If two PM rules conflict, P-13 arbitrates (counter the board you actually fight next).

**PM-1 — vs combat-start backline jumpers (Set 17 Rogues: Talon, Briar, Gwen, Fizz, Kai'Sa, Riven).**
MECHANIC (verified): Rogues jump to the enemy backline AT COMBAT START; below 50% HP they slip into shadows and attackers are redirected to a nearby unit, preferring tanks.
CONDITION: enemy fields 2+ Rogues, or any Rogue holding 2+ items.
MOVES, pick exactly ONE (they conflict):
- *Carry-front:* swap carry to r2 center (r2c4). Jumpers land in your now-empty backline where only cheap units sit; your tanks and carry fight them from the front side. Best when they have 3+ Rogues (saturation can't stop that many).
- *Saturate:* fill all hexes adjacent to the carry (carry r4c2 → occupy r4c1, r4c3, r3c1, r3c2, r3c3) so there is no adjacent landing hex; jumpers land 2+ hexes away and eat bodyguard aggro first.
- *Bait:* one expendable 1-cost alone in the far back corner opposite your carry — it must be the most isolated backline unit to draw the jump.
BOUNDARY: NEVER saturate if the enemy also has clump-punish AoE (Blitzcrank disco ball targets your LARGEST CLUMP; Jinx splash; Morgana radius chain) — use carry-front instead. Because low-HP Rogues redirect aggro to your tanks, do not count on your bodyguard killing them; the counter is positioning, not the sandwich.

**PM-2 — vs artillery / long range (Set 17 Snipers: Jhin, Xayah, Vex, Kindred, Miss Fortune, Samira all range 6; Ezreal, Gnar).**
MECHANIC (verified): Sniper trait grants damage amp PLUS per-hex amp by distance to target: (2) 18% +2%/hex, (3) 24% +3%/hex, (4) 28% +4%/hex, (5) 32% +5%/hex. Your r4 backline is ~8-9 hexes from their snipers — at 4 Snipers that is ~32-36% bonus damage you are gifting.
MOVES: compress FORWARD — backline moves r4 → r3 (each hex forward removes 3-5% of their amp), and shift your whole board toward the sniper's column side to further cut distance. Corner-hiding your carry does NOTHING vs range 6 + distance amp; it increases it.
BOUNDARY: only compress when their board is sniper-centric with a thin frontline. If they run Snipers AND Rogues/heavy melee, compression walks into the dive — then hold r4 and win the fight elsewhere (kill order, tank line).

**PM-3 — vs AoE wombo. Split by SHAPE — the counter differs (verified shapes in Set 17 Threat Table note):**
- *Radius casts* (Morgana chain-stun in radius, Blitzcrank disco ball 3-hex radius): checkerboard the backline — units on alternating columns (c1, c3, c5), max cluster size 2. This is P-7 executed concretely.
- *Line casts* (Gnar boulder, Viktor death ray, Jhin final-shot pierce): never stack two units in the same COLUMN; offset every r2/r3 unit one column from the unit in front of it.
- *Largest-clump targeting* (Blitzcrank): the ball goes to your BIGGEST clump — so give him one: 3 tanks deliberately clumped on the flank AWAY from your carry eats the ball; keep every other cluster ≤2.
- *Board-wide casts* (Aurelion Sol expanding black hole): spreading does NOTHING. Do not wreck your protection to dodge it. Counters: Shroud his column (he starts 15/75 mana — the reave delays the cast meaningfully), focused burst before cast, or win the DPS race.
BOUNDARY: spacing costs protection (contradicts P-3/P-5-saturate). Spread only the units the specific shape would actually catch.

**PM-4 — vs wrap/flank melee (Set 17: DRX Marauder boards — Akali, Bel'Veth, Rek'Sai, Rhaast, Master Yi, Briar).**
MECHANIC: melee path to the closest enemy; with a narrow wall they walk AROUND it into your backline (wrap). A wide wall makes 'closest' = the wall itself.
- *Prevent wrap:* widen r1 to 5+ occupied columns with both edge columns anchored (units at c1 and c7). With only 3-4 frontliners, refuse one flank: full wall on your carry's side, single tanky speed-bump at the far corner (r1c7 if carry is c1-side) to delay the wraparound.
- *Induce wrap (offense):* when YOUR melee outclass their front, clump your melee on one side; enemy units wrap and expose their backline to you.
BOUNDARY: a wide wall is thin — vs burst-focus boards a 2-deep staggered front (TL-3) beats width. Wrap-prevention is for melee-heavy enemies only; vs ranged boards width wastes bodies.

**PM-5 — vs enemy corner carry (meta boards corner Xayah/Kindred/Zoe/Vex at r4c1 — see High Elo Playbook).**
MOVES, stack all that apply:
- Your Zephyr holder → the MIRROR of their carry's hex (P-8 mechanic, offensive use).
- Your Shroud holder → their carry's column.
- Shift your frontline weight toward their carry's side so your melee path arrives at the corner instead of stalling center; TFT Ninja: spread your frontline so some units path toward the corner rather than getting stuck on the enemy frontline in the center.
- Your own Rogues need no help — they jump backline anyway.
BOUNDARY: shifting weight opens your other flank; only commit the shift when their board has no melee to punish it (scout first, P-13).

**PM-6 — vs lowest-HP-target hunters (Set 17 Samira: fires at the TWO LOWEST-HEALTH enemies, resets on takedown; Kindred 'Wolf hunts the weak').**
MECHANIC: targeting ignores distance — positioning cannot dodge it; unit SELECTION is the positioning move.
MOVES: bench low-HP chaff before this fight (a 1-star 1-cost is a free reset battery); no half-HP units on board; give your weakest fielded unit defensive spacing so the reset chain stalls.
BOUNDARY: don't cut a trait-critical body — losing a breakpoint costs more than one reset.

---

---
type: principle
category: positioning
scope: evergreen
priority: highest
verified: 2026-08-11
---

# Carry Protection Patterns

Extends P-1/P-2/P-3. Where exactly the carry lives and what surrounds it, decided by scouted threats.

**CP-1 — Placement decision table (ranged carry):**
| Scouted enemy board | Carry hex |
|---|---|
| No backline access, no Zephyr, no sniper advantage | r4 c2/c6 (off-corner default, P-1) |
| Zero backline access AND zero positioning items | true corner r4c1/c7 — max walk time (P-1 boundary) |
| Rogues/divers present | r2c4 (carry-front, PM-1) or saturated r4c2 |
| 3+ Snipers | r3, shifted toward their sniper side (PM-2) |
| Enemy Zephyr | ≥2 hexes from the mirror of their holder's hex (CP-4) |
| Facing same opponent again (endgame) | the OTHER side from last round (CP-5) |
Center-back (r4c4) niche: TFT Ninja — center carries 'attack the most relevant enemies because they are equidistant from the center of the action'; use when your carry must hit their key frontliner early. Cost: max AoE exposure.

**CP-2 — Box beats clump (r/CompetitiveTFT doctrine: 'You want to create a box around the carries. Boxing>clumping').**
CONDITION: default protection shape. A solid blob around the carry feeds radius AoE and clump-targeting; an open box intercepts pathing just as well.
SHAPE for carry r4c2: protectors at r3c1, r3c3, r4c4 — every approach lane is zoned, but the carry has breathing hexes and no 3-unit cluster exists.
BOUNDARY: vs 3+ Rogues the box's empty adjacent hexes are LANDING hexes — close them (PM-1 saturate) or abandon the box for carry-front.

**CP-3 — Bodyguard sandwich (upgrade of P-2 for one-side boards):**
CONDITION: carry in/near a corner, enemy approach predictable from one arc.
SHAPE: two tanky bodies DIAGONALLY covering both entry angles — carry r4c2: sandwich at r3c1 + r3c3; third body r4c4 seals the lateral walk. The tankiest body goes on the side facing the enemy's melee weight.
BOUNDARY: a sandwich is a pathing tool — useless vs ranged focus and vs jumpers who land behind it (P-2 boundary inherited). Do not pull your main r1 tank back to build it; use secondary tanks.

**CP-4 — Anti-Zephyr / anti-targeted-CC spacing:**
MECHANIC (P-8): Zephyr banishes YOUR unit closest to a whirlwind spawned at the MIRROR of the holder's hex, ignoring CC immunity.
MOVES: identify their holder's hex while scouting → compute the mirror on your side → keep the carry ≥2 hexes from it AND park a durable non-carry ON or adjacent to the mirror hex as the designated banish-eater. A banished TANK is nearly free; a banished carry is the fight.
BOUNDARY: they can move the holder late (P-12 cuts both ways) — if their Zephyr unit moved this round, re-derive the mirror; when out of time, default the carry AWAY from the corner it occupied last round (corners are the favorite Zephyr target).

**CP-5 — Endgame leapfrog (2-3 players left):**
CONDITION: you fight the same opponent repeatedly; they counter-position against what they saw last round.
MOVE: alternate carry side every rematch (c2 ↔ c6), and make the swap in the final 5 seconds (P-12). Never the same corner twice into the same opponent (extends P-1 boundary).
BOUNDARY: if the opponent demonstrably never repositions (scout says their board is frozen), stop rotating and take the strictly best position instead.

**CP-6 — When the carry goes FRONT (row 1-2):**
CONDITIONS (any): (a) melee carry — default r2 (P-4); (b) ability/mechanic charges from taking damage or the unit gains mana when hit — Dignitas: place such carries closer to the frontline 'to receive stray ability hits for faster mana generation', trading safety for a faster first cast; (c) anti-dive inversion (PM-1 carry-front); (d) durable ranged carry with defensive items when their whole threat is backline access.
BOUNDARY: never front a squishy no-sustain carry into artillery or line-AoE boards; the stray-hits trick is for boards whose chip damage will not kill the carry before its cast pays off.

---

---
type: principle
category: positioning
scope: evergreen
verified: 2026-08-11
---

# Tank Line Shapes

Extends P-6. Every shape is derived from three targeting facts:
1. Every unit attacks its CLOSEST enemy at combat start (equidistant → effectively random pick, per Mobalytics — do not rely on ties).
2. Melee must occupy a hex ADJACENT to their target; if all adjacent hexes are taken they retarget or path around — bodies physically block lanes.
3. Melee walk the shortest path — an unguarded flank IS a path (wrap, PM-4).

**TL-1 — Full wall (5-7 columns of r1 occupied).**
CONDITION: enemy is melee-heavy / wrap threat. Anchor BOTH edges (c1+c7 occupied) — an edge gap is a highway.
BOUNDARY: thin — one row deep. Vs burst boards that delete r1 fast, prefer TL-3 depth over width. Requires 5+ front-capable bodies.

**TL-2 — Split front (2+2 on opposite flanks, e.g. c2c3 + c5c6).**
CONDITION (P-6): enemy line/cone AoE from their front, or you want their melee to arrive at your carry staggered, not together — the split forces their units to choose lanes and widens their pathing.
BOUNDARY (P-6 inherited): needs ≥3-4 frontliners; with 2 tanks clump them on the carry's side instead — a split pair holds neither lane. Never split adjacency-buff frontlines (aura traits, Leona-style adjacent-ally shielding, Zeke's-type items).

**TL-3 — Staggered depth (r1 tanks with r2 bodies offset one column).**
SHAPE: r1 at c2/c4/c6, r2 at c3/c5. A breach through r1 meets a second body one step later; the column offset means no line-cast (Gnar boulder, Viktor ray, Jhin pierce) hits both rows.
CONDITION: default vs mixed boards; the correct compromise between wall and split.
BOUNDARY: costs backline bodies; don't strip the carry box (CP-2) to build depth.

**TL-4 — The 1-hex gap: 3-4 tanks at c1/c3/c5/c7 cover a 7-wide front.**
MECHANIC: melee attackers must stand adjacent — a tank every other column still zones every approach hex, so gapped coverage ≈ full coverage with fewer bodies, AND the spacing dodges clump/radius punishment (Blitzcrank ball, Morgana radius) and covers more front so enemies can't slip past (spread-don't-clump, per Mobalytics/TFT Ninja).
BOUNDARY: a gap is also a corridor — vs 4+ melee some WILL path through the gaps to r2; only run gapped fronts with a staggered r2 (TL-3) or vs ranged-heavy boards where nothing walks through.

**TL-5 — Tank ORDER inside the line: tankiest on the OUTSIDE edges, weaker tanks inside (per positioning guides); your main itemized tank goes on the side of the enemy's damage weight so it, not a 1-star filler, absorbs the opening focus.**
CONDITION: any multi-tank front. Scout which side their carry shoots from first.
BOUNDARY: if your main tank anchors an adjacency trait, trait geometry wins.

**TL-6 — Surround for kill speed: 4 attack slots around a lone frontliner.**
MECHANIC: only ~4 of your units can attack one enemy tank at a time (adjacent hexes on your side); vs a one-tank enemy front, arrange melee so all 4 slots fill instantly and excess melee path PAST to the backline instead of queueing.
CONDITION: enemy has a single frontliner; your melee-heavy board.
BOUNDARY: irrelevant vs wide fronts; do not chase this while abandoning your own carry's protection.

---

---
type: protocol
category: positioning
scope: evergreen
priority: highest
verified: 2026-08-11
---

# Scout-Then-Move: 15 seconds, one planning phase

Closes the player's measured gap: scouting that changes nothing. Every look maps to ONE move. Runs every planning phase from 4-1 (P-11); before 4-1 only at carousels. Complements the Scouting Protocol cadence table — this is the per-phase micro-routine.

**Phase A — 0-3s: WHO.** Read the matchup indicator for your next opponent. If it's ambiguous, assume the strongest board among candidates.

**Phase B — 3-10s: THEIR board, five looks in fixed order. Each look binds to one response:**
1. *Carry hex + corner side* → plan your Zephyr/Shroud/flank-weight response (PM-5); note which side their damage comes from (TL-5).
2. *Backline access count* — Rogues fielded, dash units, dive items → pick ONE of carry-front / saturate / bait (PM-1). Zero access = carry stays r4.
3. *Positioning items* — find the Zephyr holder's hex → compute your mirror hex (CP-4); find Shroud holder → note its column (P-9: shift carry one column off).
4. *AoE shapes* — radius (Morgana/Blitzcrank) → cluster ≤2; line (Gnar/Viktor/Jhin) → column offsets; board-wide (Aurelion Sol) → do NOT spread, plan Shroud/burst (PM-3).
5. *Frontline weight* — melee-heavy → wall/refuse-flank (PM-4); sniper-heavy → compress forward (PM-2).

**Phase C — 10-15s: YOUR moves, strict priority order, cap 4 moves:**
1. Carry hex (CP-1 table) — always first.
2. Zephyr-mirror dodge + banish-eater placement (CP-4).
3. Spacing/column fixes for the scouted AoE shape.
4. Tank line shape (TL-1..TL-4).
If under 8 seconds remain: move ONLY the carry. A perfect tank line around a Zephyr'd carry is a lost fight.

**Standing rules:** execute final moves in the last ~5s (P-12) but never so late a unit is left unplaced. On a roll-down turn, this routine is SKIPPED except Phase A + carry move (Scouting Protocol boundary: never scout in the last 8s of a rolling phase). With 2-3 players left, run the routine every round and add the leapfrog (CP-5).

**The contract: zero moves after a scout = the scout was wasted. If all five looks genuinely demand nothing, say so explicitly ('scouted, position already correct') — that is the only acceptable no-move outcome.**

---

---
type: reference
category: positioning
scope: evergreen
verified: 2026-08-11
note: ranking = frequency of citation across coaching sources (TFT Ninja, Bamboo Gaming, Dignitas, Mobalytics, eloboost24, r/CompetitiveTFT), not measured game data
---

# Platinum Positioning Mistakes, Ranked

1. **The frozen board.** Setting a position once and never touching it again; scouting late-game only or never. Cited by every coaching source. FIX: SM protocol every phase from 4-1; P-11 is a hard trigger, not a suggestion.
2. **Autopilot corner carry.** Carry parked in the same far corner all game 'because corners are safe' — the corner is the most predictable hex in TFT: it is where Zephyrs mirror, jumpers land, and counter-positioning aims. FIX: corner only via the CP-1 decision table (verified no access + no positioning items); otherwise off-corner, and alternate sides in endgame (CP-5).
3. **Random clumping / random spreading.** Blobbing everything around the carry (feeds radius AoE and clump-targeting) or spreading 'just in case' (feeds dive and loses protection) without reading the enemy board. Sources are explicit: some matchups punish clumping, others punish spreading — never do either without a scouted reason. FIX: box over clump (CP-2); spread only for the specific scouted shape (PM-3).
4. **Scouting without acting** (this player's measured leak) — looking at boards, changing nothing. FIX: the SM contract — every look binds to a move or an explicit 'position already correct'.
5. **Melee carry buried or blocked.** Melee carry in r3/r4, or walled in by its own units, wasting the fight walking. FIX: melee carry r2 (P-4), clear its exit hexes; front it only per CP-6.
6. **Two-island board / stray units.** Backline split into separated clusters, or single units drifting on a flank, letting the enemy win two half-fights (P-3 violation) and handing wrap lanes to melee. FIX: one connected shape — carry cluster + tank line; refuse a flank deliberately (PM-4), never accidentally.
7. **Over-scouting.** Burning the whole phase reading boards, then failing to buy/position — sources call out missing your own shop timer and unplaced units. FIX: the 15-second cap and the under-8s rule (SM Phase C).
8. **Counter-positioning ghosts.** Moving units 'to be safe' with no specific threat, which un-counters the board you actually fight. FIX: Bamboo Gaming's rule — never move a unit without naming the threat the move answers.
