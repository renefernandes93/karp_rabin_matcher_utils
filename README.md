# karp_rabin_matcher_utils

A rolling-hash string matcher that preprocesses a pattern once and then
reports every start position of that pattern in a text in expected linear
time, using only Python's standard-library integers.

```python
from karp_rabin_matcher_utils import Matcher

matcher = Matcher(b"ab")
print(list(matcher.search(b"ababab")))   # [0, 2, 4]
print(matcher.find(b"xabx"))             # 1
print(matcher.find(b"zzz"))              # None
```

`Matcher(pattern, base=257, modulus=(1 << 61) - 1)` builds the pattern hash
once.  `search(text)` yields start indices in increasing order, including
overlapping matches.  `find(text)` returns the first index or `None`.
The `pattern` property exposes the stored pattern.

## Why this exists

`str.find` is fast, but it is not a streaming interface and it does not
let you reuse a preprocessed pattern across many texts.  Karp-Rabin gives
a small object that can be constructed once and queried repeatedly, and
it makes the rolling-hash idea explicit for callers who want to build on
it.

The trade-off is probabilistic skipping with deterministic confirmation.
The rolling hash is used to skip most positions cheaply, but every hash
hit is verified with a direct byte comparison, so the output is exact
rather than merely high-probability.  Expected time is linear in the text
length; worst case degrades to quadratic only on adversarial inputs, which
is the standard Karp-Rabin contract.

## Edge cases

An empty pattern is rejected at construction time with `ValueError`,
because the set of start positions of an empty string in a text is not a
finite list of matches in any useful sense.  A text shorter than the
pattern yields no matches.  `bytearray` inputs are accepted and copied, so
mutating the original afterwards does not affect results.
