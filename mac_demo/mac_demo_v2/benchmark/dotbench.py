"""Dot-product benchmark: standard RV32IM loop vs MAC loop (no pipeline model).

CPU Time = Instruction Count x CPI x Clock Cycle Time.
Instruction counts are the loop-body counts from mac_encoding.instruction_count_per_element.
"""

import csv
import io
import random

from mac_encoding import dot_product_golden, instruction_count_per_element, mac_golden

SEED = 2026
CPI_DEFAULT = 1.0
RATIOS = (1.0, 1.1, 1.2)

WORKLOADS = [
    {"id": "B1", "kind": "full_range", "n": 64},
    {"id": "B1", "kind": "full_range", "n": 256},
    {"id": "B1", "kind": "full_range", "n": 1024},
    {"id": "B2", "kind": "int8", "n": 64},
    {"id": "B2", "kind": "int8", "n": 256},
    {"id": "B2", "kind": "int8", "n": 1024},
    {"id": "B3", "kind": "edge", "n": 64},
]


def make_inputs(kind: str, n: int, seed: int = SEED):
    rng = random.Random(seed)
    if kind == "full_range":
        a = [rng.randint(-(2**31), 2**31 - 1) for _ in range(n)]
        b = [rng.randint(-(2**31), 2**31 - 1) for _ in range(n)]
    elif kind == "int8":
        a = [rng.randint(-128, 127) for _ in range(n)]
        b = [rng.randint(-128, 127) for _ in range(n)]
    elif kind == "edge":
        a = [2**31 - 1 if i % 2 == 0 else -(2**31) for i in range(n)]
        b = [-(2**31) if i % 2 == 0 else 2**31 - 1 for i in range(n)]
    else:
        raise ValueError(kind)
    return a, b


LOOP_OVERHEAD = 4  # two pointer increments, counter decrement, bnez


def body_per_element(variant: str) -> int:
    per = instruction_count_per_element()
    key = {"standard": "standard_rv32im", "mac": "custom_mac"}[variant]
    return per[key] - LOOP_OVERHEAD


def instruction_count(variant: str, n: int, unroll: int = 1) -> int:
    if n % unroll:
        raise ValueError("n must be a multiple of unroll")
    return n * body_per_element(variant) + (n // unroll) * LOOP_OVERHEAD


def cpu_time(ic: int, cpi: float, t: float) -> float:
    return ic * cpi * t


def _mac_loop(a, b):
    acc = 0
    for x, y in zip(a, b):
        acc = mac_golden(acc, x, y)
    return acc


def run_case(kind: str, n: int, t_ratio: float = 1.0, cpi: float = CPI_DEFAULT,
             seed: int = SEED, workload_id: str = "", unroll: int = 1) -> dict:
    a, b = make_inputs(kind, n, seed)
    correct = _mac_loop(a, b) == dot_product_golden(a, b)
    ic_std = instruction_count("standard", n, unroll)
    ic_mac = instruction_count("mac", n, unroll)
    cpu_std = cpu_time(ic_std, cpi, 1.0)
    cpu_mac = cpu_time(ic_mac, cpi, t_ratio)
    return {
        "workload": workload_id or kind,
        "kind": kind,
        "n": n,
        "unroll": unroll,
        "t_ratio": t_ratio,
        "ic_std": ic_std,
        "ic_mac": ic_mac,
        "correct": correct,
        "cpu_std": cpu_std,
        "cpu_mac": cpu_mac,
        "speedup": cpu_std / cpu_mac,
    }


def run_all(ratios=RATIOS, cpi: float = CPI_DEFAULT, unroll: int = 1) -> list:
    rows = []
    for t in ratios:
        for w in WORKLOADS:
            rows.append(run_case(w["kind"], w["n"], t_ratio=t, cpi=cpi,
                                 workload_id=w["id"], unroll=unroll))
    return rows


FIELDS = ["workload", "kind", "n", "unroll", "t_ratio", "ic_std", "ic_mac", "correct",
          "cpu_std", "cpu_mac", "speedup"]


def to_csv(rows) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in FIELDS})
    return buf.getvalue()


def to_markdown(rows) -> str:
    head = "| 工作負載 | 類型 | N | T 比 | 標準 IC | MAC IC | 正確性 | 標準 CPU Time | MAC CPU Time | 加速比 |"
    sep = "|---|---|---:|---:|---:|---:|:---:|---:|---:|---:|"
    lines = [head, sep]
    for r in rows:
        lines.append(
            f"| {r['workload']} | {r['kind']} | {r['n']} | {r['t_ratio']:.1f} | {r['ic_std']} | "
            f"{r['ic_mac']} | {'OK' if r['correct'] else 'FAIL'} | {r['cpu_std']:.0f} | "
            f"{r['cpu_mac']:.1f} | {r['speedup']:.2f}x |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import pathlib

    rows = run_all()
    out = pathlib.Path(__file__).resolve().parent
    (out / "results.csv").write_text(to_csv(rows))
    (out / "results.md").write_text(to_markdown(rows))
    print(to_markdown(rows))
