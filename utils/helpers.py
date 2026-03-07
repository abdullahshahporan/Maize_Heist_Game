"""
helpers.py — Small utility functions.
"""

import time


class Timer:
    """Simple context-manager timer for measuring AI decision time."""

    def __init__(self):
        self.elapsed = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self._start


def clamp(value, lo, hi):
    return max(lo, min(hi, value))
