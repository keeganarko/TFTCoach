---
description: Post-game — write the game note, audit the coaching, update lessons
---

The game just ended. Arguments (placement, final comp/carry, anything notable): $ARGUMENTS

1. Write a new note in `vault/Games/` named `YYYY-MM-DD Game N.md` following
   `vault/Templates/Game Note.md`: frontmatter (placement, comp, set, patch from
   `vault/Meta/Current Patch.md`, source: manual-v2-test), the session's timeline summary,
   and "What decided this game" in 2-3 sentences.
2. AUDIT THE COACH: review every tip given this session against the actual result. Which
   were right, wrong, or unverifiable? Write this into the game note's Advice audit section.
3. LESSONS: for each mistake observed, check `vault/Lessons/` — if a matching lesson exists,
   add this game to its `evidence` list in frontmatter; if novel and testable, create a new
   candidate lesson from `vault/Templates/Lesson Note.md`.
4. If any lesson now has 3+ evidence links, propose (don't auto-apply) promoting it in
   `vault/TFT-Brain.md` — show me the diff and ask.
5. End with a 3-line summary: placement, the one thing to do differently next game, and
   any lesson changes made.
