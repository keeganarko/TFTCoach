---
type: meta-index
---

# Meta — machine-written patch snapshots

This folder is written by the meta-fetch pipeline, never by hand. On each patch (or daily),
the fetcher writes:

- `Current Patch.md` — set number/name, patch version, fetch timestamp. The coach refuses
  to run with a snapshot older than the live patch.
- `Comp Tier List.md` — current comp tiers with core units, items, and augment priorities.
- `Augment Stats.md` / `Item Stats.md` — top/bottom performers this patch.

Frontmatter on every file: `set`, `patch`, `fetched`, `source`. The coaching prompt loads
these instead of any hardcoded knowledge — the v1 failure mode (a May tier list giving
August advice) becomes structurally impossible.
