import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from benchmark.amdahl import amdahl_speedup, dilution_table
from benchmark.compiler_baseline import COMPILER_PER_ELEMENT, compiler_loop_count, compiler_speedup_vs_mac2

HERE = Path(__file__).resolve().parent.parent
GCC = shutil.which("riscv64-elf-gcc")
OBJDUMP = shutil.which("riscv64-elf-objdump")


class TestAmdahl(unittest.TestCase):
    def test_whole_program_kernel(self):
        self.assertAlmostEqual(amdahl_speedup(1.0, 2.0), 2.0)

    def test_half_program_kernel(self):
        self.assertAlmostEqual(amdahl_speedup(0.5, 2.0), 4 / 3)

    def test_no_kernel_no_gain(self):
        self.assertAlmostEqual(amdahl_speedup(0.0, 10.0), 1.0)

    def test_dilution_table_monotone(self):
        rows = dilution_table(s=12 / 7, fractions=(1.0, 0.5, 0.25))
        vals = [r["overall"] for r in rows]
        self.assertEqual(vals, sorted(vals, reverse=True))


class TestCompilerBaseline(unittest.TestCase):
    def test_recorded_count(self):
        self.assertEqual(COMPILER_PER_ELEMENT, 7)

    def test_speedup_against_mac2(self):
        self.assertAlmostEqual(compiler_speedup_vs_mac2(), 7 / 3.5)

    @unittest.skipUnless(GCC and OBJDUMP, "RISC-V toolchain not installed")
    def test_live_compile_matches_recorded(self):
        src = HERE / "benchmark" / "dot16.c"
        with tempfile.TemporaryDirectory() as d:
            obj = Path(d) / "dot16.o"
            subprocess.run([GCC, "-march=rv32im", "-mabi=ilp32", "-ffreestanding", "-O2",
                            "-c", str(src), "-o", str(obj)], check=True)
            self.assertEqual(compiler_loop_count(obj), COMPILER_PER_ELEMENT)


if __name__ == "__main__":
    unittest.main()
