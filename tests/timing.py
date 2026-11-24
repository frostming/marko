from __future__ import annotations

import gc
import time
from typing import Any, Callable

# Long enough for the coarse CPU clock on Windows, which ticks every ~16ms
_MIN_TIME = 0.1


def _cpu_time(func: Callable[[Any], object], arg: Any) -> float:
    # CPU time rather than wall time: on a busy shared runner a longer run is
    # more likely to be preempted, which inflates the ratio of wall times
    runs = 0
    start = time.process_time()
    while True:
        func(arg)
        runs += 1
        elapsed = time.process_time() - start
        if elapsed >= _MIN_TIME:
            return elapsed / runs


def _time_ratio(func: Callable[[Any], object], small: Any, large: Any) -> float:
    best_small = best_large = float("inf")
    for _ in range(3):
        best_small = min(best_small, _cpu_time(func, small))
        best_large = min(best_large, _cpu_time(func, large))
    return best_large / best_small


def assert_scales_linearly(
    func: Callable[[Any], object], small: Any, large: Any, limit: float = 8
) -> None:
    """Assert that ``func(large)`` takes less than ``limit`` times ``func(small)``.

    A super-linear regression exceeds the limit on every attempt, while noise
    rarely does twice in a row, so a borderline ratio is measured again.
    """
    gc_enabled = gc.isenabled()
    gc.disable()
    try:
        ratios = []
        for _ in range(3):
            ratio = _time_ratio(func, small, large)
            if ratio < limit:
                return
            ratios.append(ratio)
            if ratio >= 2 * limit:
                break
    finally:
        if gc_enabled:
            gc.enable()
    raise AssertionError(
        f"took {', '.join(f'{r:.1f}x' for r in ratios)} the time, limit {limit}x"
    )
