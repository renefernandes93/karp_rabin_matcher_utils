import unittest

from karp_rabin_matcher_utils import Matcher


class MatcherConstructionTests(unittest.TestCase):
    def test_empty_pattern_is_rejected(self):
        with self.assertRaises(ValueError):
            Matcher(b"")

    def test_pattern_must_be_bytes(self):
        with self.assertRaises(TypeError):
            Matcher("abc")  # type: ignore[arg-type]

    def test_even_base_is_rejected(self):
        with self.assertRaises(ValueError):
            Matcher(b"a", base=256)

    def test_modulus_must_exceed_base(self):
        with self.assertRaises(ValueError):
            Matcher(b"a", base=101, modulus=101)

    def test_pattern_property_round_trips(self):
        m = Matcher(bytearray(b"abc"))
        self.assertEqual(m.pattern, b"abc")


class MatcherSearchTests(unittest.TestCase):
    def test_single_occurrence(self):
        m = Matcher(b"needle")
        self.assertEqual(list(m.search(b"haystack needle haystack")), [9])

    def test_multiple_non_overlapping(self):
        m = Matcher(b"ab")
        self.assertEqual(list(m.search(b"ababab")), [0, 2, 4])

    def test_overlapping_matches_are_reported(self):
        m = Matcher(b"aa")
        self.assertEqual(list(m.search(b"aaaa")), [0, 1, 2])

    def test_no_match(self):
        m = Matcher(b"zzz")
        self.assertEqual(list(m.search(b"abcdef")), [])

    def test_text_shorter_than_pattern(self):
        m = Matcher(b"abcdef")
        self.assertEqual(list(m.search(b"abc")), [])

    def test_text_equal_to_pattern(self):
        m = Matcher(b"exact")
        self.assertEqual(list(m.search(b"exact")), [0])

    def test_empty_text(self):
        m = Matcher(b"x")
        self.assertEqual(list(m.search(b"")), [])

    def test_match_at_end_of_text(self):
        m = Matcher(b"end")
        self.assertEqual(list(m.search(b"the end")), [4])

    def test_bytearray_text_is_accepted(self):
        m = Matcher(b"bc")
        self.assertEqual(list(m.search(bytearray(b"abcd"))), [1])

    def test_non_bytes_text_is_rejected(self):
        m = Matcher(b"a")
        with self.assertRaises(TypeError):
            list(m.search("abc"))  # type: ignore[arg-type]

    def test_reusable_across_texts(self):
        m = Matcher(b"ab")
        self.assertEqual(list(m.search(b"abab")), [0, 2])
        self.assertEqual(list(m.search(b"xabx")), [1])

    def test_find_returns_first_index(self):
        m = Matcher(b"bc")
        self.assertEqual(m.find(b"abcabc"), 1)

    def test_find_returns_none_when_absent(self):
        m = Matcher(b"bc")
        self.assertIsNone(m.find(b"aaaa"))

    def test_all_bytes_are_handled(self):
        # Every possible byte value must round-trip through the hash without
        # the modular arithmetic misbehaving on high values.
        pattern = bytes(range(256))
        text = b"prefix" + pattern + b"suffix"
        m = Matcher(pattern)
        self.assertEqual(list(m.search(text)), [6])

    def test_custom_base_and_modulus(self):
        m = Matcher(b"aba", base=131, modulus=(1 << 31) - 1)
        self.assertEqual(list(m.search(b"xababa")), [1, 3])

    def test_highly_repetitive_input(self):
        # A long run of a single byte is the worst case for hash collisions;
        # the direct comparison must still produce exact positions.
        text = b"a" * 1000
        m = Matcher(b"aaa")
        positions = list(m.search(text))
        self.assertEqual(positions, list(range(998)))


if __name__ == "__main__":
    unittest.main()
