"""Latency measurement helpers for local benchmarks and observability."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


def monotonic_ms() -> float:
    return time.perf_counter() * 1000.0


@dataclass
class LatencyTracker:
    """Collect elapsed milliseconds by label."""

    timings: dict[str, float] = field(default_factory=dict)
    _starts: dict[str, float] = field(default_factory=dict)

    def start(self, label: str) -> None:
        self._starts[label] = monotonic_ms()

    def stop(self, label: str) -> float:
        started = self._starts.pop(label, monotonic_ms())
        elapsed = round(max(0.0, monotonic_ms() - started), 3)
        self.timings[label] = elapsed
        return elapsed

    @contextmanager
    def measure(self, label: str) -> Iterator[None]:
        self.start(label)
        try:
            yield
        finally:
            self.stop(label)

    def as_dict(self) -> dict[str, float]:
        return dict(self.timings)
