---
type: player-profile
player: keegancho#NA1
season: set17
sample: 200 ranked games
source: tft.dakgg.io (no API key)
generated: 2026-08-11
generated_by: tftcoach.player_profile
---

# Player Profile — keegancho#NA1

Counted outcomes over 200 ranked games. Regenerate: `python3 -m tftcoach.player_profile`.

| Metric | Value |
|---|---|
| Average placement | **4.675** |
| 1st rate | 13.0% |
| Top-4 rate | 45.0% |
| Mean gold left | 15.01 |
| Mean end level | 8.995 |

## Gold left at death

Unspent gold is banked value you never converted into board strength.

| Bucket | n | Avg place |
|---|---|---|
| 0-4 | 105 | 4.705 |
| 5-9 | 23 | 3.826 |
| 10-19 | 18 | 4.444 |
| 20-29 | 16 | 4.188 |
| 30+ | 38 | 5.421 |

## Final level

Levelling is the strongest lever on placement in most players' data.

| Bucket | n | Avg place |
|---|---|---|
| <=7 | 9 | 6.889 |
| 8 | 36 | 6.5 |
| 9 | 97 | 5.082 |
| 10 | 58 | 2.517 |

## Units holding 3 items

Completed items beat spread-thin items; this is usually a bigger lever than star levels.

| Bucket | n | Avg place |
|---|---|---|
| 0-1 | 12 | 6.25 |
| 2 | 43 | 5.977 |
| 3 | 64 | 5.062 |
| 4+ | 81 | 3.444 |

## Board size

Board size proxies both levelling and gold conversion.

| Bucket | n | Avg place |
|---|---|---|
| <=8 | 36 | 6.417 |
| 9 | 68 | 5.25 |
| 10 | 59 | 3.983 |
| 11+ | 37 | 3.027 |

## Elimination stage

Placement value per round is wildly non-linear — surviving one more stage is often worth several placements.

| Bucket | n | Avg place |
|---|---|---|
| 4-1–4-7 | 13 | 7.462 |
| 5-1–5-7 | 105 | 6.143 |
| 6-1–6-7 | 72 | 2.472 |
| 7-1–9-7 | 10 | 1.5 |

## Carries (min 4 games) — HEURISTIC, treat as soft

> Match history records a final board, not intent. "Carry" here is inferred as
> the unit holding the most items (tie-break: star level). A second independent
> pass over the same games produced a different ranking, so use these as hints
> about what to investigate, never as facts to quote.


| Carry | n | Avg place |
|---|---|---|
| Ivern Minion | 12 | 3.5 |
| Karma | 9 | 3.667 |
| Jax | 6 | 3.833 |
| Ornn | 12 | 3.833 |
| Samira | 7 | 3.857 |
| Maokai | 4 | 4.0 |
| Jhin | 8 | 4.125 |
| Nunu | 12 | 4.333 |
| Mordekaiser | 9 | 4.444 |
| Briar | 13 | 4.538 |
| Gnar | 5 | 4.6 |
| Rek Sai | 5 | 4.6 |
| Illaoi | 21 | 4.667 |
| Chogath | 5 | 4.8 |
| Rammus | 6 | 5.5 |
| Poppy | 5 | 5.6 |
| Corki | 4 | 6.25 |
| Fizz | 5 | 6.4 |
| Kaisa | 6 | 6.5 |
| Belveth | 4 | 6.75 |

## Strongest active trait (min 4 games)

| Trait | n | Avg place |
|---|---|---|
| Shield Tank | 7 | 1.857 |
| Stargazer Wolf | 8 | 3.375 |
| Stargazer Mountain | 4 | 3.5 |
| Flex Trait | 10 | 3.7 |
| Blitzcrank Unique Trait | 4 | 3.75 |
| Melee Trait | 4 | 3.75 |
| HPTank | 13 | 4.538 |
| Dark Star | 40 | 4.55 |
| Space Groove | 32 | 4.562 |
| ADMIN | 10 | 5.0 |
| Astronaut | 43 | 5.326 |
| Primordian | 6 | 5.667 |

## Read this as coaching triggers

- Lean toward: Ivern Minion (3.5), Karma (3.667), Jax (3.833)
- Avoid itemising: Fizz (6.4), Kaisa (6.5), Belveth (6.75)
- Baseline to beat: 4.675. Anything above it is a losing pattern for me specifically.
