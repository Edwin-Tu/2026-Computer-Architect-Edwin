#!/usr/bin/env python3
"""CP2 RV32IM validation and deterministic instruction tracing, version 1.2.1.

Compiles actual RV32IM machine code (ELF32), executes the MIN routines in a
small pure-Python RV32I subset interpreter, and records static/dynamic counts.
Does NOT model pipelines, caches, CPI, clock cycles, or physical runtime.
No third-party Python packages are necessary.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import platform
import re
import sys
import uuid
import json
import random
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT: Path | None = None
SOURCE_FILES = ("c_baseline/min.c", "c_baseline/min.h", "tests/test_min.c",
                "rv32im/min_branch.S", "rv32im/min_branchless.S", "tests/check_cp2.py")
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


def validate_sources() -> dict[str, str]:
    missing = [name for name in SOURCE_FILES if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing source files: " + ", ".join(missing))
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


def run_command(command: list[str], log_name: str) -> subprocess.CompletedProcess:
    if OUTPUT is None:
        raise RuntimeError("Output directory is not initialized")
    log = OUTPUT / log_name
    with log.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(command, ensure_ascii=False) + "\n")
    try:
        result = subprocess.run(command, cwd=OUTPUT, capture_output=True, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        with log.open("a", encoding="utf-8") as stream:
            stream.write(f"Launch failure: {exc}\n")
        raise RuntimeError(f"Could not run command; see {log}: {exc}") from exc
    # Preserve original bytes as well as readable UTF-8 logs (compiler locales differ).
    for suffix, data in (("stdout.bin", result.stdout), ("stderr.bin", result.stderr)):
        with (OUTPUT / (log_name + "." + suffix)).open("xb") as raw:
            raw.write(data)
    result.stdout = result.stdout.decode("utf-8", errors="replace")
    result.stderr = result.stderr.decode("utf-8", errors="replace")
    with log.open("a", encoding="utf-8") as stream:
        stream.write(f"exit_code={result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    if result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}); see {log}")
    return result


def compile_rv32(compiler: str | None) -> dict[str, str]:
    if compiler is None:
        compiler = next((shutil.which(name) for name in (
            "riscv64-unknown-elf-gcc", "riscv64-elf-gcc",
            "riscv32-unknown-elf-gcc", "clang"
        ) if shutil.which(name)), None)
    if compiler is None:
        raise RuntimeError("RISC-V build NOT RUN: no RISC-V GCC or Clang/LLD available")
    target = OUTPUT / "min_rv32im.elf"
    command = [compiler]
    if Path(compiler).name.lower().startswith("clang"):
        command += ["--target=riscv32-unknown-elf", "-fuse-ld=lld"]
    command += [
        "-march=rv32im", "-mabi=ilp32", "-O2", "-ffreestanding",
        "-fno-builtin", "-fno-pic", "-fno-pie", "-nostdlib",
        "-Wl,-e,min_branch", "-Wl,-Ttext=0x10000", "-Wl,--no-relax",
        "-o", str(target), str(ROOT / "c_baseline/min.c"),
        str(ROOT / "rv32im/min_branch.S"), str(ROOT / "rv32im/min_branchless.S"),
    ]
    run_command(command, "rv32_build.log")
    if not target.is_file():
        raise RuntimeError("Compiler returned success without creating the new ELF; NOT PASS")
    version = run_command([compiler, "--version"], "rv32_compiler.log")
    return {"binary": str(target), "compiler": compiler,
            "compiler_version": version.stdout.splitlines()[0] if version.stdout else "unknown",
            "command": " ".join(command), "command_argv": command}


class ELF32:
    """Minimal ELF32 LE reader: only the fields needed for linked RISC-V ELF."""

    def __init__(self, path: str | Path):
        self.data = Path(path).read_bytes()
        d = self.data
        if len(d) < 52 or d[:4] != b"\x7fELF" or d[4] != 1 or d[5] != 1:
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
            if flags & 1 and addr % 4 == 0 and begin <= addr and addr + 4 <= end:
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


def run_function(elf: ELF32, symbol: str, a: int, b: int, initial_seed: int = 1) -> dict[str, int]:
    pc, _ = elf.symbols[symbol]
    regs = [u32(0x13579BDF ^ (i * 0x1020304) ^ initial_seed) for i in range(32)]
    regs[0] = 0
    regs[2] = 0x60000000
    regs[1] = RETURN_ADDRESS
    regs[10], regs[11] = u32(a), u32(b)
    preserved = {i: regs[i] for i in (2, 3, 4, 8, 9, *range(18, 28))}
    instructions = 0
    branches = 0
    branch_taken = 0
    control_transfers = 0

    while True:
        if instructions >= 100:
            raise RuntimeError(f"{symbol}: possible infinite loop for ({a}, {b})")
        if pc % 4:
            raise ValueError(f"{symbol}: unaligned instruction PC: 0x{pc:08x}")
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
            # Check architectural control flow, not one preferred ret encoding.
            # Alternate source/destination registers or an executable helper are allowed.
            if opcode not in (0x63, 0x67, 0x6F):
                raise AssertionError(f"{symbol}: return sentinel reached without control transfer")
            changed = [i for i, original in preserved.items() if regs[i] != original]
            if changed:
                raise AssertionError(f"{symbol}: ABI preserved registers changed: {changed}")
            return {"result": sx(regs[10], 32), "instructions": instructions,
                    "conditional_branches": branches, "taken": branch_taken,
                    "control_transfers": control_transfers}
        pc = next_pc


def native_check(compiler: str | None = None) -> str:
    cc = compiler or next((shutil.which(name) for name in ("cc", "gcc", "clang")
                           if shutil.which(name)), None)
    if not cc:
        raise RuntimeError("Native C test NOT RUN: no cc/gcc/clang; use --skip-native only for an explicit skip")
    exe = OUTPUT / ("native_test_min.exe" if os.name == "nt" else "native_test_min")
    command = [cc, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
               "-I", str(ROOT / "c_baseline"), str(ROOT / "c_baseline/min.c"),
               str(ROOT / "tests/test_min.c"), "-o", str(exe)]
    run_command([cc, "--version"], "native_compiler.log")
    run_command(command, "native_build.log")
    result = run_command([str(exe)], "native_test.log")
    if (len(re.findall(r"^\[PASS\]", result.stdout, re.MULTILINE)) != 14
            or "[FAIL]" in result.stdout
            or "Result: 14/14 tests passed." not in result.stdout.splitlines()):
        raise AssertionError("Native test did not report 14 successful original cases; see native_test.log")
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
            trace = run_function(elf, fn, a, b, initial_seed=i + 1)
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
        "> Recorded with a pure-Python RV32I instruction interpreter, version 1.2.1,",
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
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", help="RISC-V GCC or clang; auto-detected by default")
    parser.add_argument("--host-compiler", help="Host cc/gcc/clang; auto-detected by default")
    parser.add_argument("--skip-native", action="store_true", help="Explicitly skip host C, never reported as PASS")
    parser.add_argument("--output-dir", type=Path, help="New directory only; existing directories are rejected")
    parser.add_argument("--source-version", default="unrecorded", help="Source commit/snapshot label")
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUTPUT = (args.output_dir or ROOT / "build" / (stamp + "_" + uuid.uuid4().hex[:8])).resolve()
    if OUTPUT.exists():
        parser.error(f"Output directory already exists; refusing overwrite: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    status = {"status": "running", "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_version": args.source_version, "python": sys.version, "platform": platform.platform(),
              "argv": sys.argv, "root": str(ROOT), "output": str(OUTPUT),
              "native_test": "not run", "rv32_test": "not run"}
    def save_status():
        (OUTPUT / "run_status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    save_status()
    try:
        status["source_sha256"] = validate_sources()
        save_status()
        status["native_test"] = "skipped (explicit --skip-native; NOT PASS)" if args.skip_native else native_check(args.host_compiler)
        save_status()
        comp = compile_rv32(args.compiler)
        elf = ELF32(comp["binary"])
        result = measure(elf)
        status["rv32_test"] = "5199/5199 per function passed (interpreter, not cycles)"
        if validate_sources() != status["source_sha256"]:
            raise RuntimeError("Source files changed during validation; refusing mixed-version evidence")
        result.update(native_test=status["native_test"], compiler=comp["compiler"],
                      compiler_version=comp["compiler_version"], compile_command=comp["command"],
                      compile_argv=comp["command_argv"],
                      method="ELF32 machine-code interpreter v1.2.1, RV32I subset; preserved-register/return-target checks",
                      source_version=args.source_version, created_utc=status["created_utc"],
                      source_sha256=status["source_sha256"], python=sys.version, platform=platform.platform(),
                      binary_sha256=hashlib.sha256(Path(comp["binary"]).read_bytes()).hexdigest())
        for name, value in (("measurements.json", json.dumps(result, indent=2, ensure_ascii=False) + "\n"),
                            ("measurements.md", md_summary(result))):
            (OUTPUT / name).write_text(value, encoding="utf-8")
        status["status"] = "completed_with_native_skip" if args.skip_native else "passed"
        save_status()
        print(md_summary(result))
        print(f"New evidence saved to {OUTPUT}; historical references were not overwritten")
    except Exception as exc:
        status["status"] = "failed"
        status["error"] = f"{type(exc).__name__}: {exc}"
        save_status()
        print(f"FAILED; NOT an overall PASS: {exc}\nRun record: {OUTPUT / 'run_status.json'}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
