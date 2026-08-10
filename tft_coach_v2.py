#!/usr/bin/env python3
"""
TFT Coach v2 — Claude-powered coaching runtime (macOS + Windows)

What's new vs v1 (tft_coach_gemini.py):
  - Claude (your Pro/Max subscription via the Claude Code CLI) instead of Gemini API
  - One persistent Claude session per game (--resume): the coach remembers the whole
    game timeline, not just the last screenshot
  - Context comes from the Obsidian vault (vault/TFT-Brain.md principles + player
    profile, vault/Meta/Current Patch.md live meta) — nothing hardcoded
  - End Game writes a structured game note + lesson updates INTO the vault
  - No API keys: uses whatever `claude` is logged in as

Requires: the `claude` CLI on PATH (already logged in).
  macOS: no other deps (uses built-in `screencapture` + `sips`).
         Grant Terminal: System Settings > Privacy & Security > Screen Recording.
  Windows: pip install pillow
Optional both: Pillow for capture fallback.

Run from the repo root:  python3 tft_coach_v2.py
"""

import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import datetime

# ── Config ───────────────────────────────────────────────────────────────────
REPO_DIR      = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR     = os.path.join(REPO_DIR, "vault")
CAPTURE_DIR   = os.path.join(REPO_DIR, ".captures")   # gitignored
INTERVAL_SEC  = 45          # auto-tip cadence; planning phases are ~30s apart
MODEL         = None        # None = your Claude Code default; or "haiku"/"sonnet"/"opus"
MAX_WIDTH     = 2048        # downscale Retina screenshots (token control)
CLAUDE_TIMEOUT = 150        # seconds per Claude call

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# ── Vault context ────────────────────────────────────────────────────────────
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""

def load_context() -> str:
    brain = read_file(os.path.join(VAULT_DIR, "TFT-Brain.md"))
    meta  = read_file(os.path.join(VAULT_DIR, "Meta", "Current Patch.md"))
    ctx = ""
    if brain:
        ctx += f"== VAULT BRAIN (principles, player profile, standing instructions) ==\n{brain}\n\n"
    if meta:
        ctx += f"== CURRENT META SNAPSHOT ==\n{meta}\n\n"
    return ctx

def meta_warning() -> str:
    meta = read_file(os.path.join(VAULT_DIR, "Meta", "Current Patch.md"))
    if "PASTE CURRENT LIST HERE" in meta and "S tier" not in meta:
        return "⚠ Meta tier list is empty — paste one into vault/Meta/Current Patch.md"
    return ""

# ── Screenshot ───────────────────────────────────────────────────────────────
def capture() -> str:
    """Capture the screen, downscale, return file path."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%H-%M-%S")
    path = os.path.join(CAPTURE_DIR, f"cap_{ts}.jpg")
    if IS_MAC:
        # -x silent, -t jpg format; captures main display
        subprocess.run(["screencapture", "-x", "-t", "jpg", path], check=True)
        subprocess.run(["sips", "--resampleWidth", str(MAX_WIDTH), path],
                       capture_output=True)
    else:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img.width > MAX_WIDTH:
            img = img.resize((MAX_WIDTH, int(img.height * MAX_WIDTH / img.width)))
        img.convert("RGB").save(path, "JPEG", quality=85)
    return path

# ── Claude calls ─────────────────────────────────────────────────────────────
class ClaudeSession:
    """One persistent headless Claude Code session per game."""

    def __init__(self):
        self.session_id = None
        self.calls = 0

    def call(self, prompt: str, allow_write: bool = False) -> str:
        tools = "Read,Write,Edit,Glob" if allow_write else "Read"
        cmd = ["claude", "-p", prompt, "--output-format", "json",
               "--allowedTools", tools]
        if MODEL:
            cmd += ["--model", MODEL]
        if self.session_id:
            cmd += ["--resume", self.session_id]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=CLAUDE_TIMEOUT, cwd=REPO_DIR)
        except subprocess.TimeoutExpired:
            return "❌ Claude call timed out."
        except FileNotFoundError:
            return "❌ `claude` CLI not found on PATH. Install Claude Code first."
        if out.returncode != 0:
            return f"❌ Claude error: {(out.stderr or out.stdout).strip()[:400]}"
        try:
            data = json.loads(out.stdout)
            self.session_id = data.get("session_id", self.session_id)
            self.calls += 1
            return data.get("result", "").strip() or "❌ Empty response."
        except json.JSONDecodeError:
            return out.stdout.strip()[:1000]

def coach_prompt(img_path: str, first: bool, note: str = "") -> str:
    p = ""
    if first:
        p += ("You are my TFT (Teamfight Tactics) coach for one LIVE game. "
              "Coach with the context below for the whole session; I'll send a "
              "screenshot each round. Maintain a running game timeline internally "
              "and reason over trends (HP bleed, econ curve, spikes), not single frames.\n\n"
              + load_context())
    p += f"Read the screenshot at {img_path} — this is my screen right now.\n"
    if note:
        p += f"My note: {note}\n"
    p += ("Extract only what you can actually see (stage-round, gold, level, HP, shop, "
          "board, augments); never guess unreadable values. Then give me MAX 4 bullets, "
          "most urgent first, each prefixed [ECON] [ITEM] [BOARD] or [COMBAT], each "
          "referencing observed state, one short line each, no preamble. "
          "If the screen isn't a TFT game, say so in one line.")
    return p

def postgame_prompt(result_note: str) -> str:
    today = datetime.date.today().isoformat()
    return (f"The game just ended. Result: {result_note}\n"
            f"Do the post-game pass on the Obsidian vault in {VAULT_DIR}:\n"
            f"1. Create 'vault/Games/{today} Game.md' (append ' 2', ' 3' to the name if it "
            "exists) following vault/Templates/Game Note.md: frontmatter (placement, comp, "
            "set+patch from vault/Meta/Current Patch.md, source: v2-live), a timeline "
            "summary from this session, and 'What decided this game' in 2-3 sentences.\n"
            "2. Advice audit: grade each tip you gave this session against the result.\n"
            "3. Lessons: for each observed mistake, if a matching note exists in "
            "vault/Lessons/ add this game to its frontmatter evidence list; if novel and "
            "testable, create a candidate lesson from vault/Templates/Lesson Note.md.\n"
            "4. Do NOT edit vault/TFT-Brain.md; if a lesson reached 3+ evidence links, "
            "mention it as a promotion candidate instead.\n"
            "5. Reply with: placement, the one thing to change next game, files written.")

# ── Overlay UI ───────────────────────────────────────────────────────────────
TAG_COLORS = {"[ECON]": "#4ade80", "[ITEM]": "#c89b3c",
              "[BOARD]": "#60a5fa", "[COMBAT]": "#f87171"}

def play_alert():
    try:
        if IS_MAC:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
        elif IS_WIN:
            import winsound
            winsound.Beep(880, 120)
    except Exception:
        pass

class CoachApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import scrolledtext
        self.tk = tk
        self.root = root
        self.session = ClaudeSession()
        self.running = False
        self.busy = False
        self.ui_queue = queue.Queue()

        root.title("TFT Coach v2 ⚔ Claude")
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.94)
        except Exception:
            pass
        root.geometry("420x360+20+20")
        root.configure(bg="#0a0a14")

        header = tk.Frame(root, bg="#12122a", pady=5); header.pack(fill="x")
        tk.Label(header, text="⚔  TFT COACH v2  •  Claude + Vault Brain",
                 font=("Courier", 11, "bold"), fg="#c89b3c", bg="#12122a"
                 ).pack(side="left", padx=10)
        self.dot = tk.Label(header, text="●", font=("Courier", 14), fg="#444",
                            bg="#12122a"); self.dot.pack(side="right", padx=10)

        self.status = tk.Label(root, text="", font=("Courier", 8), fg="#666",
                               bg="#0a0a14"); self.status.pack(fill="x", padx=10)

        self.text = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Courier", 11), bg="#0d0d1f", fg="#e2d8c0",
            relief="flat", bd=0, padx=10, pady=8, state="disabled", height=12)
        self.text.pack(fill="both", expand=True, padx=4, pady=2)
        for tag, color in TAG_COLORS.items():
            self.text.tag_configure(tag, foreground=color)

        bar = tk.Frame(root, bg="#0a0a14", pady=5); bar.pack(fill="x")
        self.btn = tk.Button(bar, text="▶ START", font=("Courier", 10, "bold"),
                             fg="#4ade80", command=self.toggle)
        self.btn.pack(side="left", padx=8)
        tk.Button(bar, text="⚡ TIP NOW", font=("Courier", 9),
                  command=self.tip_now).pack(side="left", padx=4)
        tk.Button(bar, text="📋 END GAME", font=("Courier", 9),
                  command=self.end_game).pack(side="left", padx=4)
        self.countdown = tk.Label(bar, text="", font=("Courier", 9), fg="#555",
                                  bg="#0a0a14"); self.countdown.pack(side="left", padx=4)
        tk.Button(bar, text="✕", command=root.quit).pack(side="right", padx=8)

        warn = meta_warning()
        self.set_text("Click ▶ START when your game begins.\n\n"
                      "Vault brain loaded from vault/TFT-Brain.md\n"
                      f"{warn or 'Meta snapshot loaded ✓'}\n\n"
                      "⚡ TIP NOW anytime · 📋 END GAME writes the vault game note.\n"
                      "First Claude call of a session is slower (loads context).")
        root.after(200, self.drain_queue)

    # ---- UI plumbing (worker threads never touch Tk directly) ----
    def drain_queue(self):
        try:
            while True:
                fn = self.ui_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(200, self.drain_queue)

    def ui(self, fn):
        self.ui_queue.put(fn)

    def set_text(self, msg):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        for line in msg.split("\n"):
            tag = next((t for t in TAG_COLORS if line.strip().startswith(t)), None)
            self.text.insert("end", line + "\n", tag)
        self.text.config(state="disabled")

    def set_status(self, msg=""):
        base = f"session: {self.session.session_id[:8] if self.session.session_id else '—'}" \
               f" | calls: {self.session.calls}"
        self.status.config(text=f"{base}  {msg}")

    # ---- actions ----
    def toggle(self):
        if self.running:
            self.running = False
            self.btn.config(text="▶ START", fg="#4ade80")
            self.dot.config(fg="#444")
        else:
            self.running = True
            self.btn.config(text="⏹ STOP", fg="#f87171")
            self.dot.config(fg="#4ade80")
            threading.Thread(target=self.loop, daemon=True).start()

    def analyze(self, note=""):
        if self.busy:
            return
        self.busy = True
        self.ui(lambda: (self.set_text("🔍 Capturing & analyzing..."), self.set_status()))
        try:
            img = capture()
            first = self.session.session_id is None
            result = self.session.call(coach_prompt(img, first, note))
        except Exception as e:
            result = f"❌ {e}"
        self.busy = False
        play_alert()
        self.ui(lambda r=result: (self.set_text(r), self.set_status()))

    def tip_now(self):
        threading.Thread(target=self.analyze, daemon=True).start()

    def loop(self):
        while self.running:
            self.analyze()
            for remaining in range(INTERVAL_SEC, 0, -1):
                if not self.running:
                    break
                self.ui(lambda r=remaining: self.countdown.config(text=f"next in {r}s"))
                time.sleep(1)
        self.ui(lambda: self.countdown.config(text=""))

    def end_game(self):
        from tkinter import simpledialog
        if self.session.session_id is None:
            self.set_text("No session yet — start coaching first.")
            return
        result = simpledialog.askstring(
            "End Game", "Result? (e.g. '3rd, star guardian jinx, greedy 4-1 roll')",
            parent=self.root)
        if not result:
            return
        self.running = False
        self.set_text("📋 Writing game note + updating lessons in the vault...")

        def run():
            out = self.session.call(postgame_prompt(result), allow_write=True)
            play_alert()
            self.ui(lambda: (self.set_text("✅ Post-game pass done:\n\n" + out),
                             self.set_status()))
        threading.Thread(target=run, daemon=True).start()

# ── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import tkinter as tk
    except ImportError:
        sys.exit("tkinter not available. On macOS: brew install python-tk "
                 "(or use python.org Python).")
    root = tk.Tk()
    CoachApp(root)
    root.mainloop()
