# TFT Coach v2 — Revamp Options (researched & verified 2026-08-10)

Fourteen research/verification agents checked every load-bearing claim against primary
sources on 2026-08-10. Facts below are current as of that date.

## The landscape (what changed since v1 was written)

- **The game:** live set is Set 17 "Space Gods", patch **17.8** — v1's hardcoded 17.3 meta is
  5 balance patches stale. **Set 18 "Enchanted Wilds" launches Aug 26, 2026 (patch 18.1) and
  moves TFT to Unreal Engine** — on-screen rendering changes (breaks any pixel/OCR pipeline
  calibrated on the old client), the meta fully resets, and a standalone TFT client follows
  Oct 9, 2026. **Build v2 for Set 18, don't tune it for Set 17's last two weeks.**
- **Static data:** `https://raw.communitydragon.org/latest/cdragon/tft/en_us.json` (verified
  live, 25.9 MB) is the canonical source — full champion stats/abilities, 44 traits with
  breakpoints, all items/augments. League Data Dragon is shallow and may freeze for TFT after
  the Unreal migration. Staleness detection: poll version endpoints daily; `TFT17_→TFT18_`
  apiName prefix change = set rollover → full resync + prompt rebuild.
- **Riot API:** `tft-match-v1` gives end-of-game truth — placement, all 8 players' final
  boards, gold left, damage — free, no vision needed. **No augments** (withheld from the API
  since Nov 2024). No per-round data, no live board state from any Riot surface. Dev key is
  instant (20 req/s, expires daily); a personal product key removes expiry. LCU
  `gameflow-phase` (unofficial but reliable) detects game start/end locally.
- **Live state:** three tiers. (1) **Overwolf GEP** — full structured live state (gold, HP,
  shop, board, opponent boards while scouting, augments); it's what MetaTFT/TFTactics use,
  but personal-app whitelisting requires an app-proposal process oriented toward
  store-distributed apps. (2) **Fixed-region OCR + template matching** pinned to 1920×1080
  borderless (reference: jfd02/TFT-OCR-BOT's coordinate map; sub-second, $0, local).
  (3) **Vision LLM** — weakest for exact state (models hallucinate shop contents even with
  clean input); demote to cropped-region gap-filling and scouting summaries, always validated
  against the CommunityDragon entity list.
- **Riot policy (know this):** the developer policy prohibits in-game tools that provide
  real-time performance-improving data or opponent tracking. Post-game/pre-game coaching is
  policy-clean. A private, personal live coach via screen capture is undetectable by Vanguard
  (screen capture is explicitly fine; memory reading/input automation are the ban category)
  but does violate the third-party policy — your call, made explicitly, not by accident.
- **Claude:** the Agent SDK does **not** take subscription auth (API key only). **Headless
  Claude Code (`claude -p`) does** — auth via `claude setup-token`, images by file path in the
  prompt, `--resume` to keep game context across calls, `--output-format json` for structured
  replies. Programmatic subscription use is currently permitted (the planned June 2026
  split-billing change is paused — re-verify if this becomes load-bearing). Model split:
  Haiku 4.5 for fast vision gap-filling (~1–3 s), your strongest model (Opus/Fable tier) for
  strategy and post-game reflection.
- **Obsidian:** plain filesystem writes are safe with Obsidian open (it re-indexes external
  changes) — no plugin needed. Keep all machine metadata in YAML frontmatter so the core
  Bases plugin gives free dashboards (avg placement by comp, leak trends). Optional later:
  Local REST API plugin (v4+ ships a built-in MCP server) for search/patch operations.

## Option A — Policy-clean coach (pre-game brief + post-game analysis, no live layer)

Pre-game: Claude briefs you from the vault + current meta snapshot ("your top 3 leaks, what's
strong this patch, comps to look for from your openers"). During: nothing. Post-game: LCU
detects game end → pull `tft-match-v1` (your placement + all 8 final boards) → write the game
note → reflection updates lessons.

- **Pros:** zero policy risk, zero capture engineering, survives the Unreal migration
  untouched, already 70% of the self-improvement value (ground truth + compounding brain).
- **Cons:** no in-game advice — drops your core ask.
- **Cost/effort:** ~2–3 sessions to build. Effectively free to run.

## Option B — Hybrid: local structured extraction + Claude brain (RECOMMENDED)

Everything in A, plus a live layer that separates perception from strategy:

1. **Capture agent** (Python, on the gaming PC): screenshots at 1920×1080 borderless →
   fixed-region OCR (tesserocr) + OpenCV template matching for gold/level/stage/HP/shop/
   board/bench, validated against the CommunityDragon entity whitelist. Sub-second, free,
   fully local. Regions live in a config file so Set 18's Unreal UI is a recalibration,
   not a rewrite. Vision-LLM (Haiku) only for what OCR can't read: augment choice screens,
   scouted opponent boards — cropped images, JSON-schema output.
2. **Game timeline**: each tick appends structured state to a per-game JSONL — the coach
   always reasons over the whole game so far plus the delta, never a single amnesiac frame.
3. **Strategy calls**: headless `claude -p --resume` on your subscription. Context = state
   timeline + current Meta snapshot + TFT-Brain principles + relevant lessons/comp playbook.
   Output = ≤4 prioritized, state-referenced directives, rendered in the overlay (keep v1's
   color coding + hotkey).
4. **Cadence — event-driven, not every-X-seconds**: trigger on planning-phase start, augment
   offer, carousel, and post-scout, plus hotkey. That's one strategy call per ~35–45 s of
   game time, each landing within the first ~5–8 s of a ~30 s planning phase. A fixed timer
   either wastes calls mid-combat or misses decision windows; verify remaining subscription
   headroom rather than tuning an interval.

- **Pros:** real-time advice grounded in exact state; cheap loop (local extraction, one
  model call per round); your strongest model does strategy; degrades gracefully to Option A.
- **Cons:** OCR calibration work (redo once at Set 18 launch); Windows-side agent to
  maintain; live layer technically violates Riot's third-party policy (private use,
  screen-capture only — enforcement risk low but nonzero, and it's your account).
- **Cost/effort:** A + ~4–6 sessions. Runs on subscription + $0 extraction.

## Option C — Max fidelity: Overwolf GEP feed

Replace Option B's OCR with a minimal Overwolf app subscribing to the TFT Game Events
Provider, relaying structured JSON (including scouted opponent boards and augments) to the
coach over localhost.

- **Pros:** perfect structured state with zero OCR; survives UI changes; the data channel
  the commercial tools use.
- **Cons:** Overwolf whitelisting expects a store-distributed app (proposal process — not a
  quick personal signup); adds the Overwolf runtime; the real-time-coaching policy question
  is unchanged. Worth revisiting if B's OCR maintenance grinds.

## Meta feed (all options)

Static data ≠ meta. Tier lists/comp stats need a separate pipeline: scheduled fetch from a
stats site (MetaTFT / TFTAcademy / tactics.tools) into `vault/Meta/` with `set`/`patch`/
`fetched` frontmatter `[!]` (exact endpoint/scrape target to be finalized — the meta-sources
research agent hadn't reported at synthesis time; manual paste-in works day one). The coach
refuses to advise on a stale snapshot. Note: augment win-rate data is specifically banned
from public display by Riot policy — fine in a private vault, never in anything distributed.

## Additional features worth building (rough priority)

1. **Advice audit loop** — post-game, grade the coach's own in-game calls against the actual
   result; feeds the consolidation pass. (This is what makes the *coach* self-improve, not
   just you.)
2. **Augment advisor** — capture the augment screen (API won't give augments), Haiku extracts
   the three options, strategy model picks with reasons; logged to the game note.
3. **Pre-game briefing card** — 30-second read: your active leaks, this patch's top lines,
   what to look for on your opener.
4. **Bases dashboards** — avg placement by comp/patch, leak recurrence trend, econ-curve vs
   placement correlation, all free from game-note frontmatter.
5. **Patch-day diff brief** — on version bump: what changed for *your* comps specifically.
6. **Scout summarizer** — hotkey while scouting: "who contests you, damage-type threats,
   where to corner your carry."
7. **TTS delivery** — speak the one highest-priority directive so you never alt-tab.
8. **Set 18 countdown mode** — until Aug 26: practice-oriented coaching ("experiment, learn
   Wisps early") rather than LP-optimizing a dying set.

## Recommendation

Build **Option A this week** (it's the foundation and pure win), layer **Option B's live loop**
targeting **Set 18 launch (Aug 26)** so OCR calibration happens once, on the Unreal client.
Decide the policy question explicitly before the live layer. Revisit C only if OCR upkeep
becomes a tax.
