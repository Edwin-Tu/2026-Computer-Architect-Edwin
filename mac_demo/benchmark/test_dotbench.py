import csv
import io
import unittest

from benchmark.dotbench import (
    CPI_DEFAULT,
    SEED,
    WORKLOADS,
    cpu_time,
    instruction_count,
    make_inputs,
    run_all,
    run_case,
    to_csv,
    to_markdown,
)
from mac_encoding import dot_product_golden


class TestWorkloads(unittest.TestCase):
    def test_workload_table(self):
        names = [(w["id"], w["kind"], w["n"]) for w in WORKLOADS]
        self.assertEqual(names, [
            ("B1", "full_range", 64), ("B1", "full_range", 256), ("B1", "full_range", 1024),
            ("B2", "int8", 64), ("B2", "int8", 256), ("B2", "int8", 1024),
            ("B3", "edge", 64),
        ])

    def test_inputs_are_deterministic(self):
        self.assertEqual(make_inputs("full_range", 32, SEED), make_inputs("full_range", 32, SEED))

    def test_inputs_are_signed_32bit(self):
        a, b = make_inputs("full_range", 256, SEED)
        for v in a + b:
            self.assertTrue(-(2**31) <= v <= 2**31 - 1)

    def test_int8_range(self):
        a, b = make_inputs("int8", 256, SEED)
        for v in a + b:
            self.assertTrue(-128 <= v <= 127)

    def test_edge_values_alternate(self):
        a, b = make_inputs("edge", 4, SEED)
        self.assertEqual(a, [2**31 - 1, -(2**31), 2**31 - 1, -(2**31)])


class TestCostModel(unittest.TestCase):
    def test_instruction_count_per_element(self):
        self.assertEqual(instruction_count("standard", 10), 80)
        self.assertEqual(instruction_count("mac", 10), 70)

    def test_cpu_time_formula(self):
        self.assertEqual(cpu_time(80, 1.0, 1.0), 80)
        self.assertAlmostEqual(cpu_time(70, 1.0, 1.2), 84.0)
        self.assertEqual(CPI_DEFAULT, 1.0)


class TestRunCase(unittest.TestCase):
    def test_result_correct_and_fields(self):
        row = run_case("full_range", 64, t_ratio=1.0)
        self.assertTrue(row["correct"])
        self.assertEqual(row["ic_std"], 512)
        self.assertEqual(row["ic_mac"], 448)
        self.assertAlmostEqual(row["speedup"], 512 / 448)

    def test_mac_loop_equals_reference(self):
        from mac_encoding import mac_golden
        a, b = make_inputs("edge", 64, SEED)
        acc = 0
        for x, y in zip(a, b):
            acc = mac_golden(acc, x, y)
        self.assertEqual(acc, dot_product_golden(a, b))
        self.assertTrue(run_case("edge", 64, t_ratio=1.0)["correct"])

    def test_slow_clock_can_erase_speedup(self):
        row = run_case("full_range", 64, t_ratio=1.2)
        self.assertLess(row["speedup"], 1.0)

    def test_run_all_covers_workloads_and_ratios(self):
        rows = run_all(ratios=(1.0, 1.1, 1.2))
        self.assertEqual(len(rows), len(WORKLOADS) * 3)
        self.assertTrue(all(r["correct"] for r in rows))


class TestOutput(unittest.TestCase):
    def test_csv_has_header_and_rows(self):
        rows = run_all(ratios=(1.0,))
        text = to_csv(rows)
        parsed = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(parsed), len(rows))
        self.assertIn("speedup", parsed[0])

    def test_markdown_table(self):
        rows = run_all(ratios=(1.0,))
        md = to_markdown(rows)
        self.assertTrue(md.splitlines()[0].startswith("| 工作負載"))
        self.assertEqual(len([l for l in md.splitlines() if l.startswith("| B")]), len(rows))


if __name__ == "__main__":
    unittest.main()


class TestUnroll(unittest.TestCase):
    def test_unroll_counts_per_element(self):
        from benchmark.dotbench import instruction_count
        self.assertEqual(instruction_count("standard", 1024, unroll=4) / 1024, 5)
        self.assertEqual(instruction_count("mac", 1024, unroll=4) / 1024, 4)

    def test_unroll1_unchanged(self):
        from benchmark.dotbench import instruction_count
        self.assertEqual(instruction_count("standard", 64), 512)
        self.assertEqual(instruction_count("mac", 64), 448)

    def test_unroll_requires_multiple(self):
        from benchmark.dotbench import instruction_count
        with self.assertRaises(ValueError):
            instruction_count("mac", 10, unroll=4)

    def test_unrolled_speedup(self):
        from benchmark.dotbench import run_case
        row = run_case("full_range", 64, unroll=4)
        self.assertAlmostEqual(row["speedup"], 5 / 4)
        self.assertTrue(row["correct"])
