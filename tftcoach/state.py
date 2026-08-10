"""Shared state contract for TFT Coach Option B.

Every module in the pipeline speaks this schema. Python 3.9 compatible
(no PEP 604 unions at runtime, no match statements).
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import os
from typing import Any, Dict, List, Optional

# Confidence a parsed field must reach to be treated as known.
MIN_CONFIDENCE = 0.55


@dataclasses.dataclass
class Field:
    """One extracted value plus how much we trust it.

    value is None when extraction failed — callers must treat None as
    'unknown', never as zero. source is one of: ocr, vision, manual, derived.
    """

    value: Optional[Any] = None
    confidence: float = 0.0
    source: str = "ocr"

    @property
    def known(self) -> bool:
        return self.value is not None and self.confidence >= MIN_CONFIDENCE

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "confidence": round(self.confidence, 2),
                "source": self.source}


@dataclasses.dataclass
class Unit:
    name: str
    star: Optional[int] = None
    items: Optional[List[str]] = None
    on_board: bool = True
    confidence: float = 0.0


@dataclasses.dataclass
class GameState:
    """One tick of observed game state. Unknown fields stay None — the coach
    prompt renders them as 'unknown' so Claude never invents them."""

    ts: str = ""
    stage: Field = dataclasses.field(default_factory=Field)      # "3-2"
    gold: Field = dataclasses.field(default_factory=Field)       # int
    level: Field = dataclasses.field(default_factory=Field)      # int
    hp: Field = dataclasses.field(default_factory=Field)         # int
    streak: Field = dataclasses.field(default_factory=Field)     # "W3"/"L2"
    shop: Field = dataclasses.field(default_factory=Field)       # List[str]
    board: Field = dataclasses.field(default_factory=Field)      # List[Unit]
    bench: Field = dataclasses.field(default_factory=Field)      # List[Unit]
    augments: Field = dataclasses.field(default_factory=Field)   # List[str]
    traits: Field = dataclasses.field(default_factory=Field)     # List[str]
    screen: str = "unknown"   # planning | combat | augment | carousel | unknown
    raw_capture: Optional[str] = None   # path to the frame this came from

    def __post_init__(self) -> None:
        if not self.ts:
            self.ts = datetime.datetime.now().isoformat(timespec="seconds")

    # -- serialization ----------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ts": self.ts, "screen": self.screen}
        for name in ("stage", "gold", "level", "hp", "streak", "shop",
                     "board", "bench", "augments", "traits"):
            field_obj: Field = getattr(self, name)
            val = field_obj.value
            if dataclasses.is_dataclass(val):
                val = dataclasses.asdict(val)
            elif isinstance(val, list) and val and dataclasses.is_dataclass(val[0]):
                val = [dataclasses.asdict(v) for v in val]
            out[name] = {"value": val, "confidence": round(field_obj.confidence, 2),
                         "source": field_obj.source}
        if self.raw_capture:
            out["raw_capture"] = self.raw_capture
        return out

    def known_fields(self) -> Dict[str, Any]:
        """Only the fields we actually trust — what goes into the prompt."""
        out = {}
        for name in ("stage", "gold", "level", "hp", "streak", "shop",
                     "board", "bench", "augments", "traits"):
            f: Field = getattr(self, name)
            if f.known:
                out[name] = f.value
        return out

    def unknown_fields(self) -> List[str]:
        return [n for n in ("stage", "gold", "level", "hp", "shop", "board")
                if not getattr(self, n).known]

    def summary_line(self) -> str:
        """Compact one-liner for the timeline / overlay status."""
        def g(n: str) -> str:
            f: Field = getattr(self, n)
            return str(f.value) if f.known else "?"
        return (f"{g('stage')} | {g('gold')}g | lv{g('level')} | "
                f"{g('hp')}hp | {g('streak')}")


class Timeline:
    """Append-only per-game record. One JSONL file per game."""

    def __init__(self, game_dir: str, game_id: Optional[str] = None):
        os.makedirs(game_dir, exist_ok=True)
        self.game_id = game_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.path = os.path.join(game_dir, f"game_{self.game_id}.jsonl")
        self.ticks: List[GameState] = []
        self.advice: List[Dict[str, Any]] = []

    def append(self, state: GameState) -> None:
        self.ticks.append(state)
        self._write({"type": "state", **state.to_dict()})

    def append_advice(self, text: str, trigger: str) -> None:
        rec = {"type": "advice", "ts": datetime.datetime.now().isoformat(timespec="seconds"),
               "trigger": trigger, "text": text}
        self.advice.append(rec)
        self._write(rec)

    def _write(self, rec: Dict[str, Any]) -> None:
        try:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except OSError:
            pass

    def last(self) -> Optional[GameState]:
        return self.ticks[-1] if self.ticks else None

    def delta(self) -> Dict[str, Any]:
        """What changed since the previous tick — the trend signal v1 lacked."""
        if len(self.ticks) < 2:
            return {}
        prev, cur = self.ticks[-2], self.ticks[-1]
        out: Dict[str, Any] = {}
        for name in ("gold", "level", "hp"):
            a: Field = getattr(prev, name)
            b: Field = getattr(cur, name)
            if a.known and b.known:
                try:
                    out[name] = int(b.value) - int(a.value)
                except (TypeError, ValueError):
                    pass
        return out

    def render(self, max_ticks: int = 14) -> str:
        """Compact game history for the coaching prompt."""
        lines = [t.summary_line() for t in self.ticks[-max_ticks:]]
        return "\n".join(lines)
