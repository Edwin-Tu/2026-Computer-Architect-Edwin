import unittest

from hw_estimate import partial_products
from pipeline_model import packed_loop_trace, simulate


class TestPackedPipeline(unittest.TestCase):
    def test_mac2_cycles_formula_lat1(self):
        # per word: 7 instructions, 1 load-use stall (lw t1 -> mac2), 2 flush cycles per taken branch
        n = 100
        self.assertEqual(simulate(packed_loop_trace("mac2", n, mac2_lat=1)), 10 * n + 2)

    def test_mac2_slower_with_two_cycle_latency(self):
        n = 100
        c1 = simulate(packed_loop_trace("mac2", n, mac2_lat=1))
        c2 = simulate(packed_loop_trace("mac2", n, mac2_lat=2))
        self.assertGreater(c2, c1)

    def test_std_lh_cycles_per_word_is_instructions_plus_flush(self):
        # std_lh: 12 instructions + 2 flush per word, no stalls -> 14 cycles/word
        n = 256
        std = simulate(packed_loop_trace("std_lh", n))
        self.assertAlmostEqual(std / n, 14, delta=0.1)

    def test_pipeline_speedup_below_instruction_speedup(self):
        # instruction ratio 12/7 = 1.71; cycle ratio (12+2)/(7+2+1) = 1.40 (mac2 load-use stall)
        n = 256
        std = simulate(packed_loop_trace("std_lh", n))
        mac2 = simulate(packed_loop_trace("mac2", n, mac2_lat=1))
        self.assertAlmostEqual(std / mac2, 14 / 10, delta=0.01)

    def test_unknown_variant_rejected(self):
        with self.assertRaises(ValueError):
            packed_loop_trace("bogus", 4)


class TestHardwareEstimate(unittest.TestCase):
    def test_partial_products(self):
        self.assertEqual(partial_products("mac"), 32 * 32)
        self.assertEqual(partial_products("mac2"), 2 * 16 * 16)

    def test_mac2_fewer_partial_products_than_mac(self):
        self.assertLess(partial_products("mac2"), partial_products("mac"))


if __name__ == "__main__":
    unittest.main()
