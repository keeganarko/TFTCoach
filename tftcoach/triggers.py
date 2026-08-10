"""Event-driven cadence for TFT Coach Option B.

v1 fired a Claude call every 30-60s on a dumb timer: half the tips landed
mid-combat (useless — the board is locked) and half missed the ~30s planning
window where every real decision is made. This module watches ONE cheap signal
(the small calibrated "stage" region, OCR'd at config.POLL_INTERVAL_SEC) and
fires only at moments that matter.

Design constraints this file obeys:
  * The poll path never grabs the full screen — only the stage rect.
  * Nothing here hardcodes pixel coordinates; rects come from config.Regions.
  * Every heavy dep (capture/ocr) is lazy-imported, so this module imports
    cleanly on a machine with nothing installed. is_available() reports why.
  * Unknown is first class: an unreadable stage yields None, never a guess.
  * Pure logic is injectable — pass any stage_reader() -> Optional[str] and the
    whole thing is unit-testable with no screen. See __main__.

Python 3.9 compatible (no PEP 604 unions at runtime, no match statements).
"""

from __future__ import annotations

import dataclasses
import queue
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # normal package import
    from tftcoach import config
except ImportError:  # running this file directly from inside tftcoach/
    import config  # type: ignore

# A stage reader returns the RAW text it saw in the stage region (e.g. "3-2",
# " 3 - 2 ", "Stage 3-2"), or None when it could not read anything at all.
StageReader = Callable[[], Optional[str]]

EVENT_KINDS = ("new_round", "augment", "carousel", "manual", "periodic")

# --- Convention-based round classification -----------------------------------
# CONVENTION, NOT TRUTH. In TFT as of Set 17 / patch 17.8 augments are offered
# on 2-1, 3-2 and 4-2, and the shared carousel is round x-4 from stage 2 on.
# Set 18 "Enchanted Wilds" (Aug 26 2026, Unreal engine) can change both.
# This classification ONLY relabels an event that would have fired as
# "new_round" anyway — if the convention is wrong we lose a label, never an
# event. Override these at runtime rather than editing code.
AUGMENT_ROUNDS = {(2, 1), (3, 2), (4, 2)}
CAROUSEL_ROUND = 4
CAROUSEL_MIN_STAGE = 2

# Safety net: if every detector is broken (uncalibrated, OCR down, HUD moved),
# still give the user advice this often so the tool is never silent.
DEFAULT_PERIODIC_SEC = 90.0

# Debounce: how many consecutive identical reads confirm a new stage value.
CONFIRM_READS = 2
# Drop a half-confirmed candidate after this many unreadable polls in a row
# (combat VFX / a full-screen animation can blank the region for a while).
MAX_MISSES_BEFORE_CANDIDATE_DROP = 6

# A jump this far backwards is a new game, not OCR noise (see _is_reset).
RESET_MAX_STAGE = 2   # only 1-x and 2-1 look like a real game start


# =============================================================================
# Stage text parsing
# =============================================================================

# Common single-char OCR confusions on the small stage HUD glyphs.
_CONFUSIONS = {
    "l": "1", "I": "1", "|": "1", "!": "1", "i": "1",
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "S": "5", "s": "5",
    "B": "8", "Z": "2", "z": "2",
}

_STAGE_RE = re.compile(r"([1-9])\s*[-–—_.:~]\s*([1-9])")


def _normalize(text: str) -> str:
    return "".join(_CONFUSIONS.get(ch, ch) for ch in text)


def parse_stage(text: Optional[str]) -> Optional[str]:
    """Raw OCR text -> canonical 'S-R', or None if it is not a stage.

    None means unknown. Never returns a guessed stage.
    """
    if not text:
        return None
    cleaned = _normalize(str(text).strip())
    m = _STAGE_RE.search(cleaned)
    if m:
        return "%s-%s" % (m.group(1), m.group(2))
    # Separator dropped entirely ("32"): accept only when the region contained
    # exactly two digits and nothing else numeric, so "3210" can't become 3-2.
    digits = [c for c in cleaned if c.isdigit()]
    if len(digits) == 2 and digits[0] != "0" and digits[1] != "0":
        return "%s-%s" % (digits[0], digits[1])
    return None


def stage_tuple(stage: Optional[str]) -> Optional[Tuple[int, int]]:
    if not stage:
        return None
    parts = stage.split("-")
    if len(parts) != 2:
        return None
    try:
        return (int(parts[0]), int(parts[1]))
    except ValueError:
        return None


def _order(stage: str) -> int:
    """Monotonic sort key so 3-4 < 4-1."""
    t = stage_tuple(stage)
    return 0 if t is None else t[0] * 100 + t[1]


def classify_round(stage: Optional[str]) -> str:
    """Which event kind a freshly-entered stage deserves.

    Degrades to 'new_round' whenever the stage is unparseable or the
    convention above does not match — never raises, never drops the event.
    """
    t = stage_tuple(stage)
    if t is None:
        return "new_round"
    st, rd = t
    if (st, rd) in AUGMENT_ROUNDS:
        return "augment"
    if rd == CAROUSEL_ROUND and st >= CAROUSEL_MIN_STAGE:
        return "carousel"
    return "new_round"


def _is_reset(old: str, new: str) -> bool:
    """True when a backwards jump is a NEW GAME rather than OCR noise.

    A real game restart lands on 1-1/1-2/... or 2-1 from a late stage. Anything
    else that goes backwards (4-2 -> 3-9, 3-2 -> 2-8) is noise and is dropped.
    """
    ot, nt = stage_tuple(old), stage_tuple(new)
    if ot is None or nt is None:
        return False
    return nt[0] <= RESET_MAX_STAGE and ot[0] - nt[0] >= 2


# =============================================================================
# Events
# =============================================================================

@dataclasses.dataclass
class Event:
    """Something worth spending a Claude call on."""

    kind: str                       # one of EVENT_KINDS
    stage: Optional[str] = None     # canonical 'S-R' or None (unknown)
    prev_stage: Optional[str] = None
    ts: float = 0.0                 # engine clock, not wall time
    reason: str = ""
    new_game: bool = False
    note: str = ""                  # free text for manual triggers

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    def __str__(self) -> str:
        s = "%-9s stage=%s" % (self.kind, self.stage or "?")
        if self.new_game:
            s += " [NEW GAME]"
        if self.reason:
            s += "  (%s)" % self.reason
        return s


# =============================================================================
# RoundWatcher — pure logic, no screen required
# =============================================================================

class RoundWatcher:
    """Turns a stream of noisy stage readings into clean round events.

    Feed it either by calling poll() (it pulls from the injected stage_reader)
    or by calling observe(raw_text) directly in tests. Both are equivalent;
    poll() is just observe(stage_reader()).
    """

    def __init__(self, stage_reader: Optional[StageReader] = None,
                 confirm_reads: int = CONFIRM_READS):
        self.stage_reader = stage_reader
        self.confirm_reads = max(1, confirm_reads)
        self.current: Optional[str] = None      # last CONFIRMED stage
        self.last_event: Optional[Event] = None
        self.misses = 0                         # consecutive unreadable polls
        self.reads = 0
        self._candidate: Optional[str] = None
        self._candidate_hits = 0

    # -- input ------------------------------------------------------------
    def poll(self) -> Optional[Event]:
        """Read the stage region once. Cheap: one small rect, no full frame."""
        raw = None
        if self.stage_reader is not None:
            try:
                raw = self.stage_reader()
            except Exception:
                raw = None   # a broken reader must not kill the loop
        return self.observe(raw)

    def observe(self, raw: Optional[str]) -> Optional[Event]:
        """Consume one reading. Returns an Event only when a round change is
        confirmed; None otherwise (including for every unreadable frame)."""
        self.reads += 1
        stage = parse_stage(raw)

        if stage is None:
            # Unreadable frame. Keep the pending candidate alive for a while —
            # combat effects routinely blank this region for a few seconds.
            self.misses += 1
            if self.misses >= MAX_MISSES_BEFORE_CANDIDATE_DROP:
                self._candidate, self._candidate_hits = None, 0
            return None
        self.misses = 0

        if stage == self.current:
            self._candidate, self._candidate_hits = None, 0
            return None

        # Debounce: the same NEW value must show up on consecutive polls.
        if stage == self._candidate:
            self._candidate_hits += 1
        else:
            self._candidate, self._candidate_hits = stage, 1
        if self._candidate_hits < self.confirm_reads:
            return None

        prev = self.current
        self._candidate, self._candidate_hits = None, 0

        if prev is None:
            self.current = stage
            return self._emit(stage, None, "first stage seen", new_game=True)

        if _order(stage) > _order(prev):
            self.current = stage
            return self._emit(stage, prev, "stage advanced")

        if _is_reset(prev, stage):
            self.current = stage
            return self._emit(stage, prev, "reset pattern -> new game",
                              new_game=True, force_kind="new_round")

        # Backwards but not a reset: OCR noise. Drop it, keep current.
        return None

    def _emit(self, stage: str, prev: Optional[str], reason: str,
              new_game: bool = False,
              force_kind: Optional[str] = None) -> Event:
        ev = Event(kind=force_kind or classify_round(stage), stage=stage,
                   prev_stage=prev, reason=reason, new_game=new_game)
        self.last_event = ev
        return ev

    # -- control ----------------------------------------------------------
    def reset(self) -> None:
        self.current = None
        self._candidate, self._candidate_hits = None, 0
        self.misses = 0

    @property
    def pending(self) -> Optional[str]:
        return self._candidate


# =============================================================================
# Default stage reader (capture + OCR), lazily wired
# =============================================================================

def _first_attr(mod: Any, names: Tuple[str, ...]) -> Optional[Callable]:
    for n in names:
        fn = getattr(mod, n, None)
        if callable(fn):
            return fn
    return None


def _coerce_text(result: Any) -> Optional[str]:
    """OCR helpers may return str, (text, confidence), or a state.Field."""
    if result is None:
        return None
    if isinstance(result, (tuple, list)):
        return _coerce_text(result[0]) if result else None
    val = getattr(result, "value", result)
    if val is None:
        return None
    return str(val)


def is_available(regions: Optional["config.Regions"] = None) -> Tuple[bool, str]:
    """Can we actually run the cheap stage poll on this machine right now?

    Returns (ok, reason). A False here is not fatal — TriggerEngine still runs
    and falls back to the 'periodic' safety net (and the app to
    config.FULLFRAME_FALLBACK), so the user is never worse off than v2.
    """
    regs = regions if regions is not None else config.Regions.load()
    if not regs.calibrated or "stage" not in regs.rects:
        return False, "stage region not calibrated (run python3 -m tftcoach.calibrate)"
    try:
        from tftcoach import capture as _capture  # type: ignore
    except Exception as exc:
        return False, "capture module unavailable: %s" % exc
    try:
        from tftcoach import ocr as _ocr  # type: ignore
    except Exception as exc:
        return False, "ocr module unavailable: %s" % exc
    for mod, name in ((_capture, "capture"), (_ocr, "ocr")):
        probe = getattr(mod, "is_available", None)
        if callable(probe):
            try:
                ok, why = probe()
            except Exception as exc:
                return False, "%s.is_available() raised: %s" % (name, exc)
            if not ok:
                return False, "%s: %s" % (name, why)
    return True, "ok"


def default_stage_reader(regions: Optional["config.Regions"] = None,
                         capture_fn: Optional[Callable] = None,
                         ocr_fn: Optional[Callable] = None) -> StageReader:
    """Build the real reader: crop the calibrated stage rect, OCR it.

    Everything is resolved lazily INSIDE the closure so importing triggers.py
    never requires mss/PIL/cv2/pytesseract to exist. Any failure returns None
    (unknown) instead of raising — a dead reader degrades the engine to its
    periodic safety net rather than crashing the poll thread.

    capture_fn / ocr_fn exist so tests (and a future refactor of capture.py's
    entry-point names) can inject explicitly instead of relying on the probe.
    """
    state: Dict[str, Any] = {"cap": capture_fn, "ocr": ocr_fn, "regs": regions}

    def read() -> Optional[str]:
        try:
            if state["regs"] is None:
                state["regs"] = config.Regions.load()
            regs = state["regs"]
            rect = regs.rects.get("stage")
            if not rect:
                return None
            if state["cap"] is None:
                from tftcoach import capture as _capture  # type: ignore
                # capture.capture_region is the contract; the aliases are a
                # cheap hedge, not an invitation to rename it.
                state["cap"] = _first_attr(
                    _capture, ("capture_region", "grab_region", "region"))
            if state["ocr"] is None:
                from tftcoach import ocr as _ocr  # type: ignore
                state["ocr"] = _first_attr(
                    _ocr, ("read_stage", "read_text", "ocr_text", "read_region",
                           "read_field", "ocr_image"))
            cap, run_ocr = state["cap"], state["ocr"]
            if cap is None or run_ocr is None:
                return None
            img = cap(rect)
            if img is None:
                return None
            try:
                out = run_ocr(img, "text")     # (image, kind) form
            except TypeError:
                out = run_ocr(img)             # (image,) form
            return _coerce_text(out)
        except Exception:
            return None

    return read


# =============================================================================
# TriggerEngine — threading, rate limiting, safety net
# =============================================================================

OnEvent = Callable[[Event], None]


class TriggerEngine:
    """Runs the watcher on a background thread and gates what reaches Claude.

    Rate limit: config.MIN_SECONDS_BETWEEN_CALLS applies to EVERY kind so a
    flickering OCR read can't spam the CLI. 'manual' (hotkey) bypasses it —
    the user asking is always more informative than our detector. Rounds are
    ~30s+ apart in real play, so the 20s floor almost never eats a real
    new_round; when it does, the next event still lands.
    """

    def __init__(self,
                 stage_reader: Optional[StageReader] = None,
                 poll_interval: Optional[float] = None,
                 min_gap: Optional[float] = None,
                 periodic_sec: float = DEFAULT_PERIODIC_SEC,
                 clock: Callable[[], float] = time.monotonic,
                 watcher: Optional[RoundWatcher] = None):
        self.poll_interval = (config.POLL_INTERVAL_SEC if poll_interval is None
                              else poll_interval)
        self.min_gap = (config.MIN_SECONDS_BETWEEN_CALLS if min_gap is None
                        else min_gap)
        self.periodic_sec = periodic_sec
        self._clock = clock
        self.watcher = watcher or RoundWatcher(stage_reader)

        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._inbox: "queue.Queue" = queue.Queue()   # external (manual) requests
        self._thread: Optional[threading.Thread] = None
        self._last_fire: Optional[float] = None
        # The safety net counts from engine start, not from epoch — otherwise a
        # 'periodic' fires on tick 1 with stage still unknown and then eats the
        # rate-limit budget the real first new_round needs. Callers that want
        # advice immediately on start should call trigger_manual() once.
        self._started_at = self._clock()
        self._on_event: Optional[OnEvent] = None
        self.fired = 0
        self.suppressed = 0
        self.callback_errors = 0

    # -- gating -----------------------------------------------------------
    def should_fire(self, kind: str) -> bool:
        """Read-only gate. Does NOT record the call — _dispatch does that, so
        callers can ask 'would this fire?' without side effects."""
        if kind == "manual":
            return True
        with self._lock:
            if self._last_fire is None:
                return True
            return (self._clock() - self._last_fire) >= self.min_gap

    def note_call(self, when: Optional[float] = None) -> None:
        """Record that a Claude call happened (including ones the UI made on
        its own) so the rate limit stays honest across the whole app."""
        with self._lock:
            self._last_fire = self._clock() if when is None else when

    def seconds_since_fire(self) -> Optional[float]:
        with self._lock:
            if self._last_fire is None:
                return None
            return self._clock() - self._last_fire

    # -- external triggers ------------------------------------------------
    def trigger_manual(self, note: str = "") -> None:
        """Hotkey / button. Wakes the loop immediately (no poll-interval wait)."""
        self._inbox.put(("manual", note))

    def request(self, kind: str = "manual", note: str = "") -> None:
        self._inbox.put((kind, note))

    # -- lifecycle --------------------------------------------------------
    def start(self, on_event: Optional[OnEvent] = None) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._on_event = on_event or self._on_event
            self._stop.clear()
            self._thread = threading.Thread(target=self.run,
                                            args=(self._on_event,),
                                            name="tft-triggers", daemon=True)
            self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        self._inbox.put(None)          # wake the blocking get() at once
        with self._lock:
            th = self._thread
        if th is not None and th.is_alive() and th is not threading.current_thread():
            th.join(timeout)
        with self._lock:
            self._thread = None

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    # -- the loop ---------------------------------------------------------
    def run(self, on_event: Optional[OnEvent] = None) -> None:
        """Blocking loop. Sleeps on the inbox queue, so stop() and manual
        triggers both wake it instantly and it never busy-waits."""
        cb = on_event or self._on_event
        self._stop.clear()
        with self._lock:
            self._started_at = self._clock()   # safety net counts from here
        while not self._stop.is_set():
            try:
                item = self._inbox.get(timeout=self.poll_interval)
            except queue.Empty:
                item = None
                external = False
            else:
                external = True
            if self._stop.is_set():
                break

            if external:
                if item is None:        # stop sentinel
                    break
                kind, note = item
                ev = Event(kind=kind, stage=self.watcher.current,
                           ts=self._clock(), reason="requested", note=note)
                if self.should_fire(kind):
                    self._dispatch(ev, cb)
                else:
                    self.suppressed += 1
                continue

            self.tick(cb)
        self._stop.set()

    def tick(self, on_event: Optional[OnEvent] = None) -> Optional[Event]:
        """One poll + safety-net check. Public so a caller can drive the engine
        synchronously (tests, or an app with its own loop)."""
        cb = on_event or self._on_event
        ev = self.watcher.poll()
        if ev is None:
            ev = self._periodic_due()
        if ev is None:
            return None
        ev.ts = self._clock()
        if not self.should_fire(ev.kind):
            self.suppressed += 1
            return None
        self._dispatch(ev, cb)
        return ev

    def _periodic_due(self) -> Optional[Event]:
        with self._lock:
            base = self._last_fire if self._last_fire is not None else self._started_at
        gap = self._clock() - base
        if gap < self.periodic_sec:
            return None
        return Event(kind="periodic", stage=self.watcher.current,
                     reason="safety net (%.0fs without advice)" % gap)

    def _dispatch(self, ev: Event, cb: Optional[OnEvent]) -> None:
        self.note_call(ev.ts or self._clock())
        self.fired += 1
        if cb is None:
            return
        try:
            cb(ev)
        except Exception:
            # A failing consumer must never take down the detector.
            self.callback_errors += 1


# =============================================================================
# Self-test — no screen, no deps, deterministic
# =============================================================================

def _selftest() -> None:
    def scenario(title: str, seq: List[Optional[str]]) -> List[Event]:
        print("\n--- %s ---" % title)
        w = RoundWatcher()
        out: List[Event] = []
        for i, raw in enumerate(seq, 1):
            ev = w.observe(raw)
            mark = str(ev) if ev else "-"
            print("  poll %d  read=%-9r confirmed=%-4s pending=%-4s  %s"
                  % (i, raw, w.current or "?", w.pending or "-", mark))
            if ev:
                out.append(ev)
        print("  events: %s" % ([e.kind + "@" + str(e.stage) for e in out] or "none"))
        return out

    # The sequence from the spec: repeat, advance, OCR garbage, confirm, then
    # two single sightings that (correctly) never confirm.
    scenario("spec sequence",
             ["3-1", "3-1", "3-2", "!!garbage!!", "3-2", "3-4", "4-1"])

    # Backwards noise is dropped; a real restart (4-x -> 1-1) is not.
    scenario("backwards noise + new game",
             ["4-1", "4-1", "2-3", "4-1", "4-4", "4-4", "1-1", "1-1"])

    # Engine pass: same readings, but now through the rate limiter on a fake
    # clock advancing one poll interval per tick.
    print("\n--- engine w/ rate limit (min_gap=%.0fs, poll=%.0fs) ---"
          % (config.MIN_SECONDS_BETWEEN_CALLS, config.POLL_INTERVAL_SEC))
    now = [0.0]
    seq = ["3-1", "3-1", "3-2", "!!garbage!!", "3-2", "3-4", "3-4", "4-1", "4-1"]
    it = iter(seq)
    eng = TriggerEngine(stage_reader=lambda: next(it, None),
                        clock=lambda: now[0], periodic_sec=DEFAULT_PERIODIC_SEC)
    got: List[Event] = []
    for _ in seq:
        eng.tick(got.append)
        now[0] += config.POLL_INTERVAL_SEC
    print("  delivered: %s" % [str(e) for e in got])
    print("  suppressed by rate limit: %d  (this synthetic sequence changes"
          " round every ~6s; real rounds are 30s+ apart, so the limiter only"
          " bites on flicker)" % eng.suppressed)

    # Manual bypasses the limit even one second after a fire.
    now[0] += 1.0
    print("  should_fire('new_round') right after a fire: %s"
          % eng.should_fire("new_round"))
    print("  should_fire('manual')    right after a fire: %s"
          % eng.should_fire("manual"))

    # Safety net: a totally dead reader still produces advice.
    print("\n--- periodic safety net (reader always fails) ---")
    now2 = [0.0]
    dead = TriggerEngine(stage_reader=lambda: None, clock=lambda: now2[0],
                         periodic_sec=30.0)
    fired: List[Event] = []
    for _ in range(40):
        dead.tick(fired.append)
        now2[0] += config.POLL_INTERVAL_SEC
    print("  %d periodic events over %.0fs: %s"
          % (len(fired), now2[0], [round(e.ts, 1) for e in fired]))

    # Threading: start/stop must exit promptly and manual must wake it.
    print("\n--- thread start/stop + manual wake ---")
    live = TriggerEngine(stage_reader=lambda: None, poll_interval=0.5,
                         periodic_sec=10_000.0)
    seen: List[Event] = []
    t0 = time.time()
    live.start(seen.append)
    live.trigger_manual("hotkey test")
    time.sleep(0.2)
    live.stop()
    print("  manual events: %d  running after stop: %s  stop took %.2fs"
          % (len(seen), live.running, time.time() - t0 - 0.2))

    ok, why = is_available()
    print("\nis_available(): %s (%s)" % (ok, why))


if __name__ == "__main__":
    _selftest()
