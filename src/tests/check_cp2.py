#!/usr/bin/env python3
"""CP2 RV32IM validation and deterministic instruction tracing, version 1.0.

Compiles actual RV32IM machine code (ELF32), executes the MIN routines in a
small pure-Python RV32I subset interpreter, and records static/dynamic counts.
Does NOT model pipelines, caches, CPI, clock cycles, or physical runtime.
No third-party Python packages are necessary.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build"
MASK = 0xFFFF_FFFF
RETURN_ADDRESS = 0x7000_0000
FUNCTIONS = ("min_s32", "min_branch", "min_branchless")

# Exact 14 CP1 test cases (kept separate from generated stress tests).
CP1_CASES = [
    (3, -2), (5, 5), (10, 20), (20, 10), (-10, -20),
    (0, 0), (0, -1), (0, 100), (-100, 100),
    (2147483647, -2147483648), (-2147483648, 0),
    (2147483647, 0), (-2147483648, -2147483648),
    (2147483647, 2147483647),
]


def sx(n: int, width: int) -> int:
    n &= (1 << width) - 1
    return n - (1 << width) if n & (1 << (width - 1)) else n


def u32(n: int) -> int:
    return n & MASK


def compile_rv32(compiler: str | None) -> dict[str, str]:
    if compiler is None:
        compiler = next((name for name in (
            "riscv64-unknown-elf-gcc", "riscv64-elf-gcc",
            "riscv32-unknown-elf-gcc", "clang"
        ) if shutil.which(name)), None)
    if compiler is None:
        raise RuntimeError("No RISC-V capable compiler found. Install riscv64-elf-gcc or clang 17+.")
    OUTPUT.mkdir(exist_ok=True)
    target = OUTPUT / "min_rv32im.elf"
    use_clang = Path(compiler).name.startswith("clang")
    command = [compiler]
    if use_clang:
        command += ["--target=riscv32-unknown-elf", "-fuse-ld=lld"]
    command += [
        "-march=rv32im", "-mabi=ilp32", "-O2", "-ffreestanding",
        "-fno-builtin", "-fno-pic", "-fno-pie", "-nostdlib",
        "-Wl,-e,min_branch", "-Wl,-Ttext=0x10000", "-Wl,--no-relax",
        "-o", str(target),
        str(ROOT / "src/c_baseline/min.c"),
        str(ROOT / "src/rv32im/min_branch.S"),
        str(ROOT / "src/rv32im/min_branchless.S"),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(
            "RISC-V compilation/link failed.\n"
            f"Command: {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    version = subprocess.run([compiler, "--version"], capture_output=True, text=True, check=False)
    return {"binary": str(target), "compiler": compiler,
            "compiler_version": version.stdout.splitlines()[0] if version.stdout else "unknown",
            "command": " ".join(command)}


class ELF32:
    """Minimal ELF32 LE reader: only the fields needed for linked RISC-V ELF."""

    def __init__(self, path: str | Path):
        self.data = Path(path).read_bytes()
        d = self.data
        if d[:4] != b"\x7fELF" or d[4] != 1 or d[5] != 1:
            raise ValueError("Expected a little-endian 32-bit ELF")
        (e_type, e_machine, _, _, phoff, shoff, _, _,
         phentsize, phnum, shentsize, shnum, _) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
        if e_type != 2 or e_machine != 243:
            raise ValueError("Expected a linked RISC-V ELF32 executable (ET_EXEC)")
        self.segments = []
        for i in range(phnum):
            pos = phoff + i * phentsize
            (kind, file_offset, vaddr, _, file_size, _, flags, _) = struct.unpack_from("<IIIIIIII", d, pos)
            if kind == 1:
                self.segments.append((vaddr, vaddr + file_size, file_offset, flags))
        sections = [struct.unpack_from("<IIIIIIIIII", d, shoff + i * shentsize)
                    for i in range(shnum)]
        self.symbols = {}
        for sh in sections:
            typ, sym_offset, size, link, entsize = sh[1], sh[4], sh[5], sh[6], sh[9]
            if typ != 2 or entsize < 16:
                continue
            strsec = sections[link]
            strings = d[strsec[4]:strsec[4] + strsec[5]]
            for pos in range(sym_offset, sym_offset + size, entsize):
                name_off, addr, sz, info, _, shndx = struct.unpack_from("<IIIBBH", d, pos)
                end = strings.find(b"\x00", name_off)
                name = strings[name_off:end].decode("utf8", errors="replace")
                if (info & 0xF) == 2 and shndx != 0 and name:
                    self.symbols[name] = (addr, sz)

    def read_u32(self, addr: int) -> int:
        for begin, end, off, flags in sorted(self.segments, key=lambda s: bool(s[3] & 1), reverse=True):
            if begin <= addr and addr + 4 <= end:
                return struct.unpack_from("<I", self.data, off + addr - begin)[0]
        raise ValueError(f"PC 0x{addr:08x} is outside executable file data")

    def static_metrics(self, symbol: str) -> dict[str, int]:
        start, size = self.symbols[symbol]
        if size == 0 or size % 4:
            raise ValueError(f"Unexpected instruction size for {symbol}: {size}")
        codes = [self.read_u32(start + 4 * i) for i in range(size // 4)]
        if any((code & 3) != 3 for code in codes):
            raise ValueError(f"Compressed/non-32-bit instruction found in {symbol}")
        cond = sum((code & 0x7F) == 0x63 for code in codes)
        return {"instructions": len(codes), "conditional_branches": cond,
                "jal_or_jalr": sum((code & 0x7F) in (0x67, 0x6F) for code in codes),
                "address": start, "size_bytes": size}


def b_imm(code: int) -> int:
    value = (((code >> 31) & 1) << 12) | (((code >> 7) & 1) << 11)
    value |= (((code >> 25) & 63) << 5) | (((code >> 8) & 15) << 1)
    return sx(value, 13)


def j_imm(code: int) -> int:
    value = (((code >> 31) & 1) << 20) | (((code >> 12) & 0xFF) << 12)
    value |= (((code >> 20) & 1) << 11) | (((code >> 21) & 0x3FF) << 1)
    return sx(value, 21)


def run_function(elf: ELF32, symbol: str, a: int, b: int) -> dict[str, int]:
    pc, _ = elf.symbols[symbol]
    regs = [0] * 32
    regs[1] = RETURN_ADDRESS
    regs[10], regs[11] = u32(a), u32(b)
    instructions = 0
    branches = 0
    branch_taken = 0
    control_transfers = 0

    while True:
        if instructions >= 100:
            raise RuntimeError(f"{symbol}: possible infinite loop for ({a}, {b})")
        code = elf.read_u32(pc)
        if (code & 3) != 3:
            raise ValueError(f"Not a 32-bit RV32IM instruction at 0x{pc:08x}")
        opcode = code & 127
        rd, f3 = (code >> 7) & 31, (code >> 12) & 7
        rs1, rs2, f7 = (code >> 15) & 31, (code >> 20) & 31, (code >> 25) & 127
        next_pc = u32(pc + 4)
        value = None
        instructions += 1

        if opcode == 0x33:
            x, y = regs[rs1], regs[rs2]
            if (f7, f3) == (0, 0): value = x + y
            elif (f7, f3) == (0x20, 0): value = x - y
            elif (f7, f3) == (0, 2): value = int(sx(x, 32) < sx(y, 32))
            elif (f7, f3) == (0, 3): value = int(x < y)
            elif (f7, f3) == (0, 4): value = x ^ y
            elif (f7, f3) == (0, 6): value = x | y
            elif (f7, f3) == (0, 7): value = x & y
        elif opcode == 0x13:
            imm = sx(code >> 20, 12)
            x = regs[rs1]
            if f3 == 0: value = x + imm
            elif f3 == 2: value = int(sx(x, 32) < imm)
            elif f3 == 3: value = int(x < u32(imm))
            elif f3 == 4: value = x ^ u32(imm)
            elif f3 == 6: value = x | u32(imm)
            elif f3 == 7: value = x & u32(imm)
            elif f3 == 1 and f7 == 0: value = x << (rs2 & 31)
            elif f3 == 5 and f7 == 0: value = x >> (rs2 & 31)
            elif f3 == 5 and f7 == 0x20: value = sx(x, 32) >> (rs2 & 31)
        elif opcode == 0x63:
            x, y = regs[rs1], regs[rs2]
            branch = {
                0: x == y, 1: x != y,
                4: sx(x, 32) < sx(y, 32),
                5: sx(x, 32) >= sx(y, 32),
                6: x < y, 7: x >= y,
            }.get(f3)
            if branch is None:
                raise ValueError(f"Unsupported branch at 0x{pc:08x}")
            branches += 1
            if branch:
                branch_taken += 1
                next_pc = u32(pc + b_imm(code))
        elif opcode == 0x67 and f3 == 0:  # JALR (also RET)
            target = (regs[rs1] + sx(code >> 20, 12)) & ~1
            value = u32(pc + 4)
            control_transfers += 1
            next_pc = u32(target)
        elif opcode == 0x6F:  # JAL
            value = u32(pc + 4)
            control_transfers += 1
            next_pc = u32(pc + j_imm(code))
        elif opcode == 0x37:  # LUI
            value = code & 0xFFFFF000
        elif opcode == 0x17:  # AUIPC
            value = pc + (code & 0xFFFFF000)

        if opcode in (0x33, 0x13, 0x67, 0x6F, 0x37, 0x17) and value is None:
            raise ValueError(f"Unsupported opcode variant 0x{code:08x} at 0x{pc:08x}")
        if opcode not in (0x33, 0x13, 0x63, 0x67, 0x6F, 0x37, 0x17):
            raise ValueError(f"Unsupported opcode 0x{code:08x} at 0x{pc:08x}")
        if value is not None and rd:
            regs[rd] = u32(value)
        regs[0] = 0
        if next_pc == RETURN_ADDRESS:
            return {"result": sx(regs[10], 32), "instructions": instructions,
                    "conditional_branches": branches, "taken": branch_taken,
                    "control_transfers": control_transfers}
        pc = next_pc


def native_check() -> str:
    cc = shutil.which("cc") or shutil.which("gcc")
    if not cc:
        return "not run (no host C compiler)"
    exe = OUTPUT / "native_test_min"
    command = [cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
               str(ROOT / "src/c_baseline/min.c"), str(ROOT / "src/c_baseline/test_min.c"),
               "-o", str(exe)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    result = subprocess.run([str(exe)], check=True, capture_output=True, text=True)
    if "14/14 tests passed." not in result.stdout:
        raise AssertionError(f"Native baseline test failure:\n{result.stdout}")
    return "14/14 native C tests passed"


def prepare_cases() -> list[tuple[int, int]]:
    grid = [(x, y) for x in range(-16, 17) for y in range(-16, 17)]
    rng = random.Random(20261018)
    pairs = [(rng.randrange(-2**31, 2**31), rng.randrange(-2**31, 2**31))
             for _ in range(4096)]
    return CP1_CASES + grid + pairs


def measure(elf: ELF32) -> dict:
    for fn in FUNCTIONS:
        if fn not in elf.symbols:
            raise AssertionError(f"Missing ELF symbol {fn}")
    all_cases = prepare_cases()
    out = {"test_vectors": len(all_cases), "cp1_vectors": len(CP1_CASES),
           "generated_grid": 33 * 33, "generated_random": 4096,
           "random_seed": 20261018, "routines": {}}
    for fn in FUNCTIONS:
        stat = elf.static_metrics(fn)
        totals = {"instructions": 0, "conditional_branches": 0, "taken": 0,
                  "control_transfers": 0}
        cp1 = {"instructions": 0, "conditional_branches": 0, "taken": 0,
               "control_transfers": 0}
        lo, hi = 99999999, 0
        for i, (a, b) in enumerate(all_cases):
            trace = run_function(elf, fn, a, b)
            expected = a if a < b else b
            if trace["result"] != expected:
                raise AssertionError(f"{fn}({a}, {b}) = {trace['result']}, expected {expected}")
            lo = min(lo, trace["instructions"])
            hi = max(hi, trace["instructions"])
            for name in totals:
                totals[name] += trace[name]
                if i < len(CP1_CASES):
                    cp1[name] += trace[name]
        out["routines"][fn] = {
            "static": stat, "dynamic_cp1_14": cp1, "dynamic_all": totals,
            "min_dynamic_per_call": lo, "max_dynamic_per_call": hi,
            "all_passed": True,
        }
    return out


def md_summary(result: dict) -> str:
    rows = []
    for fn in FUNCTIONS:
        m = result["routines"][fn]
        s, d = m["static"], m["dynamic_cp1_14"]
        rows.append(f"| `{fn}` | {s['instructions']} | {s['conditional_branches']} | "
                    f"{d['instructions']} | {d['conditional_branches']} | "
                    f"{d['taken']} | {m['min_dynamic_per_call']}–{m['max_dynamic_per_call']} |")
    return "\n".join([
        "# CP2 measured instruction counts (generated)", "",
        "> Recorded with a pure-Python RV32I instruction interpreter, version 1.0,",
        "> executing real, linked RV32IM ELF32 machine code. This is NOT a pipeline",
        "> or clock-cycle simulation. Compiler/flags and machine code are in JSON.",
        "", f"Host C test: {result['native_test']}",
        f"\nAll implementations passed {result['test_vectors']} input pairs.",
        "\nStatic count is function-body instructions including `ret`;",
        "dynamic counts sum the 14 original CP1 cases (also including `ret`).",
        "Conditional branch excludes `jal`/`jalr` (`ret`) by definition.",
        "", "| Function | Static instructions | Static conditional branches | Dynamic instructions (14) | Dynamic conditional branches (14) | Taken (14) | Instructions/call across all cases |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *rows, "", "## Toolchain", "", f"- Compiler: `{result['compiler_version']}`",
        f"- Build: `{result['compile_command']}`", "",
        "## Important interpretation", "",
        "- This is a CP2 instruction-count comparison, not a cycle-count benchmark.",
        "- Instruction count alone does not prove speedup; branch behavior and pipeline matter.",
        "- A future custom instruction cannot be assigned funct3/funct7 without instructor approval.",
        "- Review and explain every generated result independently before using it in a course submission.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", help="RISC-V compiler; auto-detected by default")
    parser.add_argument("--skip-native", action="store_true", help="Skip optional host C run")
    args = parser.parse_args()
    comp = compile_rv32(args.compiler)
    elf = ELF32(comp["binary"])
    result = measure(elf)
    result["native_test"] = "skipped" if args.skip_native else native_check()
    result["compiler"] = comp["compiler"]
    result["compiler_version"] = comp["compiler_version"]
    result["compile_command"] = comp["command"]
    result["method"] = "ELF32 machine-code interpreter v1.0, RV32I subset"
    json_path = OUTPUT / "measurements.json"
    md_path = OUTPUT / "measurements.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(md_summary(result), encoding="utf-8")
    print(md_summary(result))
    print(f"Evidence saved to {json_path} and {md_path}")


if __name__ == "__main__":
    main()
