# Windows desktop setup — 3 displays (game + Xeneon dashboard)

The desktop is the primary rig: League on your main monitor, the coach
dashboard filling the Xeneon, nothing covering the game.

## One-time setup (~10 min)

1. `git clone https://github.com/keeganarko/TFTCoach.git` and open the folder.
2. Install Python 3.12+ from python.org — in the installer tick **tcl/tk** and
   **py launcher**.
3. Run **`setup_windows.bat`** — creates the venv, installs deps, prints the rest:
   - `winget install UB-Mannheim.TesseractOCR` (add to PATH)
   - `npm install -g @anthropic-ai/claude-code`, then `claude` once to log in
4. `coach.bat refresh` — pulls current-patch comps/stats/playbook.
5. Rebuild the local caches once: `.venv\Scripts\python.exe -m tftcoach.entities`
6. Regenerate the player profile any time: `.venv\Scripts\python.exe -m tftcoach.player_profile`

## Calibrate (once per machine/resolution)

League **Borderless**, pinned **1920×1080**, on your MAIN monitor. In any
planning phase:

```
.venv\Scripts\python.exe -m tftcoach.calibrate --auto
```

Glance at the crops it prints, fix any bad region with `--only <name>`.
`coach.bat --check` must end **"All green — structured extraction active."**

## Multi-monitor rules

- **HUD**: `coach.bat` auto-fills the largest non-primary display (the Xeneon)
  in dashboard mode — big type, full buttons. Force the tiny overlay instead
  with `coach.bat --primary`.
- **Capture**: reads the game monitor. If League is NOT on the primary display,
  set the monitor index before launching (mss numbering, 1 = primary):
  `set TFTCOACH_MONITOR=2` then `coach.bat`.
- Auto start/stop watches for `League of Legends.exe` (the game, not the
  lobby client) — no button pressing; only END is manual.

## Known Windows differences

- Sound: system beep instead of Glass.aiff.
- Global hotkeys: optional; skipped unless the `keyboard` package is installed.
- The Mac's Tk/Spaces problems don't exist here — python.org ships modern Tk.

## Gotchas

- Calibration is per-machine: the Mac's `regions.json` is gitignored and would
  be wrong here anyway. Calibrate fresh.
- **Aug 26 (Set 18)**: recalibrate + `coach.bat refresh` + rerun
  `tftcoach.entities` / `tftcoach.reference` — see docs/SET18_ROLLOVER.md.
- League must be Borderless (not exclusive Fullscreen) for smooth alt-free play.
