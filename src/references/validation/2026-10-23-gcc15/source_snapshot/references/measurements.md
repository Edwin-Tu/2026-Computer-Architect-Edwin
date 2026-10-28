# CP2 measured instruction counts (generated)

> Recorded with a pure-Python RV32I instruction interpreter, version 1.0,
> executing real, linked RV32IM ELF32 machine code. This is NOT a pipeline
> or clock-cycle simulation. Compiler/flags and machine code are in JSON.

Host C test: 14/14 native C tests passed

All implementations passed 5199 input pairs.

Static count is function-body instructions including `ret`;
dynamic counts sum the 14 original CP1 cases (also including `ret`).
Conditional branch excludes `jal`/`jalr` (`ret`) by definition.

| Function | Static instructions | Static conditional branches | Dynamic instructions (14) | Dynamic conditional branches (14) | Taken (14) | Instructions/call across all cases |
|---|---:|---:|---:|---:|---:|---:|
| `min_s32` | 4 | 1 | 46 | 14 | 10 | 3–4 |
| `min_branch` | 3 | 1 | 38 | 14 | 4 | 2–3 |
| `min_branchless` | 6 | 0 | 84 | 0 | 0 | 6–6 |

## Toolchain

- Compiler: `riscv64-elf-gcc (GCC) 16.2.0`
- Build: `riscv64-elf-gcc -march=rv32im -mabi=ilp32 -O2 -ffreestanding -fno-builtin -fno-pic -fno-pie -nostdlib -Wl,-e,min_branch -Wl,-Ttext=0x10000 -Wl,--no-relax -o /Users/liuxingyuan/Desktop/CP2_RECORD_20261018_131340/build/min_rv32im.elf /Users/liuxingyuan/Desktop/CP2_RECORD_20261018_131340/src/c_baseline/min.c /Users/liuxingyuan/Desktop/CP2_RECORD_20261018_131340/src/rv32im/min_branch.S /Users/liuxingyuan/Desktop/CP2_RECORD_20261018_131340/src/rv32im/min_branchless.S`

## Important interpretation

- This is a CP2 instruction-count comparison, not a cycle-count benchmark.
- Instruction count alone does not prove speedup; branch behavior and pipeline matter.
- A future custom instruction cannot be assigned funct3/funct7 without instructor approval.
- Review and explain every generated result independently before using it in a course submission.
