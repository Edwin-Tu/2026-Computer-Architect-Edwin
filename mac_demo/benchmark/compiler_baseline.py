"""Compiler baseline: count the loop body of dot16.c compiled with riscv64-elf-gcc -O2.

Recorded output (-O2 and -O3 identical, no unrolling):
  loop: lh, lh, addi, addi, mul, add, bne  -> 7 instructions per int16 element.
"""

import subprocess

COMPILER_PER_ELEMENT = 7
MAC2_PER_ELEMENT = 3.5


def compiler_speedup_vs_mac2() -> float:
    return COMPILER_PER_ELEMENT / MAC2_PER_ELEMENT


def compiler_loop_count(obj_path) -> int:
    dump = subprocess.run(["riscv64-elf-objdump", "-d", str(obj_path)], check=True,
                          capture_output=True, text=True).stdout
    body = []
    inside = False
    for line in dump.splitlines():
        if line.strip().endswith(">:") and "<.L3>" in line:
            inside = True
            continue
        if inside:
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            mnemonic = parts[2].split()[0]
            body.append(mnemonic)
            if mnemonic.startswith("b"):
                break
    per_element = len(body)
    return per_element
