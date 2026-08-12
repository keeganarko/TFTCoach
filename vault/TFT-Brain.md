---
type: index
updated: 2026-08-11
player: keegancho#NA1
---

# TFT Brain — Index

Entry point loaded at the start of every game. Kept small: the numbers that
change decisions live here, everything else is linked and loaded on demand.

## How this vault works

- **[[Player Profile]]** (`Profile/`) — measured from 200 ranked games. This is
  the highest-confidence personal data in the vault and outranks anything
  inferred. Regenerate with `python3 -m tftcoach.player_profile`.
- **`Reference/`** — evergreen game math and strategy: trait breakpoints, item
  recipes, shop odds, econ rules. Not opinion; mechanics.
- **`Meta/`** — machine-written patch snapshots (comps, unit/item/augment
  stats). Never hand-edit; regenerated per patch.
- **`Lessons/`** — atomic claims from my own games, each with boundary
  conditions. `candidate` → `confirmed` (3+ games) → promoted here, or `retired`.
- **`Games/`** — one note per match. Raw material, append-only.

## Source precedence

Current-patch statistics → measured player profile → reference strategy →
individual lessons → the model's general (possibly stale-set) knowledge.
With only a few games logged, individual Lessons are priors, not laws.

## Measured leaks — coach against these every game

Numbers live in [[Player Profile]] (single source of truth — quote it, do not
copy figures here; copies have drifted once already).

1. **Dying with 30+ gold in the bank** — the 30+ bucket averages ~5.4 and is
   the 8th-place signature. The leak is specifically 30+ banked while bleeding:
   the 0-4 bucket is *also* bad (spending down to zero without a plan), and
   5-20 left is the healthy zone.
   → *Trigger: HP under 40 and gold 30+ at stage 4-5 → spend down toward
   5-20 left. Boundary: do not break interest breakpoints before stage 4 while
   healthy (E-3), and never spend to zero without a named purchase.*
2. **Not converting level 9 into level 10.** Final level 10 averages ~2.5 vs
   ~6.5 at level 8. Most of my 5th-8th places die in stage 5 (105 of 200
   games); the levers that move stage-5 survival in my data are completed
   items and board size — the elimination-stage table itself restates
   placement, so cite the levers, not the table.
   → *Trigger: at stage 5+ with gold banked, buy levels per E-9, not interest.*
3. **Incomplete items and thin boards.** 4+ units holding 3 items ≈ 3.4 avg vs
   ≈ 6.0 with two; boards of 11+ ≈ 3.0 vs ≈ 6.4 at 8 or fewer.
   → *Trigger: prefer completing a third/fourth item and fielding every paid
   slot over hoarding components or gold.*

**Do not chase 3-stars.** Games with 2+ three-stars average 4.65 — identical to
games with none. Completed items and board size predict placement; 3-stars do not.

## Known patterns

- **Losing trait lines (replicated):** Astronaut ~5.1–5.3 over 28–43 games and
  Primordian ~5.05–5.67 both sit well below the 4.675 baseline. Avoid forcing them.
- **Complacency, not tilt.** The game after a top-4 averages 5.14; after a bot-4,
  4.40. Flag the game following a strong finish.
- **Lobby strength swings ~1.0 placement.** Normalise any read against lobby avg.

### Carry and trait attribution — treat as soft

Two independent passes over the same 200 games disagreed on which unit was "the
carry" (one said Blitzcrank 3.32 / Illaoi 6.00, the other Ivern Minion 3.50 /
Illaoi 4.67) and on Dark Star (2.61 vs 4.55). Match history records a final
board, not intent, so "the carry" is inferred by heuristic and the label moves
with the heuristic. **Do not state per-carry averages as fact.** The aggregate
tables in [[Player Profile]] — gold left, final level, item completion, board
size, elimination stage — replicated exactly across both passes and are safe to
coach from.

## Standing instructions to the coach

- Advice must cite observed state (gold, level, stage, HP). No generic tips.
- Never recommend a comp the current [[Meta]] snapshot does not support.
- When a lesson and the current patch conflict, the patch wins — flag the lesson
  for review rather than following it.
- Unmeasured ≠ unimportant: positioning and scouting quality cannot be seen in
  match history, so absence of data there is not evidence they are fine.
