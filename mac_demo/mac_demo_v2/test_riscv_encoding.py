import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from mac_encoding import decode_mac

GCC = shutil.which("riscv64-elf-gcc")
OBJDUMP = shutil.which("riscv64-elf-objdump")
HERE = Path(__file__).resolve().parent


@unittest.skipUnless(GCC and OBJDUMP, "RISC-V toolchain not installed")
class TestRiscvEncodingInCompilerOutput(unittest.TestCase):
    def test_mac_insn_emits_custom0_encoding(self):
        with tempfile.TemporaryDirectory() as d:
            obj = Path(d) / "probe.o"
            subprocess.run(
                [GCC, "-march=rv32im", "-mabi=ilp32", "-ffreestanding", "-O1", "-c",
                 str(HERE / "riscv_probe.c"), "-I", str(HERE), "-o", str(obj)],
                check=True,
            )
            dump = subprocess.run([OBJDUMP, "-d", str(obj)], check=True,
                                  capture_output=True, text=True).stdout
            words = []
            for line in dump.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2 and parts[0].strip().endswith(":"):
                    try:
                        words.append(int(parts[1].strip().split()[0], 16))
                    except ValueError:
                        pass
            decoded = [decode_mac(w) for w in words]
            self.assertTrue(any(d is not None for d in decoded),
                            "no custom-0 mac instruction found in compiler output")


if __name__ == "__main__":
    unittest.main()
