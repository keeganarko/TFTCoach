#!/usr/bin/env python3
"""TFT Coach — Option B entry point: overlay + pipeline orchestrator.

Pipeline per event:
    TriggerEngine fires -> capture frame -> ocr.extract_state -> (optional)
    coach.vision_fill for board/bench crops -> timeline.append -> coach prompt
    -> Claude (headless CLI) -> colored bullets -> timeline.append_advice

Design rules this file obeys (see README / docs/OPTION_B_SETUP.md):
  * No pixel coordinates here. Everything comes from config.Regions.
  * Degrades gracefully. Missing OCR / uncalibrated regions / missing sibling
    modules => FULL-FRAME FALLBACK (whole screenshot -> vision), i.e. exactly
    v2 behaviour. The app always starts.
  * Unknown is first class. Nothing here invents a number.
  * Worker threads NEVER touch Tk. All UI mutation goes through self.ui().
  * Python 3.9 compatible: no match, no "X | Y" runtime unions.

MODULE CONTRACT expected from the rest of the package (all optional at import
time — anything missing degrades instead of crashing):

  tftcoach.capture
      is_available() -> (bool, str)
      capture_screen(path=None) -> str            # full-res frame path
      capture_regions(frame_path, rects) -> Dict[str, str]   # key -> crop path
      screen_size() -> (int, int)
  tftcoach.ocr
      is_available() -> (bool, str)
      extract_state(frame_path, rects) -> GameState
  tftcoach.entities
      is_available() -> (bool, str)
  tftcoach.coach
      ClaudeSession  (.call(prompt, allow_write=False, model=None) -> str,
                      .session_id, .calls)
      vision_fill(state, crops, session) -> GameState
      coach_prompt(state, timeline, first, note) -> str
      fullframe_prompt(image_path, first, note) -> str
      postgame_prompt(result_note) -> str
      FAST_MODEL / STRONG_MODEL (str or None)
  tftcoach.triggers
      TriggerEngine(regions=..., capture=...)      # kwargs are best-effort
          .poll() -> Optional[str]   # reason string when an event fires

Every one of those is resolved by name with a small alias list and called
best-effort, so a sibling module with a slightly different signature still
works. If a piece is absent, the built-in fallback in this file takes over.
"""

from __future__ import annotations

import datetime
import importlib
import inspect
import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tftcoach import config                      # noqa: E402  (path set above)
from tftcoach.state import GameState, Timeline   # noqa: E402

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# ── Models ───────────────────────────────────────────────────────────────────
# Two-model split protects subscription headroom:
#   FAST_MODEL     — perception only (board/bench crops -> names). Cheap, frequent.
#   AUTO_MODEL     — automatic per-round strategy tips. None = your Claude Code
#                    default, which is what you want most of the time.
#   STRONG_MODEL   — manual TIP NOW and the post-game vault pass. Deliberate,
#                    rare, worth the tokens.
FAST_MODEL_DEFAULT = "haiku"
AUTO_MODEL_DEFAULT = None
STRONG_MODEL_DEFAULT = "opus"

CLAUDE_TIMEOUT = 150      # seconds per Claude call
UI_TICK_MS = 200

MODE_OCR = "OCR"
MODE_FULLFRAME = "fallback"

TAG_COLORS = {"[ECON]": "#4ade80", "[ITEM]": "#c89b3c",
              "[BOARD]": "#60a5fa", "[COMBAT]": "#f87171"}
COL_BG = "#0a0a14"
COL_PANEL = "#12122a"
COL_TEXTBG = "#0d0d1f"
COL_FG = "#e2d8c0"
COL_OK = "#4ade80"
COL_BAD = "#f87171"
COL_WARN = "#c89b3c"
COL_DIM = "#666666"


# ── tiny helpers ─────────────────────────────────────────────────────────────
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def optional_import(name: str):
    """Import a sibling module, or None if it doesn't exist / can't load.

    A sibling that itself fails on a missing heavy dep must not take the app
    down — that is the whole point of the fallback path.
    """
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def pick(mod: Any, *names: str) -> Optional[Callable]:
    """First callable attribute on mod matching one of names."""
    if mod is None:
        return None
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    return None


def call_best_effort(fn: Callable, *args: Any) -> Any:
    """Call fn with as many of args as its signature accepts.

    Sibling modules are written by different hands; this tolerates
    extract_state(frame) vs extract_state(frame, rects) without a version
    negotiation protocol.
    """
    try:
        params = inspect.signature(fn).parameters.values()
        n = 0
        for p in params:
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
                n += 1
            elif p.kind == p.VAR_POSITIONAL:
                n = len(args)
                break
        return fn(*args[:min(n, len(args))])
    except (TypeError, ValueError):
        return fn(*args)


def availability(mod: Any, label: str) -> Tuple[bool, str]:
    fn = pick(mod, "is_available")
    if fn is None:
        return (False, "module %s not present" % label)
    try:
        res = fn()
    except Exception as exc:                       # a broken check is a red line
        return (False, "%s: %s" % (type(exc).__name__, exc))
    if isinstance(res, tuple) and len(res) == 2:
        return (bool(res[0]), str(res[1]))
    return (bool(res), "ok" if res else "unavailable")


def play_alert() -> None:
    try:
        if IS_MAC:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
        elif IS_WIN:
            import winsound
            winsound.Beep(880, 120)
    except Exception:
        pass


# ── vault context ────────────────────────────────────────────────────────────
def load_context() -> str:
    brain = read_file(os.path.join(config.VAULT_DIR, "TFT-Brain.md"))
    meta = read_file(os.path.join(config.VAULT_DIR, "Meta", "Current Patch.md"))
    out = ""
    if brain:
        out += ("== VAULT BRAIN (principles, player profile, standing instructions) ==\n"
                + brain + "\n\n")
    if meta:
        out += "== CURRENT META SNAPSHOT ==\n" + meta + "\n\n"
    return out


def meta_populated() -> Tuple[bool, str]:
    meta = read_file(os.path.join(config.VAULT_DIR, "Meta", "Current Patch.md"))
    if not meta:
        return (False, "vault/Meta/Current Patch.md missing")
    if "PASTE CURRENT LIST HERE" in meta and "S tier" not in meta:
        return (False, "tier list is an empty placeholder — paste one in")
    return (True, "meta snapshot loaded")


# ── capture (sibling module, or built-in fallback) ───────────────────────────
class CaptureAdapter:
    """Screen capture with a built-in path so the app runs with zero deps.

    Built-in: macOS `screencapture` (no pip deps), Pillow ImageGrab elsewhere.
    Full-frame grabs for OCR are NOT downscaled — OCR needs real pixels. The
    fallback-mode grab is downscaled for token control, like v2 did.
    """

    MAX_WIDTH_FALLBACK = 2048

    def __init__(self) -> None:
        self.mod = optional_import("tftcoach.capture")
        self._fn_screen = pick(self.mod, "capture_screen", "capture_full",
                               "grab_screen", "capture", "grab")
        self._fn_regions = pick(self.mod, "capture_regions", "crop_regions",
                                "capture_crops", "crop")
        self._fn_size = pick(self.mod, "screen_size", "screen_resolution",
                             "get_screen_size")

    # -- status ----------------------------------------------------------
    def is_available(self) -> Tuple[bool, str]:
        if self._fn_screen is not None:
            if pick(self.mod, "is_available") is not None:
                return availability(self.mod, "tftcoach.capture")
            return (True, "tftcoach.capture (no self-check)")
        if IS_MAC and shutil.which("screencapture"):
            return (True, "built-in: macOS screencapture")
        try:
            from PIL import ImageGrab  # noqa: F401
            return (True, "built-in: Pillow ImageGrab")
        except Exception:
            return (False, "no capture backend (pip install pillow)")

    # -- grabs -----------------------------------------------------------
    def full_frame(self, downscale: bool = False) -> str:
        config.ensure_dirs()
        stamp = datetime.datetime.now().strftime("%H-%M-%S")
        ext = "jpg" if downscale else "png"
        path = os.path.join(config.CAPTURE_DIR, "cap_%s.%s" % (stamp, ext))
        if self._fn_screen is not None:
            # capture_screen(monitor=None) -> PIL.Image. Call it with NO
            # arguments: its first parameter is the monitor INDEX, and passing
            # the output path positionally became int("/path/to/cap.png").
            try:
                img = self._fn_screen()
            except Exception:
                img = None
            if isinstance(img, str) and img and os.path.exists(img):
                return img                     # some backends save themselves
            if img is not None and hasattr(img, "save"):
                try:
                    if downscale and getattr(img, "width", 0) > self.MAX_WIDTH_FALLBACK:
                        h = int(img.height * self.MAX_WIDTH_FALLBACK / img.width)
                        img = img.resize((self.MAX_WIDTH_FALLBACK, h))
                    if path.endswith(".png"):
                        img.save(path)
                    else:
                        img.convert("RGB").save(path, "JPEG", quality=88)
                    return path
                except Exception:
                    pass                       # fall through to the builtin
        return self._builtin_frame(path, downscale)

    def _builtin_frame(self, path: str, downscale: bool) -> str:
        if IS_MAC:
            fmt = "jpg" if downscale else "png"
            subprocess.run(["screencapture", "-x", "-t", fmt, path], check=True)
            if downscale:
                subprocess.run(["sips", "--resampleWidth",
                                str(self.MAX_WIDTH_FALLBACK), path],
                               capture_output=True)
            return path
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if downscale and img.width > self.MAX_WIDTH_FALLBACK:
            h = int(img.height * self.MAX_WIDTH_FALLBACK / img.width)
            img = img.resize((self.MAX_WIDTH_FALLBACK, h))
        if path.endswith(".png"):
            img.save(path)
        else:
            img.convert("RGB").save(path, "JPEG", quality=88)
        return path

    def crops(self, frame_path: str, rects: Dict[str, List[int]]) -> Dict[str, str]:
        """Crop the given rects out of an existing frame. Returns key -> path.

        Always crops from THIS frame via PIL. capture.capture_regions grabs the
        live screen instead, which by vision-call time may show combat — the
        crops must match the frame the rest of the state was extracted from.
        """
        if not rects:
            return {}
        try:
            from PIL import Image
        except Exception:
            return {}                      # no Pillow -> vision fill just skips
        out: Dict[str, str] = {}
        stamp = datetime.datetime.now().strftime("%H-%M-%S")
        try:
            img = Image.open(frame_path)
        except Exception:
            return {}
        for key, rect in rects.items():
            try:
                x, y, w, h = [int(v) for v in rect]
                path = os.path.join(config.CAPTURE_DIR,
                                    "crop_%s_%s.png" % (key, stamp))
                img.crop((x, y, x + w, y + h)).save(path)
                out[key] = path
            except Exception:
                continue
        return out

    def screen_size(self, tk_root: Any = None) -> Optional[Tuple[int, int]]:
        if self._fn_size is not None:
            try:
                got = self._fn_size()
                if isinstance(got, (tuple, list)) and len(got) == 2:
                    return (int(got[0]), int(got[1]))
            except Exception:
                pass
        try:                                # real pixels, Retina-correct
            from PIL import ImageGrab
            img = ImageGrab.grab()
            return (img.width, img.height)
        except Exception:
            pass
        if tk_root is not None:             # logical points; wrong on Retina
            try:
                return (int(tk_root.winfo_screenwidth()),
                        int(tk_root.winfo_screenheight()))
            except Exception:
                pass
        return None


# ── Claude (sibling coach module, or built-in fallback) ──────────────────────
class FallbackClaudeSession:
    """Minimal headless-CLI session, contract-identical to v2's ClaudeSession.

    Verified CLI shape: claude -p PROMPT --output-format json --allowedTools ...
    [--resume SESSION] [--model M] -> stdout JSON with result + session_id.
    Images are read by FILE PATH mentioned in the prompt.
    """

    def __init__(self) -> None:
        self.session_id: Optional[str] = None
        self.calls = 0

    def call(self, prompt: str, allow_write: bool = False,
             model: Optional[str] = None) -> str:
        tools = "Read,Write,Edit,Glob" if allow_write else "Read"
        cmd = ["claude", "-p", prompt, "--output-format", "json",
               "--allowedTools", tools]
        if model:
            cmd += ["--model", model]
        if self.session_id:
            cmd += ["--resume", self.session_id]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=CLAUDE_TIMEOUT, cwd=config.REPO_DIR)
        except subprocess.TimeoutExpired:
            return "[x] Claude call timed out."
        except FileNotFoundError:
            return "[x] `claude` CLI not found on PATH."
        if out.returncode != 0:
            return "[x] Claude error: %s" % (out.stderr or out.stdout).strip()[:400]
        try:
            data = json.loads(out.stdout)
        except ValueError:
            return out.stdout.strip()[:1200]
        self.session_id = data.get("session_id", self.session_id)
        self.calls += 1
        return (data.get("result") or "").strip() or "[x] Empty response."


class CoachAdapter:
    """Prompt building + Claude calls, from tftcoach.coach when available."""

    def __init__(self) -> None:
        self.mod = optional_import("tftcoach.coach")
        session_cls = getattr(self.mod, "ClaudeSession", None) if self.mod else None
        try:
            self.session = session_cls() if session_cls else FallbackClaudeSession()
        except Exception:
            self.session = FallbackClaudeSession()
        self._fn_vision = pick(self.mod, "vision_fill", "fill_from_vision")
        self._fn_state_prompt = pick(self.mod, "coach_prompt", "build_prompt",
                                     "state_prompt")
        self._fn_frame_prompt = pick(self.mod, "fullframe_prompt",
                                     "fallback_prompt", "image_prompt")
        self._fn_post_prompt = pick(self.mod, "postgame_prompt", "post_game_prompt")
        self.fast_model = getattr(self.mod, "FAST_MODEL", FAST_MODEL_DEFAULT) \
            if self.mod else FAST_MODEL_DEFAULT
        self.strong_model = getattr(self.mod, "STRONG_MODEL", STRONG_MODEL_DEFAULT) \
            if self.mod else STRONG_MODEL_DEFAULT
        self.auto_model = getattr(self.mod, "AUTO_MODEL", AUTO_MODEL_DEFAULT) \
            if self.mod else AUTO_MODEL_DEFAULT

    # -- status ----------------------------------------------------------
    def is_available(self) -> Tuple[bool, str]:
        exe = shutil.which("claude")
        if not exe:
            return (False, "`claude` CLI not on PATH")
        return (True, exe)

    @property
    def session_id(self) -> Optional[str]:
        return getattr(self.session, "session_id", None)

    @property
    def calls(self) -> int:
        return int(getattr(self.session, "calls", 0) or 0)

    def reset_session(self) -> None:
        try:
            self.session = type(self.session)()
        except Exception:
            self.session = FallbackClaudeSession()

    def call(self, prompt: str, allow_write: bool = False,
             model: Optional[str] = None) -> str:
        fn = getattr(self.session, "call", None)
        if fn is None:
            return "[x] coach session has no call()"
        try:                                # sibling sessions may lack `model`
            return fn(prompt, allow_write=allow_write, model=model)
        except TypeError:
            try:
                return fn(prompt, allow_write)
            except TypeError:
                return fn(prompt)

    # -- vision gap-fill --------------------------------------------------
    def vision_fill(self, state: GameState, crops: Dict[str, str]) -> GameState:
        if not crops:
            return state
        if self._fn_vision is not None:
            try:
                got = call_best_effort(self._fn_vision, state, crops, self.session)
                if isinstance(got, GameState):
                    return got
            except Exception:
                return state
            return state
        return self._fallback_vision_fill(state, crops)

    def _fallback_vision_fill(self, state: GameState, crops: Dict[str, str]) -> GameState:
        """Board/bench crops -> unit names, via the cheap model, JSON out.

        Names are NOT trusted here — tftcoach.entities does whitelist
        validation. Without that module we keep confidence low on purpose.
        """
        listing = "\n".join("%s: %s" % (k, p) for k, p in sorted(crops.items()))
        prompt = ("Read these cropped TFT screenshots by file path and list the "
                  "champions you can actually identify. Do not guess.\n" + listing +
                  '\nReply with ONLY JSON: {"board": [{"name": str, "star": int|null}], '
                  '"bench": [{"name": str, "star": int|null}]}. '
                  "Omit any unit you cannot read. No prose.")
        raw = self.call(prompt, model=self.fast_model)
        try:
            start, end = raw.find("{"), raw.rfind("}")
            data = json.loads(raw[start:end + 1])
        except Exception:
            return state
        from tftcoach.state import Field
        for key in ("board", "bench"):
            items = data.get(key)
            if isinstance(items, list) and items:
                names = [str(u.get("name")) for u in items
                         if isinstance(u, dict) and u.get("name")]
                if names:
                    # Unvalidated vision output: deliberately just above the
                    # MIN_CONFIDENCE floor, never as trusted as OCR.
                    setattr(state, key, Field(value=names, confidence=0.6,
                                              source="vision"))
        return state

    # -- prompts ----------------------------------------------------------
    def state_prompt(self, state: GameState, timeline: Timeline, first: bool,
                     note: str = "") -> str:
        if self._fn_state_prompt is not None:
            try:
                return call_best_effort(self._fn_state_prompt, state, timeline,
                                        first, note)
            except Exception:
                pass
        return self._fallback_state_prompt(state, timeline, first, note)

    def _fallback_state_prompt(self, state: GameState, timeline: Timeline,
                               first: bool, note: str) -> str:
        p = ""
        if first:
            p += ("You are my TFT coach for one LIVE game. Context below holds for "
                  "the whole session; each round I send exact state extracted "
                  "locally by OCR. Reason over trends across the timeline, not a "
                  "single tick.\n\n" + load_context())
        known = state.known_fields()
        unknown = state.unknown_fields()
        delta = timeline.delta()
        p += "== STATE NOW (locally extracted, exact) ==\n"
        p += json.dumps(known, ensure_ascii=False) + "\n"
        if unknown:
            p += ("UNKNOWN this tick — treat as unavailable, never guess a value: "
                  + ", ".join(unknown) + "\n")
        if delta:
            p += "DELTA since last tick: " + json.dumps(delta) + "\n"
        hist = timeline.render()
        if hist:
            p += "== TIMELINE (stage | gold | level | hp | streak) ==\n" + hist + "\n"
        if state.raw_capture and not state.board.known:
            p += ("A full frame is at %s if you need to check the board.\n"
                  % state.raw_capture)
        if note:
            p += "My note: %s\n" % note
        p += ("Give me MAX 4 bullets, most urgent first, each prefixed [ECON] "
              "[ITEM] [BOARD] or [COMBAT], each referencing observed state, one "
              "short line each, no preamble. If key state is unknown, say what "
              "you'd need rather than assuming it.")
        return p

    def frame_prompt(self, image_path: str, first: bool, note: str = "") -> str:
        if self._fn_frame_prompt is not None:
            try:
                return call_best_effort(self._fn_frame_prompt, image_path, first, note)
            except Exception:
                pass
        p = ""
        if first:
            p += ("You are my TFT coach for one LIVE game. Coach with the context "
                  "below all session; I send a screenshot each round.\n\n"
                  + load_context())
        p += "Read the screenshot at %s — this is my screen right now.\n" % image_path
        if note:
            p += "My note: %s\n" % note
        p += ("Extract only what you can actually see (stage-round, gold, level, HP, "
              "shop, board, augments); never guess unreadable values. Then MAX 4 "
              "bullets, most urgent first, each prefixed [ECON] [ITEM] [BOARD] or "
              "[COMBAT], one short line each, no preamble. If the screen isn't a "
              "TFT game, say so in one line.")
        return p

    def postgame_prompt(self, result_note: str) -> str:
        if self._fn_post_prompt is not None:
            try:
                return call_best_effort(self._fn_post_prompt, result_note)
            except Exception:
                pass
        today = datetime.date.today().isoformat()
        return ("The game just ended. Result: %s\n"
                "Do the post-game pass on the Obsidian vault in %s:\n"
                "1. Create 'vault/Games/%s Game.md' (append ' 2', ' 3' if it exists) "
                "following vault/Templates/Game Note.md: frontmatter (placement, comp, "
                "set+patch from vault/Meta/Current Patch.md, source: optionb-live), a "
                "timeline summary from this session, and 'What decided this game' in "
                "2-3 sentences.\n"
                "2. Advice audit: grade each tip you gave this session against the result.\n"
                "3. Lessons: for each observed mistake, if a matching note exists in "
                "vault/Lessons/ add this game to its frontmatter evidence list; if novel "
                "and testable, create a candidate lesson from vault/Templates/Lesson Note.md.\n"
                "4. Do NOT edit vault/TFT-Brain.md; if a lesson reached 3+ evidence "
                "links, mention it as a promotion candidate instead.\n"
                "5. Reply with: placement, the one thing to change next game, files written."
                % (result_note, config.VAULT_DIR, today))


# ── OCR + triggers adapters ──────────────────────────────────────────────────
class OCRAdapter:
    def __init__(self) -> None:
        self.mod = optional_import("tftcoach.ocr")
        self._fn = pick(self.mod, "extract_state", "extract", "read_state")

    def is_available(self) -> Tuple[bool, str]:
        if self.mod is None or self._fn is None:
            return (False, "tftcoach.ocr.extract_state not present")
        if pick(self.mod, "is_available") is None:
            return (True, "tftcoach.ocr (no self-check)")
        return availability(self.mod, "tftcoach.ocr")

    def extract(self, frame_path: str, rects: Dict[str, List[int]]) -> GameState:
        if self._fn is None:
            raise RuntimeError("tftcoach.ocr.extract_state unavailable")
        state = call_best_effort(self._fn, frame_path, rects)
        if not isinstance(state, GameState):
            raise RuntimeError("ocr.extract_state did not return a GameState")
        if not state.raw_capture:
            state.raw_capture = frame_path
        return state


class TriggerAdapter:
    """Wraps tftcoach.triggers.TriggerEngine; falls back to a plain timer.

    poll() returns a reason string when a coaching event fires, else None.
    """

    def __init__(self, regions: Any, capture: CaptureAdapter) -> None:
        self.mod = optional_import("tftcoach.triggers")
        self.engine = None
        self._poll = None
        cls = getattr(self.mod, "TriggerEngine", None) if self.mod else None
        if cls is not None:
            for args in ((regions, capture), (regions,), ()):
                try:
                    self.engine = cls(*args)
                    break
                except Exception:
                    continue
        if self.engine is not None:
            self._poll = pick(self.engine, "poll", "check", "next_event")
        self._last_fire = 0.0

    @property
    def name(self) -> str:
        return "triggers.TriggerEngine" if self._poll else "timer fallback"

    def poll(self) -> Optional[str]:
        if self._poll is not None:
            try:
                got = self._poll()
            except Exception:
                got = None
            if not got:
                return None
            if isinstance(got, str):
                return got
            for attr in ("reason", "name", "kind"):
                val = getattr(got, attr, None)
                if isinstance(val, str) and val:
                    return val
            return "event"
        # Fallback: fixed cadence, the v2 behaviour.
        now = time.time()
        if now - self._last_fire >= max(config.MIN_SECONDS_BETWEEN_CALLS, 30.0):
            self._last_fire = now
            return "timer"
        return None

    def reset(self) -> None:
        self._last_fire = 0.0
        fn = pick(self.engine, "reset") if self.engine else None
        if fn:
            try:
                fn()
            except Exception:
                pass


# ── Overlay ──────────────────────────────────────────────────────────────────
class CoachApp:
    def __init__(self, root: Any) -> None:
        import tkinter as tk
        from tkinter import scrolledtext
        self.tk = tk
        self.root = root
        self.ui_queue: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self.running = False
        self.busy = False
        self.mode = MODE_FULLFRAME
        self.last_state: Optional[GameState] = None
        self.last_call_ts = 0.0

        config.ensure_dirs()
        self.capture = CaptureAdapter()
        self.ocr = OCRAdapter()
        self.entities = optional_import("tftcoach.entities")
        self.coach = CoachAdapter()
        self.regions = config.Regions.load()
        self.rects: Dict[str, List[int]] = dict(self.regions.rects)
        self.triggers = TriggerAdapter(self.regions, self.capture)
        self.timeline = Timeline(config.GAMES_DIR)

        root.title("TFT Coach — Option B")
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.94)
        except Exception:
            pass
        # Compact by default: an overlay that hides the game is worse than no
        # overlay. Resizable; header click toggles a bar-only collapsed mode.
        root.geometry("360x240+20+20")
        root.configure(bg=COL_BG)
        root.minsize(260, 34)

        header = tk.Frame(root, bg=COL_PANEL, pady=3)
        header.pack(fill="x")
        self.title_lbl = tk.Label(header, text="TFT COACH  (click to collapse)",
                 font=("Courier", 10, "bold"), fg=COL_WARN, bg=COL_PANEL)
        self.title_lbl.pack(side="left", padx=8)
        self.dot = tk.Label(header, text="●", font=("Courier", 12), fg="#444",
                            bg=COL_PANEL)
        self.dot.pack(side="right", padx=8)
        self.collapsed = False
        self._expanded_geo = None
        for w in (header, self.title_lbl):
            w.bind("<Button-1>", lambda _e: self.toggle_collapse())

        # Packed IMMEDIATELY (before the check panel and advice box): Tk pack
        # starves the LAST-packed widgets when space runs out, and the control
        # bar must be the last thing standing, not the first casualty.
        bar = tk.Frame(root, bg=COL_BG, pady=3)
        bar.pack(side="bottom", fill="x")
        self.btn = tk.Button(bar, text="START", font=("Courier", 9, "bold"),
                             fg=COL_OK, command=self.toggle)
        self.btn.pack(side="left", padx=4)
        for label, cmd in (("TIP", self.tip_now), ("SCOUT", self.scout),
                           ("END", self.end_game), ("CAL", self.show_calibrate)):
            tk.Button(bar, text=label, font=("Courier", 9),
                      command=cmd).pack(side="left", padx=2)
        tk.Button(bar, text="X", font=("Courier", 9),
                  command=self.quit).pack(side="right", padx=4)
        self.status = tk.Label(root, text="", font=("Courier", 8), fg=COL_DIM,
                               bg=COL_BG, anchor="w")
        self.status.pack(side="bottom", fill="x", padx=8)

        # self-check panel (auto-hides once everything is green)
        self.check = tk.Text(root, height=7, wrap="word", font=("Courier", 9),
                             bg=COL_PANEL, fg=COL_DIM, relief="flat", bd=0,
                             padx=10, pady=6, state="disabled")
        self.check.pack(fill="x", padx=4, pady=(4, 2))
        self.check.tag_configure("ok", foreground=COL_OK)
        self.check.tag_configure("bad", foreground=COL_BAD)
        self.check.tag_configure("warn", foreground=COL_WARN)

        self.text = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Courier", 10), bg=COL_TEXTBG, fg=COL_FG,
            relief="flat", bd=0, padx=8, pady=6, state="disabled", height=7)
        self.text.pack(fill="both", expand=True, padx=4, pady=2)
        for tag, color in TAG_COLORS.items():
            self.text.tag_configure(tag, foreground=color)



        self.set_text("Running self-check...")
        self.set_status()
        root.after(UI_TICK_MS, self.drain_queue)
        threading.Thread(target=self.self_check, daemon=True).start()
        self.install_hotkey()
        root.after(6000, self.watch_game)

    # ── UI plumbing (worker threads never touch Tk) ──────────────────────
    def drain_queue(self) -> None:
        try:
            while True:
                self.ui_queue.get_nowait()()
        except queue.Empty:
            pass
        except Exception:
            pass
        self.root.after(UI_TICK_MS, self.drain_queue)

    def ui(self, fn: Callable[[], None]) -> None:
        self.ui_queue.put(fn)

    def set_text(self, msg: str) -> None:
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        for line in msg.split("\n"):
            tag = None
            for t in TAG_COLORS:
                if line.strip().startswith(t):
                    tag = t
                    break
            self.text.insert("end", line + "\n", tag)
        self.text.config(state="disabled")

    def set_checks(self, rows: List[Tuple[str, str, str]]) -> None:
        """rows: (tag, label, detail) with tag in ok|bad|warn."""
        self.check.config(state="normal")
        self.check.delete("1.0", "end")
        for tag, label, detail in rows:
            mark = "OK  " if tag == "ok" else ("FAIL" if tag == "bad" else "WARN")
            self.check.insert("end", "%s  %-11s %s\n" % (mark, label, detail), tag)
        self.check.config(state="disabled")
        # All green: the panel has said everything it needed to. Reclaim the
        # space — problems keep it visible, and set_status carries the rest.
        if rows and all(tag == "ok" for tag, _l, _d in rows):
            self.root.after(4000, self.check.pack_forget)

    @staticmethod
    def _game_running() -> bool:
        """True while the actual TFT/League GAME process exists (not the
        lobby client — 'LeagueClient' runs all day; the game process only
        exists in a match)."""
        try:
            out = subprocess.run(["pgrep", "-if", "League of Legends"],
                                 capture_output=True, text=True, timeout=5)
            return bool(out.stdout.strip())
        except Exception:
            return False

    def watch_game(self) -> None:
        """Auto start/stop with the game so nobody has to press START.

        Polls the process list every 8s. Game appears -> start the loop;
        game exits -> stop and prompt for END (the vault write stays manual
        because only the player knows the placement)."""
        try:
            up = self._game_running()
            if up and not self.running:
                self.toggle()
                self.set_text("Game detected — coaching started.")
            elif not up and self.running:
                self.toggle()
                self.set_text("Game over — press END to write the vault note\n"
                              "(placement + comp), or START for the next game.")
                play_alert()
        except Exception:
            pass
        self.root.after(8000, self.watch_game)

    def toggle_collapse(self) -> None:
        """Header click: shrink to a title bar (game visible), click to restore."""
        if self.collapsed:
            self.root.geometry(self._expanded_geo or "360x240")
            self.collapsed = False
            self.title_lbl.config(text="TFT COACH  (click to collapse)")
        else:
            self._expanded_geo = self.root.geometry()
            # keep x/y, collapse height to the header only
            pos = self._expanded_geo.split("+", 1)
            xy = ("+" + pos[1]) if len(pos) == 2 else "+20+20"
            self.root.geometry("300x30" + xy)
            self.collapsed = True
            self.title_lbl.config(text="TFT COACH  (click to expand)")

    def set_status(self, extra: str = "") -> None:
        st = self.last_state
        if st is not None:
            live = st.summary_line()
        else:
            live = "— | ?g | lv? | ?hp"
        sid = self.coach.session_id
        self.status.config(text="%s | %s | calls: %d | sess: %s %s" % (
            self.mode, live, self.coach.calls, sid[:8] if sid else "—", extra))

    # ── startup self-check ───────────────────────────────────────────────
    def self_check(self) -> None:
        rows: List[Tuple[str, str, str]] = []

        cap_ok, cap_why = self.capture.is_available()
        rows.append(("ok" if cap_ok else "bad", "capture", cap_why))

        ocr_ok, ocr_why = self.ocr.is_available()
        rows.append(("ok" if ocr_ok else "bad", "ocr", ocr_why))

        ent_ok, ent_why = availability(self.entities, "tftcoach.entities")
        rows.append(("ok" if ent_ok else "warn", "entities",
                     ent_why + ("" if ent_ok else " (names unvalidated)")))

        cl_ok, cl_why = self.coach.is_available()
        rows.append(("ok" if cl_ok else "bad", "claude", cl_why))

        cal_ok = self.regions.calibrated and not self.regions.missing()
        if self.regions.calibrated:
            miss = self.regions.missing()
            cal_why = ("%dx%d, %d regions" % (self.regions.resolution[0],
                                              self.regions.resolution[1],
                                              len(self.regions.rects))
                       if cal_ok else "missing: " + ", ".join(miss))
        else:
            cal_why = "regions.json absent — run CALIBRATE"
        rows.append(("ok" if cal_ok else "warn", "regions", cal_why))

        meta_ok, meta_why = meta_populated()
        rows.append(("ok" if meta_ok else "warn", "meta", meta_why))

        # Live-vs-calibrated resolution: scaled rects are best effort only.
        size = self.capture.screen_size(self.root)
        if cal_ok and size and list(size) != list(self.regions.resolution):
            self.rects = self.regions.for_resolution(size[0], size[1])
            rows.append(("warn", "resolution",
                         "screen %dx%d != calibrated %dx%d — rects scaled, "
                         "recalibrate if reads are wrong"
                         % (size[0], size[1], self.regions.resolution[0],
                            self.regions.resolution[1])))
        else:
            self.rects = dict(self.regions.rects)

        rows.append(("ok", "triggers", self.triggers.name))

        self.mode = MODE_OCR if (cap_ok and ocr_ok and cal_ok) else MODE_FULLFRAME
        if self.mode == MODE_FULLFRAME and not config.FULLFRAME_FALLBACK:
            body = ("Full-frame fallback is disabled in config and OCR mode is not "
                    "available. Fix the FAIL lines above, or set "
                    "FULLFRAME_FALLBACK = True.")
        elif self.mode == MODE_FULLFRAME:
            why = "OCR unavailable" if not ocr_ok else (
                "regions not calibrated" if not cal_ok else "capture unavailable")
            body = ("MODE: FULL-FRAME FALLBACK (%s).\n"
                    "Whole screenshot goes to the vision model — same behaviour as "
                    "tft_coach_v2.py, no exact numbers. Press CALIBRATE for the "
                    "one-time fix.\n\nPress START when your game begins." % why)
        else:
            body = ("MODE: OCR — exact gold/level/stage/HP read locally, vision only "
                    "for board/bench crops.\n\nPress START when your game begins.\n"
                    "TIP NOW = manual tip (strong model, ignores rate limit).\n"
                    "SCOUT = press while viewing an ENEMY board — feeds "
                    "contest tracking + threat read.\n"
                    "END GAME = write the vault game note.")
        if not cl_ok:
            body = ("Claude CLI missing — advice calls will fail. Install Claude Code "
                    "and log in.\n\n") + body

        self.ui(lambda: (self.set_checks(rows), self.set_text(body), self.set_status()))

    # ── optional global hotkey (never a hard dependency) ─────────────────
    def install_hotkey(self) -> None:
        try:
            import keyboard              # needs root on macOS; optional by design
            keyboard.add_hotkey("f9", self.tip_now)
        except Exception:
            pass                          # silently skip — documented behaviour

    # ── pipeline ─────────────────────────────────────────────────────────
    def build_state(self, want_vision: bool = False) -> Tuple[GameState, str]:
        """Capture + extract. Returns (state, prompt) for the current mode."""
        first = self.coach.session_id is None
        if self.mode == MODE_OCR:
            frame = self.capture.full_frame(downscale=False)
            try:
                state = self.ocr.extract(frame, self.rects)
            except Exception as exc:
                # OCR blew up mid-game: don't fabricate, drop to fallback.
                self.mode = MODE_FULLFRAME
                self.ui(lambda e=exc: self.set_status("ocr failed: %s" % e))
                return self.build_state()
            # The vision pass is a SECOND full Claude call before the coach
            # call — it doubles tick latency. Routine ticks coach from OCR
            # state alone; board/bench vision runs only on demand (TIP NOW,
            # augment rounds), where the extra ~15s is worth it.
            crops_wanted = {k: self.rects[k] for k in config.VISION_FIELDS
                            if k in self.rects}
            needs_vision = want_vision and (
                not state.board.known or not state.bench.known)
            if crops_wanted and needs_vision:
                state = self.coach.vision_fill(state, self.capture.crops(frame, crops_wanted))
            self.timeline.append(state)
            prompt = self.coach.state_prompt(state, self.timeline, first)
            pool_block = self._pool_observe(state)
            if pool_block:
                prompt += "\n\n" + pool_block
            return (state, prompt)
        frame = self.capture.full_frame(downscale=True)
        state = GameState(raw_capture=frame)      # every field stays unknown
        self.timeline.append(state)
        return (state, self.coach.frame_prompt(frame, first))

    def run_tick(self, trigger: str, manual: bool = False, note: str = "") -> None:
        if self.busy:
            return
        self.busy = True
        self.ui(lambda: self.set_status("working (%s)" % trigger))
        try:
            want_vision = manual or trigger in ("augment", "carousel")
            state, prompt = self.build_state(want_vision)
            if note:
                prompt += "\nMy note: %s" % note
            self.last_state = state
            model = self.coach.strong_model if manual else self.coach.auto_model
            result = self.coach.call(prompt, model=model)
            self.last_call_ts = time.time()
            self.timeline.append_advice(result, trigger)
        except Exception as exc:
            result = "[x] %s: %s" % (type(exc).__name__, exc)
        finally:
            self.busy = False
        play_alert()
        self.ui(lambda r=result: (self.set_text(r), self.set_status()))

    def loop(self) -> None:
        while self.running:
            reason = self.triggers.poll()
            if reason and not self.busy:
                gap = time.time() - self.last_call_ts
                if gap >= config.MIN_SECONDS_BETWEEN_CALLS:
                    self.run_tick(reason)
                else:
                    wait = config.MIN_SECONDS_BETWEEN_CALLS - gap
                    self.ui(lambda w=wait, r=reason:
                            self.set_status("%s held %.0fs (rate limit)" % (r, w)))
            time.sleep(config.POLL_INTERVAL_SEC)
        self.ui(lambda: self.set_status())

    # ── buttons ──────────────────────────────────────────────────────────
    def toggle(self) -> None:
        if self.running:
            self.running = False
            self.btn.config(text="START", fg=COL_OK)
            self.dot.config(fg="#444")
        else:
            self.running = True
            self.btn.config(text="STOP", fg=COL_BAD)
            self.dot.config(fg=COL_OK)
            self.triggers.reset()
            threading.Thread(target=self.loop, daemon=True).start()

    def tip_now(self) -> None:
        # Manual: strongest model, no rate limit. Safe to call from any thread.
        threading.Thread(target=self.run_tick, args=("manual",),
                         kwargs={"manual": True}, daemon=True).start()

    def scout(self) -> None:
        """Press while an OPPONENT's board is on screen.

        One vision call reads their board; the result feeds pool/contest
        tracking and comes back as a threat brief (who contests my line, what
        damage type, where their carry sits). This is the only path that ever
        sees an enemy board, so it is what turns 'scout more' from a slogan
        into data.
        """
        def work() -> None:
            if self.busy:
                return
            self.busy = True
            self.ui(lambda: self.set_status("scouting..."))
            try:
                frame = self.capture.full_frame(downscale=True)
                prompt = (
                    "SCOUT REPORT. Read the screenshot at %s — it shows an "
                    "OPPONENT's TFT board (not mine). Return STRICT JSON only:\n"
                    '{"player": "<name if visible or null>", "units": '
                    '[{"name": "...", "star": 1|2|3, "items": ["..."]}], '
                    '"front_row_units": ["..."], "carry_guess": "<most-itemized '
                    'unit>", "damage_type": "AD"|"AP"|"mixed"}\n'
                    "Only units actually visible; never invent." % frame)
                raw = self.coach.call(prompt, model=self.coach.auto_model)
                try:
                    from tftcoach.coach import extract_json_object
                    data = extract_json_object(raw) or {}
                except Exception:
                    data = {}
                units = data.get("units") or []
                if units and getattr(self, "_pool", None) is not None:
                    try:
                        self._pool.observe_scout(units)
                    except Exception:
                        pass
                if data:
                    brief = ("SCOUTED %s: %d units, carry=%s, damage=%s, "
                             "front=%s" % (data.get("player") or "opponent",
                                           len(units),
                                           data.get("carry_guess") or "?",
                                           data.get("damage_type") or "?",
                                           ", ".join(data.get("front_row_units")
                                                     or [])[:60]))
                    self.timeline.append_advice(brief, "scout")
                    self.ui(lambda b=brief: self.set_text(
                        b + "\n\nPool tracking updated. Positioning advice on "
                            "the next tick will account for this board."))
                else:
                    self.ui(lambda r=raw: self.set_text(
                        "Scout read failed — is an enemy board on screen?\n\n"
                        + str(r)[:300]))
            except Exception as exc:
                self.ui(lambda e=exc: self.set_text("Scout error: %s" % e))
            finally:
                self.busy = False
                self.ui(self.set_status)
        threading.Thread(target=work, daemon=True).start()

    def show_calibrate(self) -> None:
        cmd = "%s -m tftcoach.calibrate" % (os.path.basename(sys.executable) or "python3")
        self.set_text(
            "CALIBRATE — one-time per resolution (and again after the Set 18\n"
            "Unreal client lands on Aug 26, 2026).\n\n"
            "1. Put TFT in 1920x1080 BORDERLESS, sit in a planning phase.\n"
            "2. In a terminal at %s run:\n\n    %s\n\n"
            "3. Drag a box around each region it names, then restart this app.\n\n"
            "(command copied to your clipboard)" % (config.REPO_DIR, cmd))
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd)
        except Exception:
            pass

    def end_game(self) -> None:
        from tkinter import simpledialog
        if self.coach.session_id is None:
            self.set_text("No Claude session yet — coach a game first.")
            return
        placement = simpledialog.askstring(
            "End Game", "Placement? (1-8)", parent=self.root)
        if not placement:
            return
        comp = simpledialog.askstring(
            "End Game", "Comp + what decided it (e.g. 'star guardian jinx, "
            "greedy 4-1 roll')", parent=self.root) or ""
        self.running = False
        self.btn.config(text="START", fg=COL_OK)
        self.dot.config(fg="#444")
        self.set_text("Writing game note + lesson updates into the vault...")
        note = "placement %s; %s" % (placement.strip(), comp.strip())

        def run() -> None:
            out = self.coach.call(self.coach.postgame_prompt(note),
                                  allow_write=True,
                                  model=self.coach.strong_model)
            self.timeline.append_advice(out, "postgame")
            play_alert()
            self.ui(lambda: (self.set_text("Post-game pass done:\n\n" + out
                                           + "\n\nTimeline: " + self.timeline.path),
                             self.set_status()))
            self.new_game()

        threading.Thread(target=run, daemon=True).start()

    def _pool_observe(self, state: GameState) -> str:
        """Feed the pool tracker and return its prompt block ('' when silent).

        Best-effort by design: pool intel improves advice but must never be
        able to break a tick.
        """
        try:
            if getattr(self, "_pool", None) is None:
                from tftcoach import entities as ent_mod
                from tftcoach.pool import PoolTracker
                self._pool = PoolTracker(ent_mod.load_entities())
            self._pool.observe(state)
            return self._pool.prompt_block()
        except Exception:
            return ""

    def new_game(self) -> None:
        """Fresh timeline + fresh Claude session for the next match."""
        self.coach.reset_session()
        self.timeline = Timeline(config.GAMES_DIR)
        self.last_state = None
        self.last_call_ts = 0.0
        self._pool = None          # pool knowledge is per-game by definition
        self.triggers.reset()
        self.ui(self.set_status)

    def quit(self) -> None:
        self.running = False
        self.root.quit()


def headless_check() -> int:
    """`python3 run_coach.py --check` — verify the stack without opening the UI.

    Use this after installing deps, after calibrating, and on the Windows box.
    """
    from tftcoach import capture, coach, entities, meta_feed, ocr

    print("TFT Coach — Option B setup check\n")
    rows = []
    for label, mod in (("capture", capture), ("ocr", ocr), ("entities", entities),
                       ("claude", coach), ("meta", meta_feed)):
        try:
            ok, why = mod.is_available()
        except Exception as exc:  # a broken module must not hide the others
            ok, why = False, "raised {0}".format(exc.__class__.__name__)
        rows.append((ok, label, why))

    regions = config.Regions.load()
    if not regions.calibrated:
        rows.append((False, "regions", "not calibrated — run python3 -m tftcoach.calibrate"))
    else:
        missing = regions.missing()
        rows.append((not missing, "regions",
                     "{0}x{1}, {2} regions{3}".format(
                         regions.resolution[0], regions.resolution[1],
                         len(regions.rects),
                         "" if not missing else "; missing: " + ", ".join(missing))))

    for ok, label, why in rows:
        print(" {0}  {1:<9} {2}".format("OK  " if ok else "MISS", label, why))

    blocking = [l for ok, l, _ in rows if not ok and l in ("capture", "claude")]
    degraded = [l for ok, l, _ in rows if not ok and l not in ("capture", "claude")]
    print("")
    if blocking:
        print("BLOCKED: {0} must work before the coach can run.".format(
            ", ".join(blocking)))
        return 1
    if degraded:
        print("Runs in FULL-FRAME FALLBACK mode (whole screenshot to Claude, "
              "same as tft_coach_v2.py). Fix {0} for exact local extraction."
              .format(", ".join(degraded)))
    else:
        print("All green — structured extraction active.")
    return 0


def _macos_float_over_game(root: Any) -> str:
    """Make the overlay visible above League in borderless mode on macOS.

    Tk's -topmost only floats above windows in the current Space. League's
    borderless mode occupies its own Space, so the overlay silently ends up
    behind the game and the user has to alt-tab. Raising the real NSWindow
    level and letting it join all Spaces (incl. fullscreen ones) fixes it.
    Best-effort: without pyobjc the overlay still works in the same Space.
    """
    if platform.system() != "Darwin":
        return ""
    try:
        import AppKit
        root.update_idletasks()
        floated = 0
        for win in AppKit.NSApp.windows():
            win.setLevel_(AppKit.NSStatusWindowLevel)
            win.setCollectionBehavior_(
                AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary)
            floated += 1
        return "float: over all Spaces (%d win)" % floated
    except ImportError:
        return ("float: pyobjc missing — overlay only floats in the same "
                "Space. pip install pyobjc-framework-Cocoa==10.3.1")
    except Exception as exc:
        return "float: failed (%s)" % exc


def refresh_brain() -> int:
    """`./coach refresh` — pull every live data feed into the vault."""
    config.ensure_dirs()
    jobs = (("comps + tier snapshot", "tftcoach.meta_feed", "refresh"),
            ("unit/item/augment stats", "tftcoach.meta_feed", "refresh_stats"),
            ("high-elo playbook", "tftcoach.highelo", "refresh"))
    failed = 0
    for label, module_name, fn_name in jobs:
        fn = pick(optional_import(module_name), fn_name)
        try:
            ok, msg = fn(verbose=False) if fn else (False, "module missing")
        except Exception as exc:
            ok, msg = False, str(exc)
        print("%s %-26s %s" % ("OK  " if ok else "FAIL", label, msg))
        failed += 0 if ok else 1
    print("\nBrain refreshed." if not failed else
          "\n%d feed(s) failed — old snapshots kept." % failed)
    return 1 if failed else 0


def main() -> int:
    if "refresh" in sys.argv or "--refresh" in sys.argv:
        return refresh_brain()
    if "--check" in sys.argv:
        config.ensure_dirs()
        return headless_check()
    try:
        import tkinter as tk
    except ImportError:
        print("tkinter not available. macOS: brew install python-tk "
              "(or use python.org Python). Windows: reinstall Python with tcl/tk.")
        return 1
    config.ensure_dirs()
    root = tk.Tk()
    app = CoachApp(root)

    def assert_float() -> None:
        msg = _macos_float_over_game(root)
        if msg:
            try:
                app.set_status(msg)
            except Exception:
                pass
        # Re-assert every 20s: some games reset window ordering on focus
        # changes, and the call is idempotent and cheap.
        root.after(20000, assert_float)

    root.after(500, assert_float)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
