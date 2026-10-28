import unittest

from mac_encoding import (
    OPCODE_CUSTOM0,
    apply_mac,
    decode_mac,
    decode_mac_r4,
    encode_mac,
    encode_mac_r4,
)


class TestR4Encoding(unittest.TestCase):
    def test_known_r4_encoding(self):
        # mac a0, a1, a2, a3 : rd=10 rs1=11 rs2=12 rs3=13 (funct2=0, funct3=0)
        word = encode_mac_r4(10, 11, 12, 13)
        self.assertEqual(word & 0x7F, OPCODE_CUSTOM0)
        self.assertEqual((word >> 27) & 0x1F, 13)
        self.assertEqual((word >> 25) & 0x3, 0)
        self.assertEqual((word >> 20) & 0x1F, 12)
        self.assertEqual((word >> 15) & 0x1F, 11)
        self.assertEqual((word >> 7) & 0x1F, 10)

    def test_r4_round_trip(self):
        for rd in (0, 5, 31):
            for rs1, rs2, rs3 in ((1, 2, 3), (31, 0, 17)):
                self.assertEqual(decode_mac_r4(encode_mac_r4(rd, rs1, rs2, rs3)), (rd, rs1, rs2, rs3))

    def test_r4_and_rd_forms_differ(self):
        self.assertNotEqual(encode_mac(10, 11, 12), encode_mac_r4(10, 11, 12, 10))

    def test_rd_form_does_not_decode_as_r4_and_vice_versa(self):
        self.assertIsNone(decode_mac_r4(encode_mac(1, 2, 3)))
        self.assertIsNone(decode_mac(encode_mac_r4(1, 2, 3, 4)))

    def test_r4_range_checked(self):
        with self.assertRaises(ValueError):
            encode_mac_r4(0, 0, 0, 32)


class TestRdZeroSemantics(unittest.TestCase):
    def test_write_to_x0_is_discarded(self):
        regs = [0] * 32
        regs[11], regs[12] = 3, 4
        apply_mac(regs, rd=0, rs1=11, rs2=12)
        self.assertEqual(regs[0], 0)

    def test_accumulate_into_nonzero_rd(self):
        regs = [0] * 32
        regs[10], regs[11], regs[12] = 10, 3, 4
        apply_mac(regs, rd=10, rs1=11, rs2=12)
        self.assertEqual(regs[10], 22)

    def test_other_registers_unchanged(self):
        regs = [7] * 32
        regs[0] = 0
        before = list(regs)
        apply_mac(regs, rd=5, rs1=1, rs2=2)
        self.assertEqual([i for i, v in enumerate(regs) if v != before[i]], [5])


if __name__ == "__main__":
    unittest.main()
