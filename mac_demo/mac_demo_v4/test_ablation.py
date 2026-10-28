import unittest

from benchmark.ablation import ablation_rows
from pipeline_model import scalar_int16_trace, simulate


class TestScalarTrace(unittest.TestCase):
    def test_scalar_std_pipeline_ratio_per_element(self):
        # std: 8 instr + 1 load-use stall + 2 flush = 11 cycles/element
        n = 128
        self.assertAlmostEqual(simulate(scalar_int16_trace("std", n)) / n, 11, delta=0.1)

    def test_scalar_mac_pipeline_ratio_per_element(self):
        # mac: 7 instr + 1 load-use stall + 2 flush = 10 cycles/element
        n = 128
        self.assertAlmostEqual(simulate(scalar_int16_trace("mac", n)) / n, 10, delta=0.1)


class TestAblation(unittest.TestCase):
    def setUp(self):
        self.rows = {r["id"]: r for r in ablation_rows()}

    def test_base_v1(self):
        self.assertAlmostEqual(self.rows["A0"]["instr"], 8 / 7, places=3)

    def test_unroll_adds_gain(self):
        self.assertAlmostEqual(self.rows["A1"]["instr"], 5 / 4, places=3)

    def test_packing_is_largest_instruction_factor(self):
        self.assertGreater(self.rows["A2"]["instr"], self.rows["A1"]["instr"])

    def test_pipeline_removes_packing_gain(self):
        # without packing (scalar mac), pipeline gain is small; with packing it is larger
        self.assertLess(self.rows["B1"]["pipe"], self.rows["A4"]["pipe"])

    def test_latency2_reduces_pipeline_gain(self):
        self.assertLess(self.rows["A5"]["pipe"], self.rows["A4"]["pipe"])

    def test_clock_penalty_reduces_gain(self):
        self.assertLess(self.rows["A6"]["pipe"], self.rows["A4"]["pipe"])


if __name__ == "__main__":
    unittest.main()
