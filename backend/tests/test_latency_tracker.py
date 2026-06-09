import time

from backend.app.services.performance.latency_tracker import LatencyTracker


def test_latency_tracker_returns_positive_duration() -> None:
    tracker = LatencyTracker()

    with tracker.measure("small_sleep"):
        time.sleep(0.001)

    assert tracker.timings["small_sleep"] > 0
    assert tracker.as_dict()["small_sleep"] == tracker.timings["small_sleep"]
