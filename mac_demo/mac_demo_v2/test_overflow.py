import unittest

from mac_encoding import mac_golden


class TestOverflowPolicy(unittest.TestCase):
    def test_low_word_of_full_product(self):
        # (2^31 - 1)^2 = 0x3FFFFFFF00000001; low 32 bits are 0x00000001
        self.assertEqual(mac_golden(0, 0x7FFFFFFF, 0x7FFFFFFF), 1)

    def test_product_low_word_matches_mul(self):
        for a, b in ((0x12345678, 0x9ABCDEF0), (-1, -1), (-(2**31), 2)):
            low = (a * b) & 0xFFFFFFFF
            self.assertEqual(mac_golden(0, a, b) & 0xFFFFFFFF, low)


if __name__ == "__main__":
    unittest.main()
