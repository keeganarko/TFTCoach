"""Local structured extraction for TFT Coach Option B.

This is the cheap, deterministic half of the pipeline: crop the calibrated HUD
regions out of a frame we already captured and read exact numbers from them with
tesseract. No network, no tokens, no guessing. Anything OCR cannot read stays
Field(value=None, confidence=0.0) so the coach prompt can say "unknown" out loud
instead of inventing a number.

Design constraints this module obeys (see the project rules):
  * no pixel coordinates here — every rect comes from config.Regions
  * imports cleanly with every heavy dep missing (all of them are lazy);
    call is_available() to find out whether reads will actually work
  * nothing raises: a missing region, a dead binary or a garbage read all
    degrade to unknown
  * champion/trait names are only trusted after validation against the
    CommunityDragon whitelist (tftcoach.entities); unvalidated reads are kept
    for debugging but held below state.MIN_CONFIDENCE so .known stays False

Python 3.9 compatible: no match statements, no PEP 604 runtime unions.
"""

from __future__ import annotations

import math
import os
import platform
import re
import shutil
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import OCR_FIELDS, REGION_SPECS, VISION_FIELDS, Regions, ensure_dirs
from .state import Field, GameState

# --- tunables ---------------------------------------------------------------

# Per-field plausibility windows. A read outside its window is a misread, not a
# fact, so it becomes unknown. Deliberately generous (TFT tops out at level 10,
# 11 exists via mechanics) — these are sanity checks, not game rules.
SANITY_RANGES: Dict[str, Tuple[int, int]] = {
    "gold": (0, 999),
    "level": (1, 11),
    "hp": (0, 100),
}

# UI constant, not a set-specific entity: the shop bar has held 5 slots for
# years. Bump it if Riot changes it; nothing else depends on the number.
MAX_SHOP_SLOTS = 5
MAX_TRAITS = 12

# Tesseract likes text roughly 30-60px tall; HUD crops are far smaller.
MIN_OCR_TEXT_HEIGHT = 56
MAX_UPSCALE = 4
OCR_TIMEOUT_SEC = 10

# Confidence ceiling for a name we could not validate against CommunityDragon.
# Below state.MIN_CONFIDENCE on purpose: visible in the timeline, never trusted.
UNVALIDATED_NAME_CAP = 0.40

# Characters we allow to survive a free-text read. Set-agnostic character
# classes only (apostrophes, periods, ampersands appear in champion names) —
# never a name list.
_TEXT_KEEP = re.compile(r"[^A-Za-z'&.\- ]+")

_AVAIL_CACHE: Optional[Tuple[bool, str]] = None


# --- lazy dependency plumbing ----------------------------------------------
# Every heavy import lives inside a function so `import tftcoach.ocr` works on a
# machine where setup_optionb.sh has not run yet.

def _numpy():
    import numpy  # noqa: WPS433 (lazy on purpose)
    return numpy


def _pil_image():
    from PIL import Image  # noqa: WPS433
    return Image


def _cv2():
    """OpenCV is optional — it only makes preprocessing faster/nicer."""
    try:
        import cv2  # noqa: WPS433
        return cv2
    except Exception:
        return None


def _pytesseract():
    import pytesseract  # noqa: WPS433
    return pytesseract


def _tesseract_hint() -> str:
    system = platform.system()
    if system == "Darwin":
        return "tesseract binary not found — run: brew install tesseract"
    if system == "Windows":
        return ("tesseract binary not found — run: choco install tesseract "
                "(or install the UB-Mannheim build and add it to PATH)")
    return "tesseract binary not found — install it (e.g. apt install tesseract-ocr)"


def _locate_tesseract() -> Optional[str]:
    """Find the binary and tell pytesseract about it. Windows installers
    routinely skip PATH, so probe the standard install dirs too."""
    env = os.environ.get("TESSERACT_CMD")
    if env and os.path.exists(env):
        return env
    found = shutil.which("tesseract")
    if found:
        return found
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def backend_name() -> str:
    return "pytesseract+tesseract"


def is_available(refresh: bool = False) -> Tuple[bool, str]:
    """(usable, reason). The reason string is user-facing: it names the exact
    install command for this platform."""
    global _AVAIL_CACHE
    if _AVAIL_CACHE is not None and not refresh:
        return _AVAIL_CACHE

    result: Tuple[bool, str]
    try:
        _numpy()
    except Exception:
        result = (False, "numpy not installed — run: pip3 install numpy")
        _AVAIL_CACHE = result
        return result
    try:
        _pil_image()
    except Exception:
        result = (False, "Pillow not installed — run: pip3 install pillow")
        _AVAIL_CACHE = result
        return result
    try:
        pytesseract = _pytesseract()
    except Exception:
        result = (False, "pytesseract not installed — run: pip3 install pytesseract")
        _AVAIL_CACHE = result
        return result

    binary = _locate_tesseract()
    if not binary:
        result = (False, _tesseract_hint())
        _AVAIL_CACHE = result
        return result
    try:
        pytesseract.pytesseract.tesseract_cmd = binary
        version = str(pytesseract.get_tesseract_version()).split()[0]
        result = (True, "tesseract %s via pytesseract (%s)" % (version, binary))
    except Exception as exc:  # binary present but broken / wrong arch
        result = (False, "tesseract found at %s but failed to run (%s). %s"
                  % (binary, exc, _tesseract_hint()))
    _AVAIL_CACHE = result
    return result


# --- image helpers ----------------------------------------------------------

def frame_size(frame: Any) -> Tuple[int, int]:
    """(width, height) for a numpy frame or a PIL Image. (0, 0) if unknown."""
    try:
        shape = getattr(frame, "shape", None)
        if shape is not None and len(shape) >= 2:
            return int(shape[1]), int(shape[0])
        size = getattr(frame, "size", None)
        if isinstance(size, tuple) and len(size) == 2:
            return int(size[0]), int(size[1])
    except Exception:
        pass
    return (0, 0)


def _as_array(img: Any):
    """Coerce PIL Image / numpy array to a numpy array. None on failure."""
    try:
        np = _numpy()
    except Exception:
        return None
    if img is None:
        return None
    if hasattr(img, "shape"):
        return img
    try:
        return np.asarray(img)
    except Exception:
        return None


def _to_gray(img: Any):
    """Single-channel uint8. Channel order is deliberately ignored: mss hands us
    BGRA, PIL hands us RGB, and for light HUD glyphs the plain channel mean is
    just as separable as a luma weighting while being order-agnostic."""
    np = _numpy()
    arr = _as_array(img)
    if arr is None:
        return None
    if arr.ndim == 3:
        if arr.shape[2] >= 4:
            arr = arr[:, :, :3]
        arr = arr.mean(axis=2)
    elif arr.ndim != 2:
        return None
    return np.clip(arr, 0, 255).astype(np.uint8)


def _upscale_factor(height: int) -> int:
    if height <= 0:
        return 1
    if height >= MIN_OCR_TEXT_HEIGHT * 2:
        return 1
    return max(2, min(MAX_UPSCALE, int(math.ceil(float(MIN_OCR_TEXT_HEIGHT) / height))))


def _resize(gray, factor: int):
    if factor <= 1:
        return gray
    cv2 = _cv2()
    h, w = gray.shape[:2]
    if cv2 is not None:
        return cv2.resize(gray, (w * factor, h * factor), interpolation=cv2.INTER_CUBIC)
    try:
        Image = _pil_image()
        np = _numpy()
        pil = Image.fromarray(gray).resize((w * factor, h * factor), Image.BICUBIC)
        return np.asarray(pil)
    except Exception:
        np = _numpy()
        return np.repeat(np.repeat(gray, factor, axis=0), factor, axis=1)


def _stretch(gray):
    """Percentile contrast stretch. TFT HUD text sits on animated, low-contrast
    backdrops; without this the Otsu split lands in the wrong place."""
    np = _numpy()
    lo = float(np.percentile(gray, 2))
    hi = float(np.percentile(gray, 98))
    if hi - lo < 8.0:      # near-flat crop: nothing to stretch
        return gray
    out = (gray.astype(np.float32) - lo) * (255.0 / (hi - lo))
    return np.clip(out, 0, 255).astype(np.uint8)


def _otsu_threshold(gray) -> int:
    """Otsu without OpenCV, so preprocessing still works on a cv2-less box."""
    np = _numpy()
    hist = np.bincount(gray.reshape(-1), minlength=256).astype(np.float64)
    total = hist.sum()
    if total <= 0:
        return 127
    p = hist / total
    idx = np.arange(256, dtype=np.float64)
    w0 = np.cumsum(p)
    m = np.cumsum(p * idx)
    m_t = m[-1]
    denom = w0 * (1.0 - w0)
    denom[denom <= 0] = 1e-9
    sigma_b = ((m_t * w0 - m) ** 2) / denom
    return int(np.argmax(sigma_b))


def _binarize(gray):
    cv2 = _cv2()
    if cv2 is not None:
        try:
            _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return out
        except Exception:
            pass
    np = _numpy()
    t = _otsu_threshold(gray)
    return np.where(gray > t, np.uint8(255), np.uint8(0))


def _pad(binary, border: int = 12):
    """Tesseract wants a quiet margin. Pad with whatever value dominates the
    image (that is the background, whichever polarity we ended up in)."""
    np = _numpy()
    counts = np.bincount(binary.reshape(-1), minlength=256)
    fill = int(np.argmax(counts))
    return np.pad(binary, border, mode="constant", constant_values=fill)


def preprocess(img: Any, kind: str = "text", invert: bool = True) -> Any:
    """Crop -> OCR-ready bitmap. Returns None if it cannot be done.

    kind is a config.REGION_SPECS kind ("number" | "text" | "image") and only
    tunes the upscale target. invert=True assumes the TFT default of LIGHT text
    on a DARK/busy background and flips it so tesseract sees dark-on-light;
    callers run both polarities and keep the better read, because a few HUD
    elements (tooltips, carousel banners) are the other way round.
    """
    try:
        gray = _to_gray(img)
        if gray is None or gray.size == 0:
            return None
        h = gray.shape[0]
        factor = _upscale_factor(h)
        if kind == "number":
            factor = max(factor, 2)   # digits are the smallest glyphs on screen
        gray = _resize(gray, factor)
        gray = _stretch(gray)
        binary = _binarize(gray)
        if invert:
            binary = 255 - binary
        return _pad(binary)
    except Exception:
        return None


def crop(frame: Any, rect: Sequence[int]) -> Optional[Any]:
    """Crop [x, y, w, h] out of a frame, clamped to bounds. None if degenerate."""
    try:
        arr = _as_array(frame)
        if arr is None or getattr(arr, "ndim", 0) < 2:
            return None
        fh, fw = arr.shape[0], arr.shape[1]
        x, y, w, h = (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        x0 = max(0, min(x, fw - 1))
        y0 = max(0, min(y, fh - 1))
        x1 = max(x0 + 1, min(x + w, fw))
        y1 = max(y0 + 1, min(y + h, fh))
        if x1 - x0 < 3 or y1 - y0 < 3:
            return None
        return arr[y0:y1, x0:x1]
    except Exception:
        return None


# --- raw tesseract calls ----------------------------------------------------

def _ocr_words(binary: Any, config: str) -> Tuple[List[str], float]:
    """(words, confidence 0-1). Confidence is tesseract's own per-word conf from
    image_to_data, averaged over words that produced characters — an honest
    signal, unlike a bare image_to_string which tells us nothing.

    Words are kept SEPARATE rather than pre-joined: tesseract's word boundaries
    are the only reliable split for a shop bar or trait list, and joining first
    then re-splitting on whitespace throws that information away.
    """
    ok, _reason = is_available()
    if not ok or binary is None:
        return ([], 0.0)
    try:
        pytesseract = _pytesseract()
        Image = _pil_image()
        pil = Image.fromarray(binary)
        kwargs = {"config": config, "output_type": pytesseract.Output.DICT}
        try:
            data = pytesseract.image_to_data(pil, timeout=OCR_TIMEOUT_SEC, **kwargs)
        except TypeError:      # older pytesseract without timeout support
            data = pytesseract.image_to_data(pil, **kwargs)
    except Exception:
        return ([], 0.0)

    words: List[str] = []
    confs: List[float] = []
    try:
        texts = data.get("text", [])
        raw_confs = data.get("conf", [])
        for i, word in enumerate(texts):
            word = (word or "").strip()
            if not word:
                continue
            try:
                c = float(raw_confs[i])
            except (IndexError, TypeError, ValueError):
                c = -1.0
            if c < 0:
                continue
            words.append(word)
            confs.append(c)
    except Exception:
        return ([], 0.0)
    if not words:
        return ([], 0.0)
    conf = max(0.0, min(1.0, sum(confs) / (100.0 * len(confs))))
    return (words, conf)


def _variants(img: Any, kind: str, configs: Sequence[str]
              ) -> List[Tuple[List[str], float]]:
    """Every (polarity x config) read of one crop.

    Both polarities are always tried: TFT HUD text is light-on-dark, but
    tooltips, the carousel banner and some overlays invert that, and which one
    wins is not knowable up front. Multiple psm modes are tried because psm 7
    ("one line") silently returns nothing on some single-digit crops while
    psm 8 ("one word") reads them fine.
    """
    out: List[Tuple[List[str], float]] = []
    for invert in (True, False):
        binary = preprocess(img, kind, invert=invert)
        if binary is None:
            continue
        for config in configs:
            words, conf = _ocr_words(binary, config)
            if words:
                out.append((words, conf))
    return out


def _consensus(candidates: List[Tuple[Any, float]]) -> Tuple[Optional[Any], float]:
    """Pick the best-confidence candidate and DISCOUNT it when another variant
    read something different.

    This is the guard against confidently-wrong digits: a clean glyph reads the
    same under every polarity/psm, while a misread ("52" -> "92" one way, "520"
    the other) produces rivals. The discount scales with how credible the rival
    was, so a strong read barely dented by a junk rival survives, and a coin-flip
    lands under state.MIN_CONFIDENCE and is reported as unknown.
    """
    if not candidates:
        return (None, 0.0)
    ranked = sorted(candidates, key=lambda c: -c[1])
    value, conf = ranked[0]
    if conf <= 0:
        return (None, 0.0)
    rival = next((c for c in ranked if c[0] != value), None)
    if rival is not None:
        factor = 1.0 - 0.5 * (rival[1] / conf)
        conf = conf * max(0.3, min(1.0, factor))
    return (value, max(0.0, min(1.0, conf)))


# psm 7 = single text line, psm 8 = single word, psm 6 = uniform block,
# psm 11 = sparse text.
# NOTE: pytesseract splits `config` on whitespace, so a whitelist can never
# contain a space. That is why free text is filtered in Python instead.
_CFG_DIGITS = ["--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789",
               "--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789"]
# The stage separator is a thin glyph tesseract drops or mangles, so one config
# whitelists it and one runs unrestricted to catch whatever it became.
_CFG_STAGE = ["--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789-",
              "--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789-",
              "--oem 3 --psm 7"]

# Everything OCR turns a stage separator into.
_SEP_CHARS = r"\s~_\-–—=:;.,·•|/\\'\"^"


def read_number(img: Any, value_range: Optional[Tuple[int, int]] = None
                ) -> Tuple[Optional[int], float]:
    """Digits only. Returns (None, 0.0) on anything implausible — the caller
    passes the sanity window (gold 0-999, level 1-11, hp 0-100)."""
    try:
        candidates: List[Tuple[Any, float]] = []
        for words, conf in _variants(img, "number", _CFG_DIGITS):
            digits = re.sub(r"\D", "", "".join(words))
            if not digits or len(digits) > 4:   # runaway read, not a HUD number
                continue
            candidates.append((int(digits), conf))
        value, conf = _consensus(candidates)
        if value is None:
            return (None, 0.0)
        if value_range is not None:
            lo, hi = value_range
            if value < lo or value > hi:
                return (None, 0.0)
        return (int(value), conf)
    except Exception:
        return (None, 0.0)


def read_text(img: Any, psm: int = 7) -> Tuple[str, float]:
    """General text. psm 7 for one line, 11 for sparse/multi-item regions."""
    words, conf = read_words(img, psm=psm)
    return (" ".join(words), conf) if words else ("", 0.0)


def read_words(img: Any, psm: int = 7) -> Tuple[List[str], float]:
    """Like read_text but keeps tesseract's word split, which is what the shop
    and trait readers need in order to tell two names apart."""
    try:
        variants = _variants(img, "text", ["--oem 3 --psm %d" % int(psm)])
        best_words: List[str] = []
        best_conf = 0.0
        for words, conf in variants:
            cleaned = [w for w in (_clean_word(w) for w in words) if w]
            if cleaned and conf > best_conf:
                best_words, best_conf = cleaned, conf
        return (best_words, best_conf)
    except Exception:
        return ([], 0.0)


def _clean_word(word: str) -> str:
    return _TEXT_KEEP.sub("", word or "").strip()


def _parse_stage(raw: str) -> Optional[str]:
    """"3-2" out of whatever tesseract produced, or None."""
    if not raw:
        return None
    norm = re.sub("[" + _SEP_CHARS + "]+", "-", raw).strip("-")
    match = re.search(r"(\d)-+(\d)", norm)
    if match:
        stage, rnd = int(match.group(1)), int(match.group(2))
    else:
        digits = re.sub(r"\D", "", raw)
        if len(digits) != 2:      # only unambiguous when exactly two digits
            return None
        stage, rnd = int(digits[0]), int(digits[1])
    if not (1 <= stage <= 7 and 1 <= rnd <= 7):
        return None
    return "%d-%d" % (stage, rnd)


def read_stage(img: Any) -> Tuple[Optional[str], float]:
    """Parse the "N-M" stage indicator, tolerating the usual OCR noise.

    Accepts "3-2", "3 2", "3~2" and a bare "32" when both digits are in range,
    since the separator is a thin glyph tesseract drops constantly. Validates
    stage 1-7 and round 1-7; anything else is a misread, not a stage.
    """
    try:
        candidates: List[Tuple[Any, float]] = []
        for words, conf in _variants(img, "text", _CFG_STAGE):
            parsed = _parse_stage(" ".join(words))
            if parsed:
                candidates.append((parsed, conf))
        value, conf = _consensus(candidates)
        return (value, conf) if value else (None, 0.0)
    except Exception:
        return (None, 0.0)


# --- entity validation adapters --------------------------------------------
# tftcoach.entities is a sibling module; these adapters tolerate a couple of
# plausible signatures so a small API difference degrades to "unvalidated"
# instead of crashing the tick.

def _normalize_match(result: Any) -> Tuple[Optional[str], float]:
    try:
        if result is None:
            return (None, 0.0)
        if isinstance(result, str):
            return (result, 1.0) if result else (None, 0.0)
        if isinstance(result, dict):
            name = result.get("name") or result.get("value")
            score = result.get("score", result.get("confidence", 1.0))
            return _normalize_match((name, score)) if name else (None, 0.0)
        if isinstance(result, (tuple, list)) and result:
            name = result[0]
            score = result[1] if len(result) > 1 else 1.0
            if not isinstance(name, str) or not name:
                return (None, 0.0)
            try:
                score = float(score)
            except (TypeError, ValueError):
                score = 1.0
            if score > 1.0:            # some matchers report 0-100
                score = score / 100.0
            return (name, max(0.0, min(1.0, score)))
    except Exception:
        pass
    return (None, 0.0)


def _call_variants(fn, raw: str, kind: Optional[str]) -> Any:
    attempts = []
    if kind:
        attempts.append(((raw, kind), {}))
        attempts.append(((raw,), {"kind": kind}))
    attempts.append(((raw,), {}))
    for args, kwargs in attempts:
        try:
            return fn(*args, **kwargs)
        except TypeError:
            continue
        except Exception:
            return None
    return None


def match_name(entities: Any, raw: str, kind: str = "champion"
               ) -> Tuple[Optional[str], float]:
    """Validate one OCR'd name against the CommunityDragon whitelist."""
    if entities is None or not raw:
        return (None, 0.0)
    fn = getattr(entities, "match_name", None)
    if fn is None:
        return (None, 0.0)
    return _normalize_match(_call_variants(fn, raw, kind))


def match_shop_line(entities: Any, raw: str) -> List[Tuple[str, float]]:
    """Validate a whole OCR'd shop bar. Returns [(name, score), ...]."""
    if entities is None or not raw:
        return []
    fn = getattr(entities, "match_shop_line", None)
    if fn is None:
        return []
    result = _call_variants(fn, raw, None)
    out: List[Tuple[str, float]] = []
    if result is None:
        return out
    if isinstance(result, str):
        name, score = _normalize_match(result)
        return [(name, score)] if name else []
    try:
        for item in result:
            name, score = _normalize_match(item)
            if name:
                out.append((name, score))
    except TypeError:
        return []
    return out


def _match_words(entities: Any, words: List[str], kind: str
                 ) -> List[Tuple[str, float]]:
    """Greedy left-to-right validation over OCR words.

    Bigrams are tried before unigrams because plenty of champions and traits are
    two words; the pair only wins if it matches at least as well as the single
    word, so a false pairing cannot swallow a good solo match.
    """
    pairs: List[Tuple[str, float]] = []
    i = 0
    while i < len(words):
        uni_name, uni_score = match_name(entities, words[i], kind)
        bi_name, bi_score = (None, 0.0)
        if i + 1 < len(words):
            bi_name, bi_score = match_name(
                entities, words[i] + " " + words[i + 1], kind)
        if bi_name and bi_score >= uni_score:
            pairs.append((bi_name, bi_score))
            i += 2
        elif uni_name:
            pairs.append((uni_name, uni_score))
            i += 1
        else:
            i += 1
    return pairs


def _plausible_token(word: str) -> bool:
    """Filter for the unvalidated fallback: keep things that look like a name,
    drop the letter-soup a noisy crop produces."""
    word = (word or "").strip()
    if len(word) < 3 or len(word) > 20:
        return False
    letters = sum(1 for c in word if c.isalpha())
    return letters >= 3 and letters >= 0.7 * len(word)


def _dedupe(pairs: List[Tuple[str, float]], limit: int) -> List[Tuple[str, float]]:
    seen = set()
    out: List[Tuple[str, float]] = []
    for name, score in pairs:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((name, score))
        if len(out) >= limit:
            break
    return out


# --- region readers ---------------------------------------------------------

def read_shop(img: Any, entities: Any = None) -> Tuple[List[str], float]:
    """Champion names in the shop bar, validated. Confidence blends tesseract's
    own conf with the fuzzy-match score; an unvalidated read is capped below
    state.MIN_CONFIDENCE so it shows up in the timeline but is never trusted."""
    best: List[Tuple[str, float]] = []
    best_conf = 0.0
    best_words: List[str] = []
    fallback_conf = 0.0
    # psm 6 reads the bar as a block, 11 as scattered text, 7 as one line —
    # which one wins depends on card spacing at this resolution.
    for psm in (6, 11, 7):
        words, conf = read_words(img, psm=psm)
        if not words:
            continue
        if conf > fallback_conf:
            best_words, fallback_conf = words, conf
        matched = match_shop_line(entities, " ".join(words))
        if not matched:
            matched = _match_words(entities, words, "champion")
        if sum(s for _n, s in matched) > sum(s for _n, s in best):
            best, best_conf = matched, conf
    if best:
        names = _dedupe(best, MAX_SHOP_SLOTS)
        avg_match = sum(s for _n, s in names) / float(len(names))
        return ([n for n, _s in names], max(0.0, min(1.0, best_conf * avg_match)))
    tokens = [w for w in best_words if _plausible_token(w)]
    if tokens:
        # Unvalidated: visible in the timeline for debugging, but capped below
        # state.MIN_CONFIDENCE so no downstream prompt ever treats it as fact.
        return (tokens[:MAX_SHOP_SLOTS], min(UNVALIDATED_NAME_CAP, fallback_conf))
    return ([], 0.0)


def read_traits(img: Any, entities: Any = None) -> Tuple[List[str], float]:
    """Active trait names from the synergy panel, validated the same way."""
    words, conf = read_words(img, psm=11)
    if not words:
        words, conf = read_words(img, psm=6)
    if not words:
        return ([], 0.0)
    pairs = _match_words(entities, words, "trait")
    if pairs:
        names = _dedupe(pairs, MAX_TRAITS)
        avg_match = sum(s for _n, s in names) / float(len(names))
        return ([n for n, _s in names], max(0.0, min(1.0, conf * avg_match)))
    tokens = [w for w in words if _plausible_token(w)]
    if tokens:
        return (tokens[:MAX_TRAITS], min(UNVALIDATED_NAME_CAP, conf))
    return ([], 0.0)


def rects_for_frame(regions: Any, frame: Any) -> Dict[str, List[int]]:
    """Resolve the calibrated rects against this frame's actual resolution.
    Accepts a config.Regions, a raw {key: rect} dict, or a loaded regions.json
    dict. Never raises."""
    if regions is None:
        return {}
    try:
        width, height = frame_size(frame)
        if hasattr(regions, "for_resolution") and width and height:
            return dict(regions.for_resolution(width, height))
        if hasattr(regions, "rects"):
            return dict(regions.rects)
        if isinstance(regions, dict):
            if "rects" in regions and isinstance(regions["rects"], dict):
                return dict(regions["rects"])
            return dict(regions)
    except Exception:
        pass
    return {}


def _guess_screen(state: GameState, shop_known: bool) -> str:
    """Cheap screen-phase heuristic — this is a GUESS, not a detection.

    The shop bar is only drawn during planning, so a readable shop is decent
    evidence of planning; a readable stage with an unreadable shop is usually
    combat. It will be wrong on augment/carousel screens (which also hide the
    shop) and during the shop's fade animation. Downstream code must treat
    screen as a hint, never as a fact; a real detector would need a dedicated
    calibrated marker region.
    """
    if shop_known:
        return "planning"
    if state.stage.known:
        return "combat"
    return "unknown"


def extract_state(frame: Any, regions: Any, entities: Any = None,
                  frame_path: Optional[str] = None) -> GameState:
    """MAIN ENTRY POINT. Read every OCR-able calibrated region out of an
    already-captured full frame and return a GameState.

    Fields in config.VISION_FIELDS (board/bench) are intentionally left unknown
    here — the coach module sends those crops to the vision model. Fields with
    no calibrated region (e.g. streak, augments, which REGION_SPECS does not
    cover) also stay unknown. Nothing in here raises.
    """
    state = GameState()
    if frame_path:
        state.raw_capture = frame_path

    ok, _reason = is_available()
    rects = rects_for_frame(regions, frame)
    if not ok or not rects or frame is None:
        return state   # everything unknown; caller falls back to full-frame vision

    shop_known = False
    for key, _prompt, kind in REGION_SPECS:
        if key in VISION_FIELDS or key not in OCR_FIELDS:
            continue
        if not hasattr(state, key):
            continue
        rect = rects.get(key)
        if not rect or len(rect) < 4:
            continue
        img = crop(frame, rect)
        if img is None:
            continue

        try:
            if key == "stage":
                value, conf = read_stage(img)
            elif key == "shop":
                names, conf = read_shop(img, entities)
                value = names or None
            elif key == "traits":
                names, conf = read_traits(img, entities)
                value = names or None
            elif kind == "number":
                value, conf = read_number(img, SANITY_RANGES.get(key))
            else:
                text, conf = read_text(img)
                value = text or None
        except Exception:
            value, conf = None, 0.0

        if value is None:
            continue
        setattr(state, key, Field(value=value, confidence=conf, source="ocr"))
        if key == "shop":
            shop_known = getattr(state, key).known

    # Heuristic only — see _guess_screen's docstring.
    state.screen = _guess_screen(state, shop_known)
    return state


# --- debug / calibration aids ----------------------------------------------

def debug_dump(frame: Any, regions: Any, out_dir: str) -> List[str]:
    """Write each crop and its preprocessed bitmap to out_dir so calibration
    problems are visible instead of inferred. Returns the paths written."""
    written: List[str] = []
    try:
        Image = _pil_image()
    except Exception:
        return written
    os.makedirs(out_dir, exist_ok=True)
    for key, rect in rects_for_frame(regions, frame).items():
        img = crop(frame, rect)
        if img is None:
            continue
        kind = next((k for n, _p, k in REGION_SPECS if n == key), "text")
        for suffix, data in (("raw", _to_gray(img)),
                             ("prep", preprocess(img, kind, invert=True))):
            if data is None:
                continue
            path = os.path.join(out_dir, "%s_%s.png" % (key, suffix))
            try:
                Image.fromarray(data).save(path)
                written.append(path)
            except Exception:
                continue
    return written


def _load_entities() -> Any:
    """Best-effort load of the sibling entities module. Returns None if it does
    not exist yet or exposes a different loader — name validation is then
    skipped and every name read stays below MIN_CONFIDENCE."""
    try:
        from . import entities as entities_module
    except Exception:
        return None
    for attr in ("load", "load_entities", "get", "default"):
        fn = getattr(entities_module, attr, None)
        if callable(fn):
            try:
                obj = fn()
                if obj is not None:
                    return obj
            except Exception:
                continue
    cls = getattr(entities_module, "Entities", None)
    if cls is not None:
        for attr in ("load", "load_or_fetch"):
            fn = getattr(cls, attr, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    continue
    # A module exposing match_name at module level works directly.
    if hasattr(entities_module, "match_name"):
        return entities_module
    return None


def _grab_frame() -> Tuple[Optional[Any], Optional[str]]:
    """(frame array, path). Prefers the sibling capture module; falls back to
    the platform screenshot tools v2 already relies on."""
    try:
        from . import capture as capture_module
    except Exception:
        capture_module = None

    if capture_module is not None:
        for attr in ("grab", "grab_frame", "capture_frame", "frame", "screenshot",
                     "capture"):
            fn = getattr(capture_module, attr, None)
            if not callable(fn):
                continue
            try:
                result = fn()
            except Exception:
                continue
            if result is None:
                continue
            if isinstance(result, tuple):
                arr = next((r for r in result if hasattr(r, "shape")), None)
                path = next((r for r in result if isinstance(r, str)), None)
                if arr is not None:
                    return (arr, path)
                if path:
                    return (_load_image(path), path)
                continue
            if isinstance(result, str):
                return (_load_image(result), result)
            arr = _as_array(result)
            if arr is not None:
                return (arr, None)

    # Fallback: same approach as tft_coach_v2.py
    import subprocess
    import tempfile
    path = os.path.join(tempfile.gettempdir(), "tftcoach_ocr_probe.png")
    try:
        if platform.system() == "Darwin":
            subprocess.run(["screencapture", "-x", "-t", "png", path], check=True)
        else:
            from PIL import ImageGrab
            ImageGrab.grab().save(path)
    except Exception as exc:
        print("capture failed: %s" % exc)
        return (None, None)
    return (_load_image(path), path)


def _load_image(path: str) -> Optional[Any]:
    try:
        Image = _pil_image()
        np = _numpy()
        with Image.open(path) as im:
            return np.asarray(im.convert("RGB"))
    except Exception:
        return None


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Sanity-check OCR extraction against a live frame.")
    parser.add_argument("--image", help="read this file instead of capturing")
    parser.add_argument("--debug", action="store_true",
                        help="write crops + preprocessed bitmaps to .captures/ocr_debug")
    args = parser.parse_args()

    ensure_dirs()
    ok, reason = is_available()
    print("backend : %s" % backend_name())
    print("status  : %s — %s" % ("OK" if ok else "UNAVAILABLE", reason))

    regions = Regions.load()
    if not regions.calibrated:
        print("regions : NOT CALIBRATED — run: python3 -m tftcoach.calibrate")
    else:
        print("regions : %d rects @ %sx%s (missing: %s)"
              % (len(regions.rects), regions.resolution[0], regions.resolution[1],
                 ", ".join(regions.missing()) or "none"))

    if args.image:
        frame, path = _load_image(args.image), args.image
    else:
        frame, path = _grab_frame()
    if frame is None:
        print("frame   : capture failed (on macOS grant Screen Recording to your terminal)")
        return 1
    width, height = frame_size(frame)
    print("frame   : %dx%d  %s" % (width, height, path or "(in memory)"))
    if regions.calibrated and [width, height] != list(regions.resolution):
        print("          ! resolution differs from calibration — rects are scaled, "
              "which Riot's HUD does not strictly honor. Recalibrate if reads look off.")

    entities = _load_entities()
    print("entities: %s" % ("loaded" if entities is not None
                            else "unavailable — names stay unvalidated (conf capped at %.2f)"
                            % UNVALIDATED_NAME_CAP))

    state = extract_state(frame, regions, entities, frame_path=path)
    print("\n%s" % state.summary_line())
    print("screen  : %s (heuristic guess)" % state.screen)
    print("\n%-9s %-34s %-6s %s" % ("FIELD", "VALUE", "CONF", "KNOWN"))
    for name in ("stage", "gold", "level", "hp", "streak", "shop", "board",
                 "bench", "augments", "traits"):
        f: Field = getattr(state, name)
        value = "unknown" if f.value is None else str(f.value)
        if len(value) > 33:
            value = value[:30] + "..."
        print("%-9s %-34s %-6.2f %s" % (name, value, f.confidence,
                                        "yes" if f.known else "no"))
    print("\n(board/bench are vision fields — OCR leaves them unknown by design.)")
    print("(streak/augments have no calibrated region in REGION_SPECS yet.)")

    if args.debug:
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               ".captures", "ocr_debug")
        paths = debug_dump(frame, regions, out_dir)
        print("\ndebug   : wrote %d images to %s" % (len(paths), out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
