"""Cross-platform screen capture for TFT Coach Option B (macOS + Windows).

Design contract — READ THIS BEFORE USING RECTS
----------------------------------------------
Everything in this project speaks ONE coordinate space: **capture pixels**, i.e.
the pixel grid of the image returned by `capture_screen()`. regions.json stores
rects in that space together with the resolution they were calibrated at, so a
rect is always `[x, y, w, h]` in capture pixels relative to the captured
monitor's top-left.

That distinction matters because of the Retina trap: on an Apple Silicon Mac a
"1512x982" display returns a 3024x1964 frame. Backends that take *coordinates*
(mss region grabs, `screencapture -R`) want logical POINTS, not pixels, while
the frame they hand back is in pixels. `scale_factor()` measures that ratio
empirically (never assumed to be 2.0) and `capture_region()` converts for you.

Backend priority: mss -> PIL.ImageGrab -> macOS `screencapture`.
  * mss is the only backend that can grab a *sub-rectangle* cheaply, which is
    what the 2 Hz stage-region poll needs (target <50 ms). It is a listed pip
    dependency for exactly this reason.
  * PIL.ImageGrab on macOS shells out to `screencapture` internally AND, when
    given a bbox, downscales the Retina crop back to logical size (blurry, bad
    for OCR). So on macOS the PIL/screencapture backends grab the full frame and
    crop locally; on Windows the native bbox grab is used directly.

BACKENDS DISAGREE ABOUT RESOLUTION ON RETINA — measured on this Mac 2026-08-10
(mss 10.2.0, Pillow 11.3.0, 1728x1117-point display):
    mss.grab(monitors[1]) -> 1728x1117 px  (logical, 1x)   ~53 ms
    PIL.ImageGrab.grab()  -> 3456x2234 px  (physical, 2x)  ~192 ms
    screencapture -R      -> 2x the requested point rect
So the capture-pixel space depends on which backend won. Two consequences:
  1. ALWAYS reconcile saved rects against the live frame — use
     `regions_for_current_frame()` (or config.Regions.for_resolution) rather
     than trusting regions.json's numbers verbatim.
  2. On macOS mss trades OCR detail for speed (half the pixels). If small digits
     read badly, force the sharper path with TFTCOACH_CAPTURE_BACKEND=pil or
     `set_backend("pil")`; the 2 Hz poll gets slower but stays usable.

macOS permission note: capture requires Screen Recording permission for whatever
runs Python (Terminal / iTerm / VS Code) in System Settings > Privacy & Security
> Screen Recording. WITHOUT it macOS does not raise — it silently returns a
black or desktop-picture-only frame. `is_available()` / `check_capture()`
therefore grab a real frame and test for an all-black result, and report that as
a clear error instead of pretending capture worked.

Pillow is required for every backend (it is the image type we hand around);
mss only accelerates the grab. Nothing heavy is imported at module import time,
so `import tftcoach.capture` works with zero deps installed and
`is_available()` tells you what to install.
"""

from __future__ import annotations

import datetime
import math
import os
import platform
import subprocess
import tempfile
import threading
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

try:                      # normal: `python3 -m tftcoach.<mod>` / package import
    from . import config
except ImportError:       # fallback: file run directly as a script
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tftcoach import config

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from PIL import Image

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

DEFAULT_MONITOR = 1        # mss convention: 0 = all monitors, 1 = primary
KEEP_FRAMES = 40           # max frames left in CAPTURE_DIR after save_frame()
JPEG_QUALITY = 85
BLACK_LEVEL = 8            # luma <= this everywhere => "black frame"

PIL_HINT = "pip install pillow"
MSS_HINT = "pip install mss"

# Backend ids, in the order they are probed.
BACKENDS = ("mss", "pil", "screencapture")


class CaptureError(RuntimeError):
    """Capture failed in a way the caller should surface to the user."""


# --------------------------------------------------------------------------
# lazy dependency probes
# --------------------------------------------------------------------------

_lock = threading.Lock()
_tls = threading.local()          # mss objects are not thread-safe -> one each
_state: Dict[str, Any] = {
    "backend": None,              # resolved backend id
    "backend_err": "",            # why the better ones were unusable
    "scale": {},                  # monitor idx -> capture px per logical point
    "size": {},                   # monitor idx -> (w, h) in capture px
    "available": None,            # cached (ok, reason) from is_available()
}


def _pil_image():
    """PIL.Image module or raise CaptureError with an install hint."""
    try:
        from PIL import Image
        return Image
    except ImportError as exc:
        raise CaptureError("Pillow not installed (%s) -- %s" % (exc, PIL_HINT))


def _mss_module() -> Optional[Any]:
    try:
        import mss
        return mss
    except Exception:             # ImportError, or a broken platform build
        return None


def _mss_session() -> Any:
    """One mss instance per thread; they hold OS handles and are not shareable."""
    sct = getattr(_tls, "mss", None)
    if sct is None:
        mss = _mss_module()
        if mss is None:
            raise CaptureError("mss not installed -- " + MSS_HINT)
        # mss >= 10 renamed the factory to MSS and deprecates mss.mss()
        factory = getattr(mss, "MSS", None) or getattr(mss, "mss", None)
        if factory is None:
            raise CaptureError("mss installed but exposes no factory (broken build)")
        sct = factory()
        _tls.mss = sct
    return sct


def _have_screencapture() -> bool:
    return IS_MAC and os.path.exists("/usr/sbin/screencapture")


def detect_backend(force: Optional[str] = None) -> str:
    """Resolve (and cache) which backend to use. Returns its id.

    Only checks importability/presence — it does not grab, so it is cheap and
    safe to call from anywhere. Use is_available() for the real end-to-end test.
    """
    if force:
        _state["backend"] = force
        return force
    with _lock:
        if _state["backend"]:
            return str(_state["backend"])
        notes: List[str] = []
        try:
            _pil_image()
        except CaptureError as exc:
            notes.append(str(exc))
            _state["backend"] = ""
            _state["backend_err"] = "; ".join(notes)
            return ""
        if _mss_module() is not None:
            _state["backend"] = "mss"
        else:
            notes.append("mss unavailable (" + MSS_HINT + ") -- region grabs "
                         "fall back to full-frame + crop")
            grab_ok = False
            try:
                from PIL import ImageGrab
                grab_ok = hasattr(ImageGrab, "grab")
            except Exception as exc:
                notes.append("PIL.ImageGrab unusable (%s)" % exc)
            if grab_ok:
                _state["backend"] = "pil"
            elif _have_screencapture():
                _state["backend"] = "screencapture"
            else:
                _state["backend"] = ""
                notes.append("no usable backend on this platform")
        _state["backend_err"] = "; ".join(notes)
        return str(_state["backend"])


def backend_name() -> str:
    """Backend id currently in use ('' if none)."""
    return detect_backend()


def reset() -> None:
    """Drop cached backend/scale/session state (tests, or after a display change)."""
    sct = getattr(_tls, "mss", None)
    if sct is not None:
        try:
            sct.close()
        except Exception:
            pass
        _tls.mss = None
    with _lock:
        _state.update({"backend": None, "backend_err": "", "scale": {},
                       "size": {}, "available": None})


# --------------------------------------------------------------------------
# monitor geometry / scale factor
# --------------------------------------------------------------------------

def _mon_index(monitor: Optional[int]) -> int:
    return DEFAULT_MONITOR if monitor is None else int(monitor)


def _mss_monitor(idx: int) -> Dict[str, int]:
    sct = _mss_session()
    mons = sct.monitors
    if idx < 0 or idx >= len(mons):
        raise CaptureError("monitor %d does not exist (have %d)" % (idx, len(mons) - 1))
    return dict(mons[idx])


def _probe_mac_scale() -> float:
    """Ask `screencapture` for a known 100x100 point region and measure pixels."""
    if not _have_screencapture():
        return 1.0
    fh, path = tempfile.mkstemp(suffix=".png")
    os.close(fh)
    try:
        subprocess.run(["/usr/sbin/screencapture", "-x", "-t", "png",
                        "-R", "0,0,100,100", path],
                       capture_output=True, timeout=20)
        Image = _pil_image()
        with Image.open(path) as im:
            w = im.width
        return round(w / 100.0, 4) if w else 1.0
    except Exception:
        return 1.0
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def scale_factor(monitor: Optional[int] = None) -> float:
    """Capture pixels per logical point for this monitor (2.0 on Retina).

    Measured, never assumed. Needed to translate a capture-pixel rect into the
    point coordinates that mss / `screencapture -R` expect.
    """
    idx = _mon_index(monitor)
    cached = _state["scale"].get(idx)
    if cached:
        return float(cached)
    backend = detect_backend()
    scale = 1.0
    if backend == "mss":
        try:
            mon = _mss_monitor(idx)
            shot = _mss_session().grab(mon)
            if mon.get("width"):
                scale = round(shot.width / float(mon["width"]), 4) or 1.0
            _state["size"][idx] = (shot.width, shot.height)
        except Exception:
            scale = _probe_mac_scale() if IS_MAC else 1.0
    elif IS_MAC:
        scale = _probe_mac_scale()
    _state["scale"][idx] = scale
    return scale


def screen_size(monitor: Optional[int] = None) -> Tuple[int, int]:
    """(w, h) of the target monitor in CAPTURE PIXELS — the space rects live in.

    Cached; the first call may perform one grab.
    """
    idx = _mon_index(monitor)
    cached = _state["size"].get(idx)
    if cached:
        return (int(cached[0]), int(cached[1]))
    img = capture_screen(monitor=idx)
    size = (img.width, img.height)
    _state["size"][idx] = size
    return size


def logical_size(monitor: Optional[int] = None) -> Tuple[int, int]:
    """(w, h) in logical points — what the OS/Tk think the display is."""
    w, h = screen_size(monitor)
    s = scale_factor(monitor) or 1.0
    return (int(round(w / s)), int(round(h / s)))


# --------------------------------------------------------------------------
# full-frame capture
# --------------------------------------------------------------------------

def _grab_mss_full(idx: int) -> "Image.Image":
    Image = _pil_image()
    sct = _mss_session()
    mon = _mss_monitor(idx)
    shot = sct.grab(mon)
    _state["size"][idx] = (shot.width, shot.height)
    if mon.get("width"):
        _state["scale"].setdefault(idx, round(shot.width / float(mon["width"]), 4) or 1.0)
    # documented fast path: mss hands back BGRA, PIL reads it with no copy loop
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def _grab_pil_full(idx: int) -> "Image.Image":
    _pil_image()
    from PIL import ImageGrab
    kwargs: Dict[str, Any] = {}
    if IS_WIN and idx == 0:
        kwargs["all_screens"] = True     # Windows-only: whole virtual desktop
    img = ImageGrab.grab(**kwargs)
    return img.convert("RGB") if img.mode != "RGB" else img


def _grab_screencapture_full(idx: int) -> "Image.Image":
    Image = _pil_image()
    fh, path = tempfile.mkstemp(suffix=".png")
    os.close(fh)
    cmd = ["/usr/sbin/screencapture", "-x", "-t", "png"]
    if idx and idx > 1:
        cmd += ["-D", str(idx)]          # -D selects a display (1-based)
    cmd.append(path)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        if proc.returncode != 0 or not os.path.getsize(path):
            raise CaptureError("screencapture failed: %s"
                               % (proc.stderr or b"").decode("utf-8", "replace").strip()[:200])
        with Image.open(path) as im:
            im.load()
            return im.convert("RGB")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def capture_screen(monitor: Optional[int] = None) -> "Image.Image":
    """Grab the whole monitor. Returns a PIL RGB Image in CAPTURE PIXELS.

    Raises CaptureError if no backend can produce a frame.
    """
    idx = _mon_index(monitor)
    backend = detect_backend()
    if not backend:
        raise CaptureError(unavailable_reason())
    errors: List[str] = []
    order = [backend] + [b for b in BACKENDS if b != backend]
    for name in order:
        try:
            if name == "mss":
                if _mss_module() is None:
                    continue
                img = _grab_mss_full(idx)
            elif name == "pil":
                img = _grab_pil_full(idx)
            elif name == "screencapture":
                if not _have_screencapture():
                    continue
                img = _grab_screencapture_full(idx)
            else:
                continue
            if img is None or not img.width or not img.height:
                raise CaptureError("%s returned an empty frame" % name)
            _state["size"][idx] = (img.width, img.height)
            if name != backend:            # a fallback won: remember it
                _state["backend"] = name
            return img
        except Exception as exc:           # try the next backend down the list
            errors.append("%s: %s" % (name, exc))
    raise CaptureError("all capture backends failed -- " + "; ".join(errors))


# --------------------------------------------------------------------------
# region capture (the hot 2 Hz path)
# --------------------------------------------------------------------------

def _norm_rect(rect: Sequence[int]) -> Tuple[int, int, int, int]:
    if rect is None or len(rect) != 4:
        raise CaptureError("rect must be [x, y, w, h], got %r" % (rect,))
    x, y, w, h = (int(round(float(v))) for v in rect)
    if w <= 0 or h <= 0:
        raise CaptureError("rect has non-positive size: %r" % (rect,))
    return (x, y, w, h)


def clamp_rect(rect: Sequence[int], size: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Clip a capture-pixel rect into a frame of `size`. Never returns w/h < 1."""
    x, y, w, h = _norm_rect(rect)
    fw, fh = int(size[0]), int(size[1])
    x = max(0, min(x, max(0, fw - 1)))
    y = max(0, min(y, max(0, fh - 1)))
    w = max(1, min(w, fw - x))
    h = max(1, min(h, fh - y))
    return (x, y, w, h)


def crop_rect(img: "Image.Image", rect: Sequence[int]) -> "Image.Image":
    """Crop a capture-pixel rect out of an already-captured frame (clamped)."""
    x, y, w, h = clamp_rect(rect, (img.width, img.height))
    return img.crop((x, y, x + w, y + h))


def _mss_region_plan(rect: Tuple[int, int, int, int], mon: Dict[str, int],
                     scale: float) -> Tuple[Dict[str, int], Optional[Tuple[int, int, int, int]]]:
    """Capture-pixel rect -> (mss monitor dict in POINTS, exact pixel crop box).

    On a 1x display this is the identity. On Retina we round the point rect
    outward so the grab always contains the requested pixels, then crop back to
    exactly [w, h] so callers get the pixel rect they asked for.
    """
    x, y, w, h = rect
    if abs(scale - 1.0) < 1e-6:
        return ({"left": int(mon["left"] + x), "top": int(mon["top"] + y),
                 "width": int(w), "height": int(h)}, None)
    l_pt = int(math.floor(x / scale))
    t_pt = int(math.floor(y / scale))
    r_pt = int(math.ceil((x + w) / scale))
    b_pt = int(math.ceil((y + h) / scale))
    grab = {"left": int(mon["left"] + l_pt), "top": int(mon["top"] + t_pt),
            "width": max(1, r_pt - l_pt), "height": max(1, b_pt - t_pt)}
    dx = int(round(x - l_pt * scale))
    dy = int(round(y - t_pt * scale))
    return (grab, (dx, dy, dx + w, dy + h))


def capture_region(rect: Sequence[int], monitor: Optional[int] = None) -> "Image.Image":
    """Grab just `rect` ([x, y, w, h] capture pixels). Returns a PIL RGB Image.

    With mss this issues a single sub-rectangle grab (well under 50 ms) — the
    cheap poll path. Other backends grab the frame and crop, which is correct
    but slow; that is why mss is a listed dependency.
    """
    idx = _mon_index(monitor)
    r = _norm_rect(rect)
    backend = detect_backend()
    if backend == "mss":
        try:
            Image = _pil_image()
            mon = _mss_monitor(idx)
            scale = scale_factor(idx)
            grab, box = _mss_region_plan(r, mon, scale)
            shot = _mss_session().grab(grab)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            if box:
                x0, y0, x1, y1 = box
                x1 = min(x1, img.width)
                y1 = min(y1, img.height)
                x0 = max(0, min(x0, max(0, x1 - 1)))
                y0 = max(0, min(y0, max(0, y1 - 1)))
                img = img.crop((x0, y0, x1, y1))
            return img
        except Exception:
            pass  # fall through to full-frame + crop
    if IS_WIN and backend == "pil":
        # Windows GDI bbox grab is native and shares the full-grab coordinate
        # space. (Not used on macOS: Pillow downscales bbox grabs to logical
        # size there, which destroys the Retina detail OCR needs.)
        try:
            _pil_image()
            from PIL import ImageGrab
            x, y, w, h = r
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            if img.width == w and img.height == h:
                return img.convert("RGB") if img.mode != "RGB" else img
        except Exception:
            pass
    return crop_rect(capture_screen(monitor=idx), r)


def capture_regions(rects: Dict[str, Sequence[int]],
                    monitor: Optional[int] = None,
                    frame: Optional["Image.Image"] = None
                    ) -> Dict[str, "Image.Image"]:
    """Crop several named rects at once, consistently from ONE moment in time.

    Pass `frame` to reuse a frame you already have. Otherwise: <=2 rects use
    individual region grabs (cheapest); more than that, one full grab plus local
    crops beats N round trips — and guarantees every crop shows the same tick.
    """
    out: Dict[str, "Image.Image"] = {}
    if not rects:
        return out
    if frame is None and len(rects) <= 2:
        for key, rect in rects.items():
            try:
                out[key] = capture_region(rect, monitor=monitor)
            except CaptureError:
                continue
        return out
    src = frame if frame is not None else capture_screen(monitor=monitor)
    for key, rect in rects.items():
        try:
            out[key] = crop_rect(src, rect)
        except CaptureError:
            continue
    return out


# --------------------------------------------------------------------------
# frame health / availability
# --------------------------------------------------------------------------

def is_black_frame(img: "Image.Image", threshold: int = BLACK_LEVEL) -> bool:
    """True if the frame is (essentially) uniformly black.

    On macOS this is the signature of missing Screen Recording permission: the
    grab "succeeds" and returns nothing. Downsampled first so this stays cheap.
    """
    try:
        small = img.resize((32, 32))
        lo, hi = small.convert("L").getextrema()
        return hi <= threshold
    except Exception:
        return False


def permission_hint() -> str:
    if IS_MAC:
        return ("macOS returned a black frame -- grant Screen Recording to your "
                "terminal app: System Settings > Privacy & Security > Screen "
                "Recording, tick Terminal/iTerm/VS Code, then FULLY QUIT and "
                "reopen it (a reload is not enough).")
    return ("Captured frame is entirely black -- the game may be in exclusive "
            "fullscreen. Switch TFT to Borderless/Windowed.")


def check_capture(monitor: Optional[int] = None) -> Tuple[bool, str]:
    """Grab one real frame and report honestly. (ok, human-readable message)."""
    try:
        img = capture_screen(monitor=monitor)
    except CaptureError as exc:
        return (False, str(exc))
    except Exception as exc:                       # pragma: no cover
        return (False, "capture crashed: %s" % exc)
    if is_black_frame(img):
        return (False, permission_hint())
    scale = scale_factor(monitor)
    note = _state.get("backend_err") or ""
    msg = "backend=%s  frame=%dx%d px  scale=%.2fx" % (
        backend_name() or "?", img.width, img.height, scale)
    if note:
        msg += "  (note: %s)" % note
    return (True, msg)


def unavailable_reason() -> str:
    backend = detect_backend()
    if backend:
        return ""
    err = _state.get("backend_err") or ""
    return ("No screen-capture backend available. Install: %s and %s. %s"
            % (MSS_HINT, PIL_HINT, err)).strip()


def is_available(recheck: bool = False) -> Tuple[bool, str]:
    """(ok, reason) — names the winning backend, or what to install / fix.

    Performs a real grab (cached) so a macOS permission failure is reported as
    an error instead of silently yielding black frames all game.
    """
    if not recheck and _state.get("available") is not None:
        ok, reason = _state["available"]
        return (bool(ok), str(reason))
    if not detect_backend():
        result = (False, unavailable_reason())
    else:
        result = check_capture()
    _state["available"] = result
    return result


# --------------------------------------------------------------------------
# saving frames
# --------------------------------------------------------------------------

def _resample():
    Image = _pil_image()
    try:
        return Image.Resampling.LANCZOS      # Pillow >= 9.1
    except AttributeError:                   # pragma: no cover - old Pillow
        return Image.LANCZOS


def downscale(img: "Image.Image", max_width: int) -> "Image.Image":
    """Shrink to max_width if wider (token control for the vision path)."""
    if max_width and img.width > max_width:
        h = max(1, int(img.height * max_width / float(img.width)))
        return img.resize((max_width, h), _resample())
    return img


def prune_captures(keep: int = KEEP_FRAMES, directory: Optional[str] = None) -> int:
    """Keep only the `keep` newest image files at the top of CAPTURE_DIR.

    Subdirectories (e.g. calib_check/) are left alone. Returns files removed.
    """
    directory = directory or config.CAPTURE_DIR
    try:
        entries = []
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            if os.path.splitext(entry.name)[1].lower() not in (".jpg", ".jpeg", ".png"):
                continue
            try:
                entries.append((entry.stat().st_mtime, entry.path))
            except OSError:
                continue
    except OSError:
        return 0
    entries.sort(reverse=True)
    removed = 0
    for _, path in entries[max(0, int(keep)):]:
        try:
            os.unlink(path)
            removed += 1
        except OSError:
            pass
    return removed


def save_frame(img: "Image.Image", prefix: str = "cap",
               max_width: Optional[int] = None,
               keep: int = KEEP_FRAMES, quality: int = JPEG_QUALITY) -> str:
    """Write `img` to CAPTURE_DIR as JPEG, prune old frames, return the path."""
    config.ensure_dirs()
    if max_width:
        img = downscale(img, max_width)
    if img.mode != "RGB":
        img = img.convert("RGB")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    safe = "".join(c for c in (prefix or "cap") if c.isalnum() or c in "-_") or "cap"
    path = os.path.join(config.CAPTURE_DIR, "%s_%s.jpg" % (safe, stamp))
    img.save(path, "JPEG", quality=quality)
    prune_captures(keep)
    return path


def capture_and_save(prefix: str = "cap", monitor: Optional[int] = None,
                     max_width: Optional[int] = None) -> str:
    """Convenience for the whole-frame vision fallback: grab -> save -> path."""
    return save_frame(capture_screen(monitor=monitor), prefix=prefix,
                      max_width=max_width)


# --------------------------------------------------------------------------
# self-test:  python3 -m tftcoach.capture
# --------------------------------------------------------------------------

def _self_test() -> int:
    import time
    config.ensure_dirs()
    ok, reason = is_available(recheck=True)
    print("capture backend : %s" % (backend_name() or "NONE"))
    print("available       : %s -- %s" % (ok, reason))
    if not ok:
        return 1
    t0 = time.time()
    frame = capture_screen()
    full_ms = (time.time() - t0) * 1000.0
    print("full frame      : %dx%d in %.0f ms" % (frame.width, frame.height, full_ms))
    print("logical size    : %dx%d points (scale %.2fx)"
          % (logical_size() + (scale_factor(),)))
    w, h = frame.width, frame.height
    rect = [w // 4, h // 4, max(80, w // 8), max(30, h // 20)]
    times = []
    for _ in range(8):
        t0 = time.time()
        crop = capture_region(rect)
        times.append((time.time() - t0) * 1000.0)
    times.sort()
    print("region %s : median %.1f ms, best %.1f ms -> %dx%d px"
          % (rect, times[len(times) // 2], times[0], crop.width, crop.height))
    if times[len(times) // 2] > 50:
        print("  ! slower than the 50 ms poll target -- is mss installed? (%s)" % MSS_HINT)
    print("saved           : %s" % save_frame(frame, "selftest", max_width=1600))
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
