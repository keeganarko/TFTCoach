# The Obsidian Lessons-Learned Brain

Design for the self-improving memory layer in `vault/`. The vault ships in this repo so it's
versioned; point Obsidian at it directly (Open folder as vault) or move it into an existing
vault and update the coach's `VAULT_PATH`.

## The core idea

v1 appended flat `.txt` lessons and dumped all of them into every prompt. That *accumulates*
but doesn't *compound*: no deduplication, no promotion, no expiry, no ground truth. The vault
replaces it with a knowledge lifecycle:

```
per-game raw notes  ──distill──▶  candidate lessons  ──evidence──▶  confirmed
   (Games/)                          (Lessons/)                        │
      ▲                                                     promote／retire
      │ auto-written from                                          ▼
      │ screenshot timeline                            Principles (in TFT-Brain.md,
      │ + Riot match result                            hard cap ~10, in every prompt)
```

- **Games/** — one note per match, machine-written: the in-game analysis timeline plus the
  post-game Riot match result (placement, final board, augments, opponents). Raw material.
- **Lessons/** — atomic, testable claims with frontmatter (`status`, `category`, `scope`,
  `evidence`, `counter_evidence`). Status lifecycle: `candidate` → `confirmed` (3+ supporting
  games or authoritative-guide confirmation) → `principle` or `retired`.
- **TFT-Brain.md** — the index. Active principles inline (capped ~10), player profile,
  standing instructions. This is the only file guaranteed into every coaching prompt.
- **Comps/** — set-bound playbooks mixing fetched meta with personal per-comp history.
- **Meta/** — machine-written current-patch snapshots (tier list, augment/item stats).
  Never hand-edited; the coach refuses stale snapshots. Kills the v1 stale-meta failure mode.

## The three passes that make it self-improving

1. **Post-game reflection** (after every match, ~1 min): pull the Riot match result, write the
   game note, audit the coach's own advice against the actual outcome, propose/increment
   candidate lessons. Crucially this grades both the *player* and the *coach* — v1 could only
   grade itself against itself.
2. **Consolidation** (weekly or every ~10 games): merge duplicate lessons, apply promotion/
   retirement rules, update the player profile ("positioning mistakes down from 3/5 games to
   1/5"), rotate the principle list. This is what turns accumulation into compounding.
3. **Set rotation** (every ~4 months): archive Comps/ and patch-bound lessons wholesale,
   carry evergreen principles forward, reseed Meta/ for the new set.

## Why frontmatter everywhere

Every note carries YAML properties (`placement`, `comp`, `patch`, `status`, `category`...).
That makes the vault queryable three ways at once: by Claude (structured retrieval — "load
confirmed positioning lessons + the playbook for the comp I'm pivoting to"), by Obsidian
Dataview/Bases ("avg placement by comp this patch" dashboards you can browse yourself), and
by scripts (staleness checks, evidence counting) without parsing prose.

## Selective loading, not kitchen-sink prompts

Per coaching call, the context is: TFT-Brain.md + current Meta snapshot + the live game
timeline + *only the lessons relevant to the current decision* (matched by category and by
the comp being played). Post-game and consolidation passes get wider context. Token cost
stays flat as the vault grows — v1's prompt grew linearly with games played.

## How Claude accesses it

Plain filesystem read/write of markdown is the baseline and is fully sufficient — Obsidian
picks up external file changes live, and links/frontmatter are just text. An Obsidian MCP
server (e.g. via the Local REST API plugin) is an optional upgrade for search-in-vault; see
REVAMP_OPTIONS.md for the integration matrix after research findings.
