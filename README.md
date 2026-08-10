# TFT Coach

Personal project exploring AI coaching for Teamfight Tactics.

## v1 (current script)

`tft_coach_gemini.py` — Windows Tkinter overlay: screenshots the game every 30–60 s (F9 for
instant tips), sends them to Gemini 2.5 Flash-Lite with meta knowledge in the prompt, shows
color-coded suggestions, and writes post-game lesson files (`notes/`).

> ⚠️ v1's meta knowledge is hardcoded (Set 17 / patch 17.3, May 2026) and is now stale.
> See the v2 revamp before relying on it.

## v2 revamp (in design, 2026-08-10)

- **[docs/ANALYSIS.md](docs/ANALYSIS.md)** — honest audit of v1: what worked (the
  lesson loop, cadence UX) and what caps it (stale hardcoded meta, unstructured
  single-frame vision, no match ground truth).
- **[docs/REVAMP_OPTIONS.md](docs/REVAMP_OPTIONS.md)** — researched architecture options:
  policy-clean post-game coach (A), hybrid local-OCR + Claude brain (B, recommended),
  Overwolf GEP feed (C). Includes verified 2026-08-10 facts: Set 18 "Enchanted Wilds" +
  Unreal Engine launch Aug 26, Riot API surface, CommunityDragon data, headless Claude
  Code on subscription auth.
- **[docs/OBSIDIAN_BRAIN.md](docs/OBSIDIAN_BRAIN.md)** — the self-improving lessons brain.
- **[vault/](vault/)** — the Obsidian vault itself (open this folder as a vault):
  `TFT-Brain.md` index with active principles, per-game notes (May 2026 sessions
  migrated), lessons with a candidate → confirmed → principle lifecycle, machine-written
  meta snapshots.

## Setup (v1)

```
pip install pillow pyautogui google-genai keyboard screeninfo
set GEMINI_API_KEY, then run tft_coach_gemini.py
```

Secrets live in environment variables only — never in code.
