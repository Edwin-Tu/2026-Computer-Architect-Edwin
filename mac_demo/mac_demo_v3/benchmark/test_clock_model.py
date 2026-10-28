import unittest

from benchmark.clock_model import (
    breakeven_ratio,
    cycles_per_element,
    cpu_time_ratio,
    mix_standard,
    mix_mac,
)


class TestCyclesPerElement(unittest.TestCase):
    def test_standard_mix_with_mul_cpi_3(self):
        # lw, lw (CPI 2 each) + mul (3) + add, addi x3, bnez (CPI 1 each)
        self.assertEqual(cycles_per_element(mix_standard(mul_cpi=3)), 12)

    def test_mac_mix_with_mac_cpi_1(self):
        # lw, lw (2 each) + mac (1) + addi x3, bnez (1 each)
        self.assertEqual(cycles_per_element(mix_mac(mac_cpi=1)), 9)

    def test_instruction_counts(self):
        self.assertEqual(sum(n for _, _, n in mix_standard(mul_cpi=3)), 8)
        self.assertEqual(sum(n for _, _, n in mix_mac(mac_cpi=1)), 7)


class TestBreakeven(unittest.TestCase):
    def test_breakeven_with_mul_cpi_3(self):
        # standard 12 cycles, mac 9 cycles: MAC stays faster until T ratio 12/9
        self.assertAlmostEqual(breakeven_ratio(mul_cpi=3, mac_cpi=1), 12 / 9)

    def test_breakeven_with_mul_cpi_1(self):
        # standard 10 cycles (mul CPI 1), mac 9 cycles: break-even 10/9
        self.assertAlmostEqual(breakeven_ratio(mul_cpi=1, mac_cpi=1), 10 / 9)

    def test_cpu_time_ratio_at_unit_clock(self):
        r = cpu_time_ratio(mul_cpi=3, mac_cpi=1, t_ratio=1.0)
        self.assertAlmostEqual(r, 9 / 12)

    def test_slow_clock_erases_gain_when_past_breakeven(self):
        r = cpu_time_ratio(mul_cpi=1, mac_cpi=1, t_ratio=1.2)
        self.assertGreater(r, 1.0)


if __name__ == "__main__":
    unittest.main()
