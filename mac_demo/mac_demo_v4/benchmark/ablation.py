"""Ablation of the MAC strategies, measured against the configurations of base, v2, v3, v4.

Each row changes one factor relative to the row above it.
  instr: instruction-count speedup (per element or per word, as defined by each row)
  pipe : pipeline cycle speedup (None when the row has no pipeline model)
"""

from benchmark.compiler_baseline import COMPILER_PER_ELEMENT
from benchmark.dotbench import instruction_count
from benchmark.packed import BODY, LOOP_OVERHEAD
from pipeline_model import packed_loop_trace, scalar_int16_trace, simulate


def _instr_ratio(std_body, cus_body):
    return (std_body + LOOP_OVERHEAD) / (cus_body + LOOP_OVERHEAD)


def ablation_rows(n_words: int = 1024):
    n = 2 * n_words
    std_pipe = simulate(packed_loop_trace("std_lh", n_words))
    mac2_lat1 = simulate(packed_loop_trace("mac2", n_words, mac2_lat=1))
    mac2_lat2 = simulate(packed_loop_trace("mac2", n_words, mac2_lat=2))
    scalar_std = simulate(scalar_int16_trace("std", n))
    scalar_mac = simulate(scalar_int16_trace("mac", n))
    return [
        {"id": "A0", "config": "base(v1):scalar mac,INT32,展開 1,手寫 lw 基準",
         "instr": instruction_count("standard", 1024) / instruction_count("mac", 1024),
         "pipe": None},
        {"id": "A1", "config": "+ 展開 4(v2)",
         "instr": instruction_count("standard", 1024, unroll=4) / instruction_count("mac", 1024, unroll=4),
         "pipe": None},
        {"id": "A2", "config": "+ 封包 mac2(v3),INT16,手寫 lh 基準",
         "instr": _instr_ratio(BODY["std_lh"], BODY["mac2"]),
         "pipe": std_pipe / mac2_lat1},
        {"id": "A3", "config": "+ 編譯器 -O2 基準(取代手寫 lh)",
         "instr": COMPILER_PER_ELEMENT / 3.5,
         "pipe": None},
        {"id": "A4", "config": "+ 管線模型(v4),mac2 延遲 1 拍 [完整配置]",
         "instr": _instr_ratio(BODY["std_lh"], BODY["mac2"]),
         "pipe": std_pipe / mac2_lat1},
        {"id": "A5", "config": "A4 + mac2 延遲 2 拍",
         "instr": _instr_ratio(BODY["std_lh"], BODY["mac2"]),
         "pipe": std_pipe / mac2_lat2},
        {"id": "A6", "config": "A4 + 週期時間比 1.2",
         "instr": _instr_ratio(BODY["std_lh"], BODY["mac2"]) / 1.2,
         "pipe": (std_pipe / mac2_lat1) / 1.2},
        {"id": "B1", "config": "移除封包:標量 mac(INT16,每元素一次迭代),管線",
         "instr": 8 / 7,
         "pipe": scalar_std / scalar_mac},
    ]
