import unittest

from benchmark.packed import packed_counts, run_packed_case, run_packed_all, PACKED_WORKLOADS


class TestPackedCounts(unittest.TestCase):
    def test_per_word_counts(self):
        # body + loop overhead (4) per 32-bit word (two int16 elements)
        self.assertEqual(packed_counts("std_lh", 1), 12)
        self.assertEqual(packed_counts("std_lw", 1), 16)
        self.assertEqual(packed_counts("mac2", 1), 7)

    def test_scales_linearly(self):
        self.assertEqual(packed_counts("mac2", 1024), 7 * 1024)


class TestPackedRun(unittest.TestCase):
    def test_correct_and_speedup(self):
        row = run_packed_case(256, t_ratio=1.0)
        self.assertTrue(row["correct"])
        self.assertAlmostEqual(row["speedup_lh"], 12 / 7)
        self.assertAlmostEqual(row["speedup_lw"], 16 / 7)

    def test_all_workloads_correct(self):
        rows = run_packed_all(ratios=(1.0, 1.1, 1.2))
        self.assertEqual(len(rows), len(PACKED_WORKLOADS) * 3)
        self.assertTrue(all(r["correct"] for r in rows))


if __name__ == "__main__":
    unittest.main()
