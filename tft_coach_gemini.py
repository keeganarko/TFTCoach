#!/usr/bin/env python3
"""
TFT Coach Pro - Full featured AI overlay for Teamfight Tactics
Features:
  - Gemini 2.5 Flash-Lite vision analysis
  - F9 hotkey for on-demand analysis
  - Left monitor capture only
  - Session history (last 3 tips passed to API)
  - Sound alert on new tip
  - Color coded tips (economy/combat/items)
  - Live session cost tracker
  - Post-game lesson file generator
  - Personal notes/library loader
  - Rank-aware coaching

Requires: pip install pillow pyautogui google-genai keyboard screeninfo
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import io
import os
import random
import json
import datetime
import winsound
from google import genai
from google.genai import types

# ── Config ───────────────────────────────────────────────────────────────────
API_KEY        = os.environ.get("GEMINI_API_KEY", "")
MODEL          = "gemini-2.5-flash-lite"
INTERVAL_MIN   = 30
INTERVAL_MAX   = 60
PLAYER_RANK    = "Gold"           # Change to your rank: Iron/Bronze/Silver/Gold/Plat/Diamond/Master/GM/Challenger
NOTES_DIR      = r"C:\Coach\notes"   # Where lesson files are saved and loaded from
HOTKEY         = "f9"             # Press this for instant analysis

# Token cost estimates (Gemini 2.5 Flash-Lite)
COST_PER_INPUT_TOKEN  = 0.10 / 1_000_000
COST_PER_OUTPUT_TOKEN = 0.40 / 1_000_000
AVG_INPUT_TOKENS      = 700
AVG_OUTPUT_TOKENS     = 150

# ── Load personal notes from library ─────────────────────────────────────────
def load_notes() -> str:
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
        return ""
    notes = []
    for fname in sorted(os.listdir(NOTES_DIR)):
        if fname.endswith(".txt"):
            try:
                with open(os.path.join(NOTES_DIR, fname), "r", encoding="utf-8") as f:
                    notes.append(f"--- {fname} ---\n{f.read()}")
            except Exception:
                pass
    return "\n\n".join(notes)

# ── Screenshot helper ─────────────────────────────────────────────────────────
def capture_left_monitor() -> bytes:
    """Capture only the leftmost monitor."""
    try:
        from screeninfo import get_monitors
        monitors = sorted(get_monitors(), key=lambda m: m.x)
        m = monitors[0]  # leftmost monitor
        import pyautogui
        screenshot = pyautogui.screenshot(region=(m.x, m.y, m.width, m.height))
    except Exception:
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
        except Exception:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()

    w, h = screenshot.size
    if w > 1280:
        ratio = 1280 / w
        screenshot = screenshot.resize((1280, int(h * ratio)))

    buf = io.BytesIO()
    screenshot.save(buf, format="JPEG", quality=75)
    return buf.getvalue()

# ── Build prompt ──────────────────────────────────────────────────────────────
def build_prompt(history: list[str], personal_notes: str) -> str:
    base = f"""You are an expert TFT (Teamfight Tactics) Set 17 coach watching a {PLAYER_RANK} player's screen in real time.
Analyze the screenshot and give SHORT, punchy, actionable suggestions based on what you see AND the meta knowledge below.

== PATCH 17.2/17.3 META (Set 17) ==

COMP TIER LIST (TFTAcademy, Patch 17.3):
S tier: Dark Star, Graves/Vex Fast 9, Corki/Riven (rising)
A tier: Vanguard/Aurelion Sol flex, Yi Brawlers (falling), Fountain Lulu, Dark Star Lissandra (rising)
B tier: Karma/LB duo (rising), Voyager Crab, Fast 9 Jhin Stargazer, Kai'Sa Karma, Veigar Printer, Samira Knockup, Karnami flex (rising), Anima Reroll (rising)
C tier: Ez/Cho, TF Reroll (falling), Vanguard Teemo (falling), Primordian Reroll (falling — Heart of Swarm disabled), Conduit MF Reroll, Vanguard Zoe
Situational: Invader Zed (S), Shieldmaiden Leona (A, nerfed), Meepsie (A), Self-Destruct (A)

KEY PATCH CHANGES:
- Briar, Leona, Jax all nerfed — don't over-invest
- Timebreaker nerfed early (less XP/rerolls stages 2-3)
- Heart of the Swarm disabled — avoid Primordian
- New encounters: Double Duplicators, Artifact Anvil, Reroll Start, Cheaper Levels, Stage 3 Augments
- God Armory reduced (12→10 gold) at 4-7
- Early loot slightly reduced — fewer components in stages 1-3

== ECONOMY FUNDAMENTALS ==
- Interest breakpoints: 10/20/30/40/50g = 1/2/3/4/5 interest per round
- GREEDY: Save to 50g, level/roll only when needed — best for Fast 8/9
- AGGRESSIVE: Spend for tempo/win streak, roll at 3-2 or 4-1 for reroll comps
- BALANCED: Hit interest breakpoints, level at standard timings, flex into shop

== LEVELING TIMINGS ==
- Standard: Lvl5 on 2-1, Lvl6 on 3-2, Lvl7 on 4-1, Lvl8 on 4-5 or 5-1
- Fast 8/9: Save hard through stage 3, hit Lvl8 on 4-2, Lvl9 with leftover gold
- Reroll: Stay Lvl6-7, roll hard at 3-2 or 4-1 to 3-star key units, stop once hit
- Slow Roll: Stay Lvl5-6, only spend gold above 50g for 1-2 cost 3-stars

== ITEM PRIORITIES ==
- Carry: Rabadon's Deathcap, Jeweled Gauntlet, Blue Buff (mages), Infinity Edge, Giant Slayer, Guinsoo's
- Tank: Warmog's, Dragon's Claw, Gargoyle Stoneplate, Bramble Vest
- Flex: Hand of Justice, Quicksilver, Titan's Resolve
- Best components: Tear (Blue Buff/JG), BF Sword (IE/GS), Rod (Rabadon's/JG)

== STAGE-SPECIFIC FOCUS ==
- Stage 1-2: Focus on win/loss streak, build economy, don't overspend
- Stage 3: Decide your comp, hit interest breakpoints, scout lobbies
- Stage 3-2: Key decision point — roll for reroll comps OR save for fast 8
- Stage 4: Stabilize board, start leveling to 7/8, itemize carry
- Stage 5+: Push levels aggressively, contest 5-costs, finalize board
"""

    if personal_notes.strip():
        base += f"\n== PLAYER'S PERSONAL NOTES & LESSONS ==\n{personal_notes}\n"

    if history:
        base += "\n== RECENT TIPS ALREADY GIVEN (don't repeat these) ==\n"
        for i, tip in enumerate(history[-3:], 1):
            base += f"Tip {i}: {tip[:200]}\n"

    base += """
== OUTPUT FORMAT ==
Categorize each bullet with a prefix so I can color code it:
[ECON] for economy/gold/leveling tips
[ITEM] for item building tips
[BOARD] for positioning/comp/synergy tips
[COMBAT] for fight/streak/positioning tips

Max 4 bullets. Be direct. Reference what you actually see (gold, level, stage, items, units).
If you can't clearly see a TFT game: "Can't see your board — bring TFT into focus!"
"""
    return base

# ── Gemini API call ───────────────────────────────────────────────────────────
def get_tft_suggestion(client, history: list[str], personal_notes: str) -> str:
    try:
        img_bytes = capture_left_monitor()
        prompt    = build_prompt(history, personal_notes)
        response  = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                types.Part.from_text(text=prompt)
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ── Post-game lesson generator ────────────────────────────────────────────────
def generate_lesson_file(client, session_tips: list[str], personal_notes: str) -> str:
    """Ask Gemini to reflect on the session and produce lesson notes."""
    if not session_tips:
        return ""
    try:
        tips_text = "\n".join(f"- {t[:300]}" for t in session_tips)
        prompt = f"""You are a TFT coach reviewing a coaching session. Here are all the tips given to a {PLAYER_RANK} player this game:

{tips_text}

Write a SHORT post-game lesson file (max 300 words) covering:
1. KEY LESSONS: What were the most important strategic patterns this game?
2. GOOD CALLS: Advice that was likely correct and why
3. AREAS TO IMPROVE: Things the player should focus on next game
4. THINGS TO REMEMBER: Specific TFT mechanics or decisions worth noting for future games

Write it as plain text, no markdown, concise and useful as a personal reference note."""

        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Part.from_text(text=prompt)]
        )
        return response.text
    except Exception as e:
        return f"Could not generate lesson: {e}"

# ── Color tag parser ──────────────────────────────────────────────────────────
TAG_COLORS = {
    "[ECON]":   "#4ade80",   # green
    "[ITEM]":   "#c89b3c",   # gold
    "[BOARD]":  "#60a5fa",   # blue
    "[COMBAT]": "#f87171",   # red
}

# ── Overlay UI ────────────────────────────────────────────────────────────────
class TFTOverlay:
    def __init__(self, root: tk.Tk):
        self.root          = root
        self.running       = False
        self.client        = None
        self.session_tips  = []
        self.total_cost    = 0.0
        self.call_count    = 0
        self.personal_notes = load_notes()
        self._dx           = 0
        self._dy           = 0

        self.root.title("TFT Coach Pro 🎯")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.93)
        self.root.geometry("400x340+20+20")
        self.root.configure(bg="#0a0a14")
        self.root.resizable(True, True)

        self._build_ui()
        self._make_draggable()
        self._setup_hotkey()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#12122a", pady=5)
        header.pack(fill="x")

        tk.Label(
            header, text="⚔️  TFT COACH PRO  •  17.3",
            font=("Courier", 11, "bold"), fg="#c89b3c", bg="#12122a"
        ).pack(side="left", padx=10)

        self.status_dot = tk.Label(
            header, text="●", font=("Courier", 14), fg="#444", bg="#12122a"
        )
        self.status_dot.pack(side="right", padx=10)

        # Cost bar
        self.cost_label = tk.Label(
            self.root, text="Session: $0.0000  |  0 calls  |  F9 = instant tip",
            font=("Courier", 8), fg="#444", bg="#0a0a14"
        )
        self.cost_label.pack(fill="x", padx=10)

        # Text area with color tags
        self.text_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, font=("Courier", 10),
            bg="#0d0d1f", fg="#e2d8c0", insertbackground="#c89b3c",
            relief="flat", bd=0, padx=10, pady=8,
            state="disabled", height=12
        )
        self.text_box.pack(fill="both", expand=True, padx=4, pady=2)

        # Configure color tags
        for tag, color in TAG_COLORS.items():
            self.text_box.tag_configure(tag, foreground=color)

        # Controls
        controls = tk.Frame(self.root, bg="#0a0a14", pady=5)
        controls.pack(fill="x")

        self.toggle_btn = tk.Button(
            controls, text="▶  START",
            font=("Courier", 10, "bold"),
            bg="#1a3a1a", fg="#4ade80", activebackground="#2a5a2a",
            relief="flat", bd=0, padx=12, pady=4,
            command=self.toggle
        )
        self.toggle_btn.pack(side="left", padx=8)

        tk.Button(
            controls, text="📋 END GAME",
            font=("Courier", 9),
            bg="#1a1a3a", fg="#60a5fa", activebackground="#2a2a5a",
            relief="flat", bd=0, padx=8, pady=4,
            command=self.end_game
        ).pack(side="left", padx=4)

        self.next_label = tk.Label(
            controls, text="", font=("Courier", 9), fg="#555", bg="#0a0a14"
        )
        self.next_label.pack(side="left", padx=4)

        tk.Button(
            controls, text="✕", font=("Courier", 10),
            bg="#0a0a14", fg="#555", activebackground="#1a0a0a",
            relief="flat", bd=0, padx=8, command=self._quit
        ).pack(side="right", padx=8)

        notes_count = len([f for f in os.listdir(NOTES_DIR) if f.endswith(".txt")]) if os.path.exists(NOTES_DIR) else 0
        self._set_text(
            f"Click ▶ START to begin coaching.\n\n"
            f"Patch 17.3 meta loaded ✓\n"
            f"Personal notes loaded: {notes_count} file(s) ✓\n"
            f"Rank: {PLAYER_RANK}\n"
            f"Hotkey: F9 for instant tip\n"
            f"Notes saved to: {NOTES_DIR}"
        )

    def _setup_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey(HOTKEY, self._hotkey_trigger)
        except Exception:
            pass

    def _hotkey_trigger(self):
        if self.running:
            self.root.after(0, lambda: self._set_text("🎯 F9 triggered — analyzing now..."))
            threading.Thread(target=self._single_analysis, daemon=True).start()

    def _make_draggable(self):
        self.root.bind("<Button-1>", self._drag_start)
        self.root.bind("<B1-Motion>", self._drag_move)

    def _drag_start(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{x}+{y}")

    def _set_text(self, msg: str):
        self.text_box.config(state="normal")
        self.text_box.delete("1.0", tk.END)

        # Insert with color tags
        for line in msg.split("\n"):
            tagged = False
            for tag, color in TAG_COLORS.items():
                if line.startswith(tag):
                    self.text_box.insert(tk.END, line + "\n", tag)
                    tagged = True
                    break
            if not tagged:
                self.text_box.insert(tk.END, line + "\n")

        self.text_box.config(state="disabled")

    def _update_cost(self):
        self.call_count += 1
        cost = (AVG_INPUT_TOKENS * COST_PER_INPUT_TOKEN) + (AVG_OUTPUT_TOKENS * COST_PER_OUTPUT_TOKEN)
        self.total_cost += cost
        self.root.after(0, lambda: self.cost_label.config(
            text=f"Session: ${self.total_cost:.4f}  |  {self.call_count} calls  |  F9 = instant tip",
            fg="#4ade80" if self.total_cost < 0.10 else "#c89b3c"
        ))

    def _set_status(self, active: bool):
        self.status_dot.config(fg="#4ade80" if active else "#444")

    def _play_alert(self):
        try:
            winsound.Beep(880, 120)
        except Exception:
            pass

    def toggle(self):
        if self.running:
            self.running = False
            self.toggle_btn.config(text="▶  START", fg="#4ade80", bg="#1a3a1a")
            self.next_label.config(text="")
            self._set_status(False)
        else:
            if not API_KEY:
                self._set_text(
                    "❌ No Gemini API key!\n\n"
                    "$env:GEMINI_API_KEY = \"your_key_here\"\n\n"
                    "Then restart the script."
                )
                return
            self.client        = genai.Client(api_key=API_KEY)
            self.personal_notes = load_notes()
            self.running       = True
            self.session_tips  = []
            self.total_cost    = 0.0
            self.call_count    = 0
            self.toggle_btn.config(text="⏹  STOP", fg="#f87171", bg="#3a1a1a")
            self._set_status(True)
            threading.Thread(target=self._coaching_loop, daemon=True).start()

    def _single_analysis(self):
        """One-off analysis for hotkey trigger."""
        suggestion = get_tft_suggestion(self.client, self.session_tips, self.personal_notes)
        self.session_tips.append(suggestion)
        self._update_cost()
        self._play_alert()
        if self.running:
            self.root.after(0, lambda s=suggestion: self._set_text(s))

    def _coaching_loop(self):
        while self.running:
            self.root.after(0, lambda: self._set_text("🔍 Analyzing your board..."))
            suggestion = get_tft_suggestion(self.client, self.session_tips, self.personal_notes)
            self.session_tips.append(suggestion)
            self._update_cost()
            self._play_alert()

            if self.running:
                self.root.after(0, lambda s=suggestion: self._set_text(s))

            wait = random.randint(INTERVAL_MIN, INTERVAL_MAX)
            for remaining in range(wait, 0, -1):
                if not self.running:
                    break
                self.root.after(0, lambda r=remaining: self.next_label.config(text=f"next in {r}s"))
                time.sleep(1)

        self.root.after(0, lambda: self.next_label.config(text=""))

    def end_game(self):
        """Generate and save a post-game lesson file."""
        if not self.session_tips:
            self._set_text("No tips recorded this session yet!")
            return
        if not self.client:
            self._set_text("Start a session first before ending the game.")
            return

        self._set_text("📋 Generating post-game lessons...")

        def generate():
            lesson = generate_lesson_file(self.client, self.session_tips, self.personal_notes)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            fname = f"session_{timestamp}.txt"
            fpath = os.path.join(NOTES_DIR, fname)

            try:
                os.makedirs(NOTES_DIR, exist_ok=True)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(f"TFT Coach Session — {timestamp}\n")
                    f.write(f"Rank: {PLAYER_RANK} | Calls: {self.call_count} | Cost: ${self.total_cost:.4f}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(lesson)
                saved = f"✅ Lessons saved to:\n{fpath}\n\nThis file will be loaded automatically next session.\n\n{lesson[:400]}..."
            except Exception as e:
                saved = f"❌ Could not save: {e}\n\n{lesson}"

            self.root.after(0, lambda: self._set_text(saved))

        threading.Thread(target=generate, daemon=True).start()

    def _quit(self):
        self.running = False
        self.root.quit()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not API_KEY:
        print("\n⚠️  GEMINI_API_KEY not set!")
        print('Run: $env:GEMINI_API_KEY = "your_key_here"\n')

    root = tk.Tk()
    TFTOverlay(root)
    root.mainloop()
