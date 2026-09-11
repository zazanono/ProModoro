"""Timer state independent of terminal rendering."""

import math
import re
import time
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum


class Phase(str, Enum):
    FOCUS = "focus"
    SHORT = "short"
    LONG = "long"

    @property
    def label(self) -> str:
        return {
            self.FOCUS: "Focus",
            self.SHORT: "Short break",
            self.LONG: "Long break",
        }[self]


def parse_duration(value: str) -> int:
    """Accept minutes, unit-suffixed durations, or minutes:seconds."""
    value = value.strip().lower()
    match = re.fullmatch(r"(\d+):(\d{2})", value)
    if match:
        minutes, seconds = map(int, match.groups())
        if seconds >= 60:
            raise ValueError("Seconds after ':' must be between 00 and 59.")
        result = minutes * 60 + seconds
    else:
        match = re.fullmatch(r"(\d+(?:\.\d+)?)([smh]?)", value)
        if not match:
            raise ValueError("Use minutes, 25m, 90s, 1h, or 25:00.")
        amount, unit = match.groups()
        with localcontext() as context:
            context.prec = max(28, len(amount) + 4)
            seconds = Decimal(amount) * {"": 60, "s": 1, "m": 60, "h": 3600}[unit]
        if seconds != seconds.to_integral_value():
            raise ValueError("Use a duration with whole seconds.")
        result = int(seconds)
    if not 1 <= result <= 180 * 60:
        raise ValueError("Choose a duration from 1 second to 180 minutes.")
    return result


def format_time(seconds: float) -> str:
    minutes, seconds = divmod(max(0, math.ceil(seconds)), 60)
    return f"{minutes:02d}:{seconds:02d}"


@dataclass
class Durations:
    focus: int = 25 * 60
    short: int = 5 * 60
    long: int = 15 * 60

    def for_phase(self, phase: Phase) -> int:
        return getattr(self, phase.value)


class Timer:
    def __init__(self, durations: Durations | None = None) -> None:
        self.durations = durations or Durations()
        self.phase = Phase.FOCUS
        self.completed = 0
        self.remaining = float(self.total)
        self.deadline: float | None = None

    @property
    def total(self) -> int:
        return self.durations.for_phase(self.phase)

    @property
    def running(self) -> bool:
        return self.deadline is not None

    def start(self) -> None:
        if not self.running:
            self.deadline = time.monotonic() + self.remaining

    def pause(self) -> None:
        if self.deadline is not None:
            self.remaining = max(0.0, self.deadline - time.monotonic())
            self.deadline = None

    def select(self, phase: Phase) -> None:
        self.phase = phase
        self.reset()

    def reset(self) -> None:
        self.deadline = None
        self.remaining = float(self.total)

    def next_phase(self) -> Phase:
        if self.phase != Phase.FOCUS:
            return Phase.FOCUS
        return Phase.LONG if (self.completed + 1) % 4 == 0 else Phase.SHORT

    def skip(self) -> None:
        # Skipping never counts as a completed focus session.
        self.select(self.next_phase())

    def tick(self) -> bool:
        """Update from a deadline, so delayed rendering cannot slow the timer."""
        if self.deadline is None:
            return False
        self.remaining = max(0.0, self.deadline - time.monotonic())
        if self.remaining > 0:
            return False
        finished_focus = self.phase == Phase.FOCUS
        following = self.next_phase()
        if finished_focus:
            self.completed += 1
        self.select(following)
        if finished_focus:
            self.start()
        return True
