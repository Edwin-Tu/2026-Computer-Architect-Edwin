import random
import unittest

from mac_encoding import (
    OPCODE_CUSTOM0,
    decode_mac,
    dot_product_golden,
    encode_mac,
    mac_golden,
)


class TestEncoding(unittest.TestCase):
    def test_known_encoding(self):
        # mac a0, a1, a2 : rd=10, rs1=11, rs2=12
        # funct7=0 | rs2=01100 | rs1=01011 | funct3=000 | rd=01010 | opcode=0001011
        expected = 0b0000000_01100_01011_000_01010_0001011
        self.assertEqual(encode_mac(10, 11, 12), expected)

    def test_round_trip(self):
        for rd in range(32):
            for rs1 in range(0, 32, 5):
                for rs2 in range(0, 32, 7):
                    w = encode_mac(rd, rs1, rs2)
                    self.assertEqual(decode_mac(w), (rd, rs1, rs2))

    def test_rejects_non_mac_words(self):
        self.assertIsNone(decode_mac(0x00C58533))  # add a0, a1, a2
        self.assertIsNone(decode_mac(0x02C58533))  # mul a0, a1, a2
        self.assertIsNone(decode_mac(encode_mac(1, 2, 3) | (1 << 12)))  # funct3 != 0

    def test_register_range_checked(self):
        with self.assertRaises(ValueError):
            encode_mac(32, 0, 0)


class TestGoldenModel(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(mac_golden(10, 3, 4), 22)

    def test_negative_operands(self):
        self.assertEqual(mac_golden(0, -3, 4), -12)
        self.assertEqual(mac_golden(-5, -3, -4), 7)

    def test_wraparound(self):
        self.assertEqual(mac_golden(0x7FFF_FFFF, 1, 1), -0x8000_0000)
        self.assertEqual(mac_golden(0, 0x4000_0000, 4), 0)

    def test_dot_product_random_matches_python(self):
        rng = random.Random(1)
        for _ in range(200):
            n = rng.randint(0, 64)
            a = [rng.randint(-(2**31), 2**31 - 1) for _ in range(n)]
            b = [rng.randint(-(2**31), 2**31 - 1) for _ in range(n)]
            exp = sum(x * y for x, y in zip(a, b)) & 0xFFFF_FFFF
            exp = exp - (1 << 32) if exp & 0x8000_0000 else exp
            self.assertEqual(dot_product_golden(a, b), exp)


if __name__ == "__main__":
    unittest.main()
