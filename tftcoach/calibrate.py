"""Interactive region calibration — run once per client / resolution.

    python3 -m tftcoach.calibrate            # draw the boxes
    python3 -m tftcoach.calibrate --verify   # crop them back out and eyeball it

Why this exists: rule #1 of Option B is that NO pixel coordinate is ever
hardcoded. Riot's HUD is not a proportional scale across resolutions, and Set 18
(Aug 26, 2026) moves TFT to Unreal, which will move the HUD again. Recalibration
must be a 5-minute chore, not a code change.

THE RETINA TRAP (handled explicitly here):
  * The captured frame is in CAPTURE PIXELS (3024x1964 on a "1512x982" Mac).
    regions.json stores rects in that space plus the resolution they came from.
  * Tk reports mouse coordinates in canvas units, and a canvas image item maps
    1 canvas unit to 1 photo pixel — but a HiDPI-aware Tk build can draw it at a
    different ratio, so instead of assuming, we MEASURE it (`canvas.bbox` of the
    image item vs the photo's own width) and store it as `tk_ratio`.
  * We also downscale the frame ourselves to fit the window (`fit_scale`).
  So: capture_pixel = canvas_unit / (tk_ratio * view_scale). Both factors are
  measured, never assumed, and --verify is the ground-truth check.

Calibrating without TFT running is allowed (it just won't be useful), a region
can always be skipped with 's', and a skipped region simply stays missing —
config.Regions.missing() reports it and the runtime falls back to whole-frame
vision for anything it lacks.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:                      # normal: `python3 -m tftcoach.calibrate`
    from . import capture, config
except ImportError:       # fallback: file run directly as a script
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tftcoach import capture, config

CHECK_DIRNAME = "calib_check"

# Per-kind coaching for the box the user is about to draw.
KIND_HINT = {
    "number": "Tight box around JUST the digits. Exclude icons, borders and the "
              "coin/XP art — OCR reads a clean crop far better.",
    "text":   "Cover the whole text area with a few pixels of padding. Include "
              "every item you want read (all shop slots / all trait rows).",
    "image":  "Cover the full area generously. This crop is sent to the vision "
              "model, so context around the units helps it.",
}

COL_BG = "#0a0a14"
COL_PANEL = "#12122a"
COL_ACCENT = "#c89b3c"
COL_TEXT = "#e2d8c0"
COL_OK = "#4ade80"
COL_DIM = "#6b6b7b"
COL_WARN = "#f87171"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _resample():
    from PIL import Image
    try:
        return Image.Resampling.LANCZOS
    except AttributeError:                      # pragma: no cover - old Pillow
        return Image.LANCZOS


def _photo_image(tk_mod: Any, pil_img: Any, master: Any) -> Any:
    """PIL image -> Tk photo. Falls back to a temp PNG if ImageTk is missing
    (some macOS Python builds ship Pillow without the Tk bindings)."""
    try:
        from PIL import ImageTk
        return ImageTk.PhotoImage(pil_img, master=master)
    except Exception:
        config.ensure_dirs()
        path = os.path.join(config.CAPTURE_DIR, "_calib_view.png")
        pil_img.save(path, "PNG")
        return tk_mod.PhotoImage(file=path, master=master)   # Tk 8.6 reads PNG


def _import_tk() -> Any:
    try:
        import tkinter as tk
        return tk
    except ImportError as exc:
        raise SystemExit(
            "tkinter is not available (%s).\n"
            "  macOS: brew install python-tk   (or use a python.org build)\n"
            "  Windows: reinstall Python with the 'tcl/tk and IDLE' option."
            % exc)


def _countdown(seconds: int, message: str) -> None:
    if seconds <= 0:
        return
    print(message)
    for remaining in range(int(seconds), 0, -1):
        sys.stdout.write("\r  capturing in %d... " % remaining)
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r  capturing now.      \n")
    sys.stdout.flush()


def _grab_frame(monitor: Optional[int], delay: int,
                image_path: Optional[str]) -> Tuple[Any, str]:
    """Return (PIL frame, description). Raises SystemExit with a clear reason."""
    if image_path:
        try:
            from PIL import Image
        except ImportError:
            raise SystemExit("Pillow is required to read an image (%s)." % capture.PIL_HINT)
        try:
            img = Image.open(image_path)
            img.load()
        except Exception as exc:
            raise SystemExit("Could not open %s: %s" % (image_path, exc))
        return (img.convert("RGB"), "file %s" % image_path)

    ok, reason = capture.is_available(recheck=True)
    print("capture: %s" % reason)
    if not ok:
        raise SystemExit("Cannot capture the screen.\n  %s" % reason)
    _countdown(delay, "\nBring TFT to the FRONT now (a planning phase is the "
                      "most useful frame to calibrate on).")
    try:
        frame = capture.capture_screen(monitor=monitor)
    except capture.CaptureError as exc:
        raise SystemExit("Capture failed: %s" % exc)
    if capture.is_black_frame(frame):
        raise SystemExit("Captured frame is entirely black.\n  %s"
                         % capture.permission_hint())
    return (frame, "live capture")


# --------------------------------------------------------------------------
# the picker window
# --------------------------------------------------------------------------

class RegionPicker:
    """Tk window that walks the user through REGION_SPECS one rect at a time.

    Selection state is stored in CAPTURE PIXELS (the source of truth); canvas
    coordinates are derived for drawing only.
    """

    def __init__(self, tk_mod: Any, frame: Any,
                 specs: Sequence[Tuple[str, str, str]],
                 seed: Optional[Dict[str, List[int]]] = None):
        self.tk = tk_mod
        self.img = frame
        self.specs = list(specs)
        self.rects: Dict[str, List[int]] = dict(seed or {})
        self.result: Optional[Dict[str, List[int]]] = None

        self.i = 0
        self.sel: Optional[List[int]] = None
        self.anchor: Optional[Tuple[float, float]] = None
        self.tk_ratio = 1.0          # canvas units per displayed photo pixel
        self.photo = None            # keep a reference or Tk garbage-collects it

        self.root = tk_mod.Tk()
        self.root.title("TFT Coach — region calibration")
        self.root.configure(bg=COL_BG)
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass

        sw = max(640, self.root.winfo_screenwidth())
        sh = max(480, self.root.winfo_screenheight())
        avail_w = max(400, sw - 60)
        avail_h = max(300, sh - 260)
        # NOTE: image dims are capture PIXELS, screen dims are logical POINTS.
        # Fitting one into the other is exactly what makes Retina work here.
        self.fit_scale = min(avail_w / float(self.img.width),
                             avail_h / float(self.img.height), 1.0)
        self.view_scale = self.fit_scale
        self.zoomed = False

        self._build_ui(min(avail_w, int(self.img.width * self.fit_scale)),
                       min(avail_h, int(self.img.height * self.fit_scale)))
        self._render()
        self._load_current()

    # -- layout ---------------------------------------------------------
    def _build_ui(self, cw: int, ch: int) -> None:
        tk = self.tk
        root = self.root
        root.geometry("%dx%d+%d+%d" % (cw + 34, ch + 196, 20, 20))

        head = tk.Frame(root, bg=COL_PANEL, pady=6)
        head.pack(fill="x")
        self.progress = tk.Label(head, text="", font=("Courier", 10, "bold"),
                                 fg=COL_ACCENT, bg=COL_PANEL)
        self.progress.pack(side="left", padx=12)
        self.done_lbl = tk.Label(head, text="", font=("Courier", 9),
                                 fg=COL_DIM, bg=COL_PANEL)
        self.done_lbl.pack(side="right", padx=12)

        self.prompt = tk.Label(root, text="", font=("Helvetica", 15, "bold"),
                               fg=COL_TEXT, bg=COL_BG, anchor="w",
                               wraplength=cw, justify="left")
        self.prompt.pack(fill="x", padx=14, pady=(8, 0))
        self.hint = tk.Label(root, text="", font=("Helvetica", 10), fg=COL_DIM,
                             bg=COL_BG, anchor="w", wraplength=cw, justify="left")
        self.hint.pack(fill="x", padx=14, pady=(2, 6))

        body = tk.Frame(root, bg=COL_BG)
        body.pack(fill="both", expand=True, padx=12)
        self.canvas = tk.Canvas(body, width=cw, height=ch, bg="#000000",
                                highlightthickness=1, highlightbackground=COL_PANEL,
                                cursor="crosshair")
        vsb = tk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        hsb = tk.Scrollbar(body, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.readout = tk.Label(root, text="", font=("Courier", 10), fg=COL_OK,
                                bg=COL_BG, anchor="w")
        self.readout.pack(fill="x", padx=14, pady=(6, 0))

        bar = tk.Frame(root, bg=COL_BG, pady=8)
        bar.pack(fill="x")
        tk.Button(bar, text="✓ Next (Enter)", command=self.accept).pack(side="left", padx=(14, 4))
        tk.Button(bar, text="Skip (s)", command=self.skip).pack(side="left", padx=4)
        tk.Button(bar, text="Clear (c)", command=self.clear).pack(side="left", padx=4)
        tk.Button(bar, text="Back (b)", command=self.back).pack(side="left", padx=4)
        self.zoom_btn = tk.Button(bar, text="Zoom 100% (z)", command=self.toggle_zoom)
        self.zoom_btn.pack(side="left", padx=4)
        tk.Button(bar, text="Save & quit (Esc)", command=self.quit_now).pack(side="right", padx=14)

        tk.Label(root, text="drag a box · arrows nudge 1px · shift+arrows resize · "
                            "wheel scrolls when zoomed",
                 font=("Courier", 8), fg=COL_DIM, bg=COL_BG).pack(fill="x", padx=14,
                                                                  pady=(0, 6))

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag)
        for seq, fn in (("<Return>", self.accept), ("<KP_Enter>", self.accept),
                        ("<Escape>", self.quit_now)):
            root.bind(seq, lambda e, f=fn: f())
        for seq, fn in (("s", self.skip), ("c", self.clear), ("b", self.back),
                        ("z", self.toggle_zoom)):
            root.bind("<KeyPress-%s>" % seq, lambda e, f=fn: f())
            root.bind("<KeyPress-%s>" % seq.upper(), lambda e, f=fn: f())
        for key, dx, dy in (("Left", -1, 0), ("Right", 1, 0),
                            ("Up", 0, -1), ("Down", 0, 1)):
            root.bind("<%s>" % key, lambda e, a=dx, b=dy: self._nudge(a, b, False))
            root.bind("<Shift-%s>" % key, lambda e, a=dx, b=dy: self._nudge(a, b, True))
        # wheel: macOS/Windows send <MouseWheel>, X11 sends Button-4/5
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Shift-MouseWheel>", lambda e: self._on_wheel(e, horiz=True))
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))
        root.protocol("WM_DELETE_WINDOW", self.quit_now)
        root.focus_force()

    # -- rendering ------------------------------------------------------
    def _render(self) -> None:
        scale = self.view_scale
        if abs(scale - 1.0) < 1e-6:
            disp = self.img
        else:
            disp = self.img.resize(
                (max(1, int(round(self.img.width * scale))),
                 max(1, int(round(self.img.height * scale)))), _resample())
        self.photo = _photo_image(self.tk, disp, self.root)
        self.canvas.delete("all")
        self.img_item = self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.root.update_idletasks()
        bbox = self.canvas.bbox(self.img_item)
        if bbox and disp.width:
            # MEASURED, not assumed: a HiDPI-aware Tk may not draw 1 photo pixel
            # per canvas unit, and every coordinate we save depends on this.
            ratio = (bbox[2] - bbox[0]) / float(disp.width)
            self.tk_ratio = ratio if ratio > 0 else 1.0
            self.canvas.config(scrollregion=bbox)
        else:
            self.tk_ratio = 1.0
            self.canvas.config(scrollregion=(0, 0, disp.width, disp.height))
        self._draw_overlays()

    def _factor(self) -> float:
        return max(1e-6, self.tk_ratio * self.view_scale)

    def _canvas_to_px(self, cx: float, cy: float) -> Tuple[float, float]:
        f = self._factor()
        return (cx / f, cy / f)

    def _px_to_canvas(self, px: float, py: float) -> Tuple[float, float]:
        f = self._factor()
        return (px * f, py * f)

    def _draw_overlays(self) -> None:
        self.canvas.delete("sel")
        self.canvas.delete("done")
        cur_key = self.specs[self.i][0] if self.specs else None
        for key, rect in self.rects.items():          # already-set rects, faint
            if key == cur_key:
                continue
            x0, y0 = self._px_to_canvas(rect[0], rect[1])
            x1, y1 = self._px_to_canvas(rect[0] + rect[2], rect[1] + rect[3])
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=COL_OK,
                                         width=1, dash=(3, 3), tags="done")
            self.canvas.create_text(x0 + 3, y0 + 7, anchor="w", text=key,
                                    fill=COL_OK, font=("Courier", 8), tags="done")
        if self.sel:
            x, y, w, h = self.sel
            x0, y0 = self._px_to_canvas(x, y)
            x1, y1 = self._px_to_canvas(x + w, y + h)
            # black underlay first so the box stays visible on any background
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#000000",
                                         width=3, tags="sel")
            self.canvas.create_rectangle(x0, y0, x1, y1, outline=COL_ACCENT,
                                         width=1, tags="sel")

    # -- step state -----------------------------------------------------
    def _load_current(self) -> None:
        key, prompt, kind = self.specs[self.i]
        self.progress.config(text="REGION %d/%d  [%s]"
                                  % (self.i + 1, len(self.specs), key))
        self.prompt.config(text=prompt)
        self.hint.config(text=KIND_HINT.get(kind, ""))
        existing = self.rects.get(key)
        self.sel = list(existing) if existing else None
        self.done_lbl.config(text="%d/%d set" % (len(self.rects), len(self.specs)))
        self._draw_overlays()
        self._update_readout()

    def _update_readout(self, msg: str = "") -> None:
        if msg:
            self.readout.config(text=msg, fg=COL_WARN)
            return
        if self.sel:
            x, y, w, h = self.sel
            self.readout.config(
                text="x=%d y=%d  w=%d h=%d  (capture pixels)" % (x, y, w, h),
                fg=COL_OK)
        else:
            self.readout.config(text="no box yet — drag one over the region, "
                                     "or press 's' to skip", fg=COL_DIM)

    # -- mouse ----------------------------------------------------------
    def _event_px(self, event: Any) -> Tuple[float, float]:
        return self._canvas_to_px(self.canvas.canvasx(event.x),
                                  self.canvas.canvasy(event.y))

    def _on_press(self, event: Any) -> None:
        self.anchor = self._event_px(event)
        self.sel = None
        self._draw_overlays()

    def _on_drag(self, event: Any) -> None:
        if self.anchor is None:
            return
        cx, cy = self._event_px(event)
        ax, ay = self.anchor
        x0, x1 = sorted((ax, cx))
        y0, y1 = sorted((ay, cy))
        self.sel = self._clamped([int(round(x0)), int(round(y0)),
                                  max(1, int(round(x1 - x0))),
                                  max(1, int(round(y1 - y0)))])
        self._draw_overlays()
        self._update_readout()

    def _on_wheel(self, event: Any, horiz: bool = False) -> None:
        delta = event.delta
        step = -1 if delta > 0 else 1
        if abs(delta) >= 120:                    # Windows reports multiples of 120
            step = int(-delta / 120)
        if horiz:
            self.canvas.xview_scroll(step, "units")
        else:
            self.canvas.yview_scroll(step, "units")

    def _clamped(self, rect: List[int]) -> List[int]:
        x, y, w, h = rect
        x = max(0, min(x, self.img.width - 1))
        y = max(0, min(y, self.img.height - 1))
        w = max(1, min(w, self.img.width - x))
        h = max(1, min(h, self.img.height - y))
        return [x, y, w, h]

    def _nudge(self, dx: int, dy: int, resize: bool) -> None:
        if not self.sel:
            return
        x, y, w, h = self.sel
        if resize:
            self.sel = self._clamped([x, y, w + dx, h + dy])
        else:
            self.sel = self._clamped([x + dx, y + dy, w, h])
        self._draw_overlays()
        self._update_readout()

    # -- actions --------------------------------------------------------
    def accept(self) -> None:
        key = self.specs[self.i][0]
        if not self.sel:
            self._update_readout("draw a box first — or press 's' to skip this one")
            return
        if self.sel[2] < 4 or self.sel[3] < 4:
            self._update_readout("that box is tiny (%dx%d px) — drag a real one"
                                 % (self.sel[2], self.sel[3]))
            return
        self.rects[key] = list(self.sel)
        self._advance()

    def skip(self) -> None:
        # leaves any previously saved rect for this key untouched
        self._advance()

    def clear(self) -> None:
        key = self.specs[self.i][0]
        self.rects.pop(key, None)
        self.sel = None
        self.anchor = None
        self.done_lbl.config(text="%d/%d set" % (len(self.rects), len(self.specs)))
        self._draw_overlays()
        self._update_readout()

    def back(self) -> None:
        if self.i > 0:
            self.i -= 1
            self.anchor = None
            self._load_current()

    def toggle_zoom(self) -> None:
        self.zoomed = not self.zoomed
        self.view_scale = 1.0 if self.zoomed else self.fit_scale
        self.zoom_btn.config(text="Fit (z)" if self.zoomed else "Zoom 100% (z)")
        self._render()
        if self.zoomed and self.sel:             # centre the view on the selection
            cx, cy = self._px_to_canvas(self.sel[0] + self.sel[2] / 2.0,
                                        self.sel[1] + self.sel[3] / 2.0)
            total_w = max(1.0, self.img.width * self._factor())
            total_h = max(1.0, self.img.height * self._factor())
            self.canvas.xview_moveto(max(0.0, (cx - self.canvas.winfo_width() / 2.0) / total_w))
            self.canvas.yview_moveto(max(0.0, (cy - self.canvas.winfo_height() / 2.0) / total_h))

    def _advance(self) -> None:
        self.anchor = None
        if self.i + 1 >= len(self.specs):
            self.result = dict(self.rects)
            self.root.destroy()
            return
        self.i += 1
        self._load_current()

    def quit_now(self) -> None:
        from tkinter import messagebox
        if self.rects:
            keep = messagebox.askyesno(
                "Quit calibration",
                "Save the %d region(s) you have already set?" % len(self.rects),
                parent=self.root)
            self.result = dict(self.rects) if keep else None
        else:
            self.result = None
        self.root.destroy()

    def run(self) -> Optional[Dict[str, List[int]]]:
        self.root.mainloop()
        return self.result


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def calibrate(monitor: Optional[int] = None, delay: int = 5,
              only: Optional[Sequence[str]] = None,
              image_path: Optional[str] = None,
              fresh: bool = False) -> int:
    """Run the interactive picker and save regions.json. Returns an exit code."""
    config.ensure_dirs()
    frame, source = _grab_frame(monitor, delay, image_path)
    width, height = frame.width, frame.height
    print("frame: %dx%d px from %s" % (width, height, source))

    specs = list(config.REGION_SPECS)
    if only:
        wanted = set(only)
        unknown = wanted - set(k for k, _, _ in config.REGION_SPECS)
        if unknown:
            print("unknown region key(s): %s" % ", ".join(sorted(unknown)))
        specs = [s for s in specs if s[0] in wanted]
        if not specs:
            print("nothing to calibrate.")
            return 1

    existing = config.Regions.load()
    seed: Dict[str, List[int]] = {}
    if existing.calibrated and not fresh:
        if list(existing.resolution) == [width, height]:
            seed = dict(existing.rects)
            print("seeded from regions.json (same resolution) — adjust or skip.")
        else:
            print("existing regions.json was calibrated at %sx%s, this frame is "
                  "%dx%d — starting fresh." % (existing.resolution[0],
                                               existing.resolution[1], width, height))

    tk_mod = _import_tk()
    try:
        picker = RegionPicker(tk_mod, frame, specs, seed)
    except Exception as exc:
        print("could not open the calibration window: %s" % exc)
        return 1
    rects = picker.run()
    if rects is None:
        print("cancelled — regions.json untouched.")
        return 1

    merged = dict(seed)
    merged.update(rects)
    regions = config.Regions(merged, [width, height])
    regions.save()

    print("\nsaved %s  (resolution %dx%d)" % (config.REGIONS_PATH, width, height))
    for key, _, kind in config.REGION_SPECS:
        rect = merged.get(key)
        print("  %-7s %-6s %s" % (key, kind, rect if rect else "-- not set --"))
    missing = regions.missing()
    if missing:
        print("\nstill missing: %s" % ", ".join(missing))
        print("  (missing regions fall back to whole-frame vision at runtime)")
    print("\nnext: python3 -m tftcoach.calibrate --verify")
    return 0


def verify(monitor: Optional[int] = None, image_path: Optional[str] = None) -> int:
    """Re-crop every saved region from a live frame so the user can eyeball it."""
    config.ensure_dirs()
    regions = config.Regions.load()
    if not regions.calibrated:
        print("regions.json has no rects yet — run: python3 -m tftcoach.calibrate")
        return 1
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow is required (%s)." % capture.PIL_HINT)
        return 2

    if image_path:
        frame, source = _grab_frame(monitor, 0, image_path)
    else:
        ok, reason = capture.is_available(recheck=True)
        print("capture: %s" % reason)
        if not ok:
            return 2
        frame = capture.capture_screen(monitor=monitor)
        source = "live capture"
        if capture.is_black_frame(frame):
            print(capture.permission_hint())
            return 2

    width, height = frame.width, frame.height
    rects = regions.for_resolution(width, height)
    if list(regions.resolution) != [width, height]:
        print("! calibrated at %sx%s but this frame is %dx%d — rects were scaled "
              "proportionally, which Riot's HUD does NOT strictly follow. If the "
              "crops below look off, recalibrate at this resolution."
              % (regions.resolution[0], regions.resolution[1], width, height))

    out_dir = os.path.join(config.CAPTURE_DIR, CHECK_DIRNAME)
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):              # clear stale crops
        if name.lower().endswith(".png"):
            try:
                os.unlink(os.path.join(out_dir, name))
            except OSError:
                pass

    overview = frame.copy()
    draw = ImageDraw.Draw(overview)
    line_w = max(2, width // 700)
    order = [k for k, _, _ in config.REGION_SPECS if k in rects]
    order += [k for k in sorted(rects) if k not in order]

    print("\nregion crops from %s (%dx%d):" % (source, width, height))
    for key in order:
        rect = rects[key]
        try:
            clamped = capture.clamp_rect(rect, (width, height))
        except capture.CaptureError as exc:
            print("  %-7s BAD RECT %s (%s)" % (key, rect, exc))
            continue
        x, y, w, h = clamped
        crop = frame.crop((x, y, x + w, y + h))
        path = os.path.join(out_dir, "%s.png" % key)
        crop.save(path, "PNG")
        flag = ""
        if list(clamped) != list(rect):
            flag = " (clamped into frame)"
        if capture.is_black_frame(crop):
            flag += " ** all black — wrong spot, or the HUD is hidden **"
        print("  %-7s %-22s -> %s%s" % (key, str(clamped), os.path.basename(path), flag))
        draw.rectangle([x, y, x + w, y + h], outline=(200, 155, 60), width=line_w)
        draw.text((x + line_w + 2, max(0, y - 12 * line_w)), key, fill=(255, 255, 255))

    ov_path = os.path.join(out_dir, "_overview.png")
    capture.downscale(overview, 1600).save(ov_path, "PNG")
    missing = regions.missing()
    if missing:
        print("\nnot calibrated: %s" % ", ".join(missing))
    print("\nopen these and check each box: %s" % out_dir)
    if capture.IS_MAC:
        print("  open '%s'" % out_dir)
    print("  _overview.png shows every rect drawn on the full frame.")
    print("anything wrong -> python3 -m tftcoach.calibrate --only <key>")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m tftcoach.calibrate",
        description="Calibrate TFT HUD regions (no coordinate is ever hardcoded).")
    parser.add_argument("--verify", action="store_true",
                        help="re-crop the saved regions from a live frame into "
                             ".captures/%s/ for eyeballing" % CHECK_DIRNAME)
    parser.add_argument("--monitor", type=int, default=None,
                        help="monitor index (mss convention: 1 = primary)")
    parser.add_argument("--delay", type=int, default=5,
                        help="countdown seconds before the grab (default 5)")
    parser.add_argument("--only", default="",
                        help="comma-separated region keys to (re)calibrate")
    parser.add_argument("--image", default=None,
                        help="calibrate from an existing full-screen image "
                             "instead of grabbing one")
    parser.add_argument("--fresh", action="store_true",
                        help="ignore the saved rects instead of seeding from them")
    args = parser.parse_args(list(argv) if argv is not None else None)

    only = [k.strip() for k in args.only.split(",") if k.strip()]
    if args.verify:
        return verify(monitor=args.monitor, image_path=args.image)
    return calibrate(monitor=args.monitor, delay=args.delay, only=only,
                     image_path=args.image, fresh=args.fresh)


if __name__ == "__main__":
    raise SystemExit(main())
