"""Rolling-hash string matching (Karp-Rabin).

Why this module exists: Python's ``str.find`` is already fast, but it is not
a streaming interface.  Karp-Rabin lets a caller push text in chunks and
receive matches as soon as the rolling window fills, using only integers
from the standard library.

Hash choice: the modulus is the Mersenne prime ``2**61 - 1``.  Multiplication
of two values below that prime fits comfortably in a machine word on every
platform CPython supports, so the modular arithmetic stays cheap without
needing ``gmpy2`` or ``numpy``.  The base is a small odd prime; any odd base
larger than the alphabet works, and 257 is the conventional pick.
"""

from __future__ import annotations

from typing import Iterator, Optional


class Matcher:
    """Preprocess a pattern, then stream-report its occurrences in a text.

    The matcher is reusable across texts: construction computes the pattern
    hash once, and each call to :meth:`search` only does rolling work.

    Parameters
    ----------
    pattern:
        The byte string to look for.  An empty pattern is rejected because
        the set of start positions of an empty string is unbounded.
    base:
        Hash base.  Must be odd and at least 2 so that the polynomial hash
        separates distinct strings with high probability.
    modulus:
        Hash modulus.  Must be prime and larger than the base.  The default
        is the Mersenne prime ``2**61 - 1``.

    Raises
    ------
    ValueError:
        If the pattern is empty, or if base/modulus are not usable.
    """

    __slots__ = ("_pattern", "_m", "_base", "_mod", "_pattern_hash", "_high_power")

    def __init__(
        self,
        pattern: bytes,
        base: int = 257,
        modulus: int = (1 << 61) - 1,
    ) -> None:
        if not isinstance(pattern, (bytes, bytearray)):
            raise TypeError("pattern must be bytes or bytearray")
        if len(pattern) == 0:
            raise ValueError("pattern must be non-empty")
        if base < 2 or base % 2 == 0:
            raise ValueError("base must be an odd integer >= 2")
        if modulus <= base:
            raise ValueError("modulus must be larger than base")

        self._pattern = bytes(pattern)
        self._m = len(self._pattern)
        self._base = base
        self._mod = modulus
        self._pattern_hash = self._hash_bytes(self._pattern)
        # ``base ** (m - 1) mod modulus`` is the weight of the leading byte
        # when we slide the window; precomputing it keeps the inner loop to
        # two multiplications per position.
        self._high_power = pow(base, self._m - 1, modulus)

    def _hash_bytes(self, data: bytes) -> int:
        h = 0
        for b in data:
            h = (h * self._base + b) % self._mod
        return h

    @property
    def pattern(self) -> bytes:
        """The pattern this matcher was built for."""
        return self._pattern

    def search(self, text: bytes) -> Iterator[int]:
        """Yield every start index where ``pattern`` occurs in ``text``.

        The scan is left-to-right and reports matches in increasing order of
        start index.  Overlapping matches are reported independently, which
        is what a caller asking for "all start positions" expects.

        A rolling hash is used to skip most comparisons, but every hash hit
        is confirmed with a direct byte comparison.  That confirmation step
        is what makes the algorithm correct rather than merely probabilistic.
        """
        if not isinstance(text, (bytes, bytearray)):
            raise TypeError("text must be bytes or bytearray")
        text = bytes(text)
        n = len(text)
        m = self._m
        if n < m:
            return

        base = self._base
        mod = self._mod
        target = self._pattern_hash
        high = self._high_power
        pattern = self._pattern

        # Hash of text[0:m], computed directly because there is no prior
        # window to roll from.
        window_hash = 0
        for b in text[:m]:
            window_hash = (window_hash * base + b) % mod

        last_start = n - m
        i = 0
        while True:
            if window_hash == target and text[i : i + m] == pattern:
                yield i
            if i == last_start:
                break
            # Roll: drop the leading byte, shift the rest left, add the new
            # trailing byte.  ``% mod`` after the subtraction keeps the
            # intermediate non-negative, which Python needs but C would not.
            outgoing = text[i]
            incoming = text[i + m]
            window_hash = (window_hash - outgoing * high) % mod
            window_hash = (window_hash * base + incoming) % mod
            i += 1

    def find(self, text: bytes) -> Optional[int]:
        """Return the first start index in ``text``, or ``None``.

        A convenience wrapper around :meth:`search` for callers who only
        care whether the pattern appears at all.
        """
        for pos in self.search(text):
            return pos
        return None
