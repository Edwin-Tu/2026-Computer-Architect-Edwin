"""CP3 work 2 semantics check v1.1; no compilation or cycle simulation.

Executes the preserved baseline ELF with the existing RV32I subset interpreter.
Custom MIN is a Python semantic model, not an executed custom instruction.
"""

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
MASK = 0xFFFFFFFF


def signed32(bits):
    bits &= MASK
    return bits - (1 << 32) if bits >= 0x80000000 else bits


def apply_min(regs, rd, rs1, rs2):
    a = regs[rs1] if rs1 else 0
    b = regs[rs2] if rs2 else 0
    result = a if signed32(a) < signed32(b) else b
    if rd:
        regs[rd] = result & MASK


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def parse_number(text):
    text = text.strip()
    constants = {"INT32_MIN": -(1 << 31), "INT32_MAX": (1 << 31) - 1}
    return constants[text] if text in constants else int(text)


def check_document_tables(cases):
    """Check authored examples against the existing C test table, not just the model."""
    originals = {(a, b): expected for a, b, expected in cases}
    spec = (ROOT / "spec/README.md").read_text(encoding="utf-8")
    report = (ROOT.parents[1] / "report/CP3.md").read_text(encoding="utf-8")
    spec_count = report_count = 0
    for line in spec.splitlines():
        cells = [x.strip().strip("`") for x in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not cells[0].isdigit():
            continue
        index, a, b, expected = map(int, cells[:4])
        check(1 <= index <= len(cases) and cases[index - 1] == (a, b, expected),
              f"Specification example does not match original case {index}")
        check(int(cells[4], 16) == expected & MASK, "Incorrect hex output in specification")
        spec_count += 1
    for line in report.splitlines():
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not re.fullmatch(r"-?\d+", cells[0]):
            continue
        a, b, expected = map(int, cells[:3])
        check(originals.get((a, b)) == expected, "Report example differs from original vector")
        report_count += 1
    check(spec_count == 7 and report_count == 4, "Expected 7 specification and 4 report examples")
    print(f"Document example tables: {spec_count + report_count}/11 PASS")


def main():
    source = (ROOT / "tests/test_min.c").read_text(encoding="utf-8-sig")
    rows = re.findall(r'\{"[^"]*",\s*([^,]+),\s*([^,]+),\s*([^}]+)\}', source)
    cases = [tuple(parse_number(x) for x in row) for row in rows]
    check(len(cases) == 14, "Expected the original 14 C test vectors")
    check_document_tables(cases)

    spec = importlib.util.spec_from_file_location("rv32i_semantics_baseline", ROOT / "tests/check_cp2.py")
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    evidence = ROOT / "references/validation/2026-10-23-gcc15/gcc_run_fixed"
    snapshot = evidence.parent / "source_snapshot"
    for relative in ("rv32im/min_branch.S", "c_baseline/min.c", "tests/test_min.c"):
        check((ROOT / relative).read_text(encoding="utf-8-sig") ==
              (snapshot / relative).read_text(encoding="utf-8-sig"),
              f"Current source differs from preserved snapshot: {relative}")
    binary = evidence / "min_rv32im.elf"
    metadata = json.loads((evidence / "measurements.json").read_text(encoding="utf-8-sig"))
    check(hashlib.sha256(binary.read_bytes()).hexdigest() == metadata["binary_sha256"],
          "Preserved ELF hash does not match its evidence")
    elf = baseline.ELF32(binary)
    start, size = elf.symbols["min_branch"]
    check(size == 12, "Expected three RV32I instructions in min_branch")
    codes = [elf.read_u32(start + offset) for offset in (0, 4, 8)]
    check(codes == [0x00B54463, 0x00058513, 0x00008067],
          "Saved branch machine code differs from the documented baseline")
    check(elf.static_metrics("min_branch")["instructions"] == 3,
          "Incorrect static baseline instruction count")
    print("Source snapshots + preserved ELF hash/instruction shape: PASS")
    total_ic = 0
    taken = 0
    for a, b, expected in cases:
        check(expected == min(a, b), f"Incorrect original expectation: {(a, b)}")
        result = baseline.run_function(elf, "min_branch", a, b)
        check(result["result"] == expected, f"Baseline mismatch: {(a, b)}")
        regs = [0] * 32
        regs[10], regs[11] = a & MASK, b & MASK
        apply_min(regs, 10, 10, 11)
        check(signed32(regs[10]) == expected, f"Semantic mismatch: {(a, b)}")
        total_ic += result["instructions"]
        taken += result["taken"]
    check((total_ic, taken) == (38, 4), "Original baseline path counts changed")
    print("Original C table + preserved branch ELF + custom semantic model: 14/14 PASS")
    print("Baseline: static core/function = 2/3; dynamic core/function = 24/38; taken = 4/14")

    edges = [-(1 << 31), -(1 << 31) + 1, -1, 0, 1, (1 << 31) - 2, (1 << 31) - 1]
    configurations = [(10, 10, 11), (11, 10, 11), (12, 10, 11),
                      (0, 10, 11), (12, 0, 11), (12, 10, 0), (12, 0, 0)]
    checks = 0
    for a, b in itertools.product(edges, repeat=2):
        trace = baseline.run_function(elf, "min_branch", a, b)
        check(trace["result"] == min(a, b), f"Boundary baseline mismatch: {(a, b)}")
        for rd, rs1, rs2 in configurations:
            regs = [0] * 32
            regs[10], regs[11] = a & MASK, b & MASK
            before = regs[:]
            # Independent signed conversion avoids testing signed32 against itself.
            a_signed = int.from_bytes(before[rs1].to_bytes(4, "little"), "little", signed=True)
            b_signed = int.from_bytes(before[rs2].to_bytes(4, "little"), "little", signed=True)
            expected = min(a_signed, b_signed) & MASK
            apply_min(regs, rd, rs1, rs2)
            check(regs[rd] == (expected if rd else 0), "Register writeback mismatch")
            check(all(regs[i] == before[i] for i in range(32) if i != rd),
                  "Unexpected change to another register")
            checks += 1
    print("Preserved branch ELF boundary grid: 49/49 PASS")
    print(f"Custom semantic model boundary/writeback checks: {checks}/{checks} PASS")
    print(f"Python: {sys.version.split()[0]}; semantic checker v1.1; baseline RV32I subset interpreter v1.0")
    print("No native compilation, custom-opcode execution, cycles or speedup measured.")


if __name__ == "__main__":
    main()
