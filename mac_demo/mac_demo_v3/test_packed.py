import unittest

from mac_encoding import OPCODE_CUSTOM0, decode_mac, encode_mac, encode_mac2, decode_mac2, mac2_golden
from benchmark.packed import dot16_reference, make_int16_words, pack


class TestMac2Encoding(unittest.TestCase):
    def test_known_encoding(self):
        # mac2 a0, a1, a2 : funct3=2, funct7=0
        word = encode_mac2(10, 11, 12)
        self.assertEqual(word & 0x7F, OPCODE_CUSTOM0)
        self.assertEqual((word >> 12) & 0x7, 2)
        self.assertEqual(decode_mac2(word), (10, 11, 12))

    def test_distinct_from_mac_and_mac4(self):
        self.assertIsNone(decode_mac(encode_mac2(1, 2, 3)))
        self.assertIsNone(decode_mac2(encode_mac(1, 2, 3)))


class TestMac2Semantics(unittest.TestCase):
    def test_two_lanes_added(self):
        a = pack(3, 4)      # lanes: lo=3, hi=4
        b = pack(5, 6)
        self.assertEqual(mac2_golden(0, a, b), 3 * 5 + 4 * 6)

    def test_signed_lanes(self):
        a = pack(-3, -4)
        b = pack(7, -8)
        self.assertEqual(mac2_golden(0, a, b), -21 + 32)

    def test_accumulates(self):
        self.assertEqual(mac2_golden(100, pack(1, 1), pack(1, 1)), 102)

    def test_wraparound(self):
        self.assertEqual(mac2_golden(0x7FFFFFFF, pack(1, 0), pack(1, 0)), -(2**31))

    def test_reference_dot_matches_lane_loop(self):
        a_words, b_words, a16, b16 = make_int16_words(16, seed=2026)
        acc = 0
        for x, y in zip(a_words, b_words):
            acc = mac2_golden(acc, x, y)
        self.assertEqual(acc, dot16_reference(a16, b16))


if __name__ == "__main__":
    unittest.main()
