"""INT16 dot product with two 16-bit lanes per 32-bit word.

Standard RV32IM baselines:
  std_lh : four halfword loads, two mul, two add            -> body 8
  std_lw : two word loads, sign-extract four lanes, two mul, two add -> body 12
Custom: mac2 on packed words: two word loads + mac2          -> body 3
Loop overhead per word: 4 (two pointer increments, counter, bnez).
"""

import random

from mac_encoding import dot_product_golden, mac2_golden  # noqa: F401  (re-exported for callers)

LOOP_OVERHEAD = 4
BODY = {"std_lh": 8, "std_lw": 12, "mac2": 3}
PACKED_WORKLOADS = (64, 256, 1024)


def pack(lo: int, hi: int) -> int:
    return ((hi & 0xFFFF) << 16) | (lo & 0xFFFF)


def make_int16_words(n_words: int, seed: int = 2026):
    rng = random.Random(seed)
    a16 = [rng.randint(-32768, 32767) for _ in range(2 * n_words)]
    b16 = [rng.randint(-32768, 32767) for _ in range(2 * n_words)]
    a_words = [pack(a16[2 * i], a16[2 * i + 1]) for i in range(n_words)]
    b_words = [pack(b16[2 * i], b16[2 * i + 1]) for i in range(n_words)]
    return a_words, b_words, a16, b16


def dot16_reference(a16, b16) -> int:
    acc = 0
    for x, y in zip(a16, b16):
        acc = (acc + x * y) & 0xFFFFFFFF
    return acc - (1 << 32) if acc & 0x80000000 else acc


def packed_counts(variant: str, n_words: int) -> int:
    return n_words * (BODY[variant] + LOOP_OVERHEAD)


def run_packed_case(n_words: int, t_ratio: float = 1.0, seed: int = 2026) -> dict:
    a_words, b_words, a16, b16 = make_int16_words(n_words, seed)
    acc = 0
    for x, y in zip(a_words, b_words):
        acc = mac2_golden(acc, x, y)
    correct = acc == dot16_reference(a16, b16)
    ic_lh = packed_counts("std_lh", n_words)
    ic_lw = packed_counts("std_lw", n_words)
    ic_mac2 = packed_counts("mac2", n_words)
    return {
        "n_words": n_words,
        "t_ratio": t_ratio,
        "ic_std_lh": ic_lh,
        "ic_std_lw": ic_lw,
        "ic_mac2": ic_mac2,
        "correct": correct,
        "speedup_lh": ic_lh / (ic_mac2 * t_ratio),
        "speedup_lw": ic_lw / (ic_mac2 * t_ratio),
    }


def run_packed_all(ratios=(1.0, 1.1, 1.2)):
    return [run_packed_case(n, t_ratio=t) for t in ratios for n in PACKED_WORKLOADS]
