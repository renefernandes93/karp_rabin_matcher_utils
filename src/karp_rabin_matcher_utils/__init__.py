"""Karp-Rabin rolling-hash string matcher.

Public API:
    Matcher(pattern, base=257, modulus=(1 << 61) - 1)
        .search(text) -> iterator of start positions
"""

from .core import Matcher

__all__ = ["Matcher"]
