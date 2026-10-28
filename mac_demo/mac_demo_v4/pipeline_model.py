"""Cycle model for a 5-stage in-order pipeline (IF, ID, EX, MEM, WB).

Assumptions:
  * Full forwarding into EX; a dependent ALU op can issue in the next cycle.
  * Load result is available only after MEM, so a load-use pair stalls 1 cycle.
  * Branches resolve in EX; predict not-taken, so each taken branch flushes 2 cycles.
  * Multiply latency is a parameter (mul_lat). MAC is a single EX-stage operation.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

FIRST_EX = 3          # IF=1, ID=2, EX=3 for the first instruction (1-indexed cycles)
TAIL = 2              # MEM and WB after the last EX
BRANCH_FLUSH = 2


@dataclass
class Ins:
    name: str
    rd: Optional[str]
    srcs: Tuple[str, ...]
    lat: int = 1          # cycles occupying EX
    ready_delay: int = 1  # cycles after EX start before rd is usable by a consumer's EX
    taken: bool = False


def ex_schedule(trace, branch_flush: int = BRANCH_FLUSH):
    """Per instruction: (ins, ex_start, data_stall_cycles, flush_bubbles)."""
    ready = {}
    ex_next = FIRST_EX
    earliest = FIRST_EX
    out = []
    for ins in trace:
        base = max(earliest, ex_next)
        t = base
        for s in ins.srcs:
            if s in ready:
                t = max(t, ready[s])
        if ins.rd is not None:
            ready[ins.rd] = t + ins.lat - 1 + ins.ready_delay
        flush_bubbles = max(0, earliest - ex_next)
        out.append((ins, t, t - base, flush_bubbles))
        if ins.taken:
            earliest = t + 1 + branch_flush
        ex_next = t + ins.lat
    return out


def simulate(trace, branch_flush: int = BRANCH_FLUSH) -> int:
    """Return total cycles to retire the trace."""
    sched = ex_schedule(trace, branch_flush)
    last_ex = sched[-1][1] if sched else FIRST_EX - 1
    return last_ex + TAIL


def _alu(rd, *srcs):
    return Ins("alu", rd, srcs)


def standard_loop_body(last: bool, mul_lat: int):
    """One iteration of: c[i] += a[i] * b[i] with RV32IM."""
    return [
        Ins("lw", "t0", ("a0",), ready_delay=2),
        Ins("lw", "t1", ("a1",), ready_delay=2),
        Ins("mul", "t2", ("t0", "t1"), lat=mul_lat),
        _alu("t3", "t3", "t2"),
        _alu("a0", "a0"),
        _alu("a1", "a1"),
        _alu("a2", "a2"),
        Ins("bnez", None, ("a2",), taken=not last),
    ]


def mac_loop_body(last: bool, mac_lat: int = 1):
    """One iteration of the same loop using mac t3, t0, t1."""
    return [
        Ins("lw", "t0", ("a0",), ready_delay=2),
        Ins("lw", "t1", ("a1",), ready_delay=2),
        Ins("mac", "t3", ("t3", "t0", "t1"), lat=mac_lat),
        _alu("a0", "a0"),
        _alu("a1", "a1"),
        _alu("a2", "a2"),
        Ins("bnez", None, ("a2",), taken=not last),
    ]


def loop_trace(body_fn, n: int, **kw):
    trace = []
    for i in range(n):
        trace.extend(body_fn(last=(i == n - 1), **kw))
    return trace


def compare(n: int, mul_lat: int):
    std = simulate(loop_trace(standard_loop_body, n, mul_lat=mul_lat))
    mac = simulate(loop_trace(mac_loop_body, n))
    return std, mac


if __name__ == "__main__":
    N = 1000
    print(f"Dot product, N={N}")
    print(f"{'mul_lat':>8} {'std cycles':>12} {'mac cycles':>12} {'reduction':>12} {'pct':>8}")
    for mul_lat in (1, 3, 5):
        std, mac = compare(N, mul_lat)
        print(f"{mul_lat:>8} {std:>12} {mac:>12} {std - mac:>12} {(std - mac) / std * 100:>7.1f}%")

    print()
    print("Clock-period sensitivity (mul_lat=1, MAC cycle time = k x baseline):")
    std, mac = compare(N, 1)
    for k in (1.0, 1.1, 1.2, 1.5):
        t_std = std * 1.0
        t_mac = mac * k
        print(f"  k={k:<4} time ratio mac/std = {t_mac / t_std:.3f}  speedup = {t_std / t_mac:.3f}")


def compare_mac_latency(n: int, mac_lats=(1, 2, 3), mul_lat: int = 1):
    std = simulate(loop_trace(standard_loop_body, n, mul_lat=mul_lat))
    rows = []
    for lat in mac_lats:
        mac = simulate(loop_trace(mac_loop_body, n, mac_lat=lat))
        rows.append({"mac_lat": lat, "std_cycles": std, "mac_cycles": mac,
                     "speedup": std / mac})
    return rows


PACKED_BODY = {"std_lh", "mac2"}


def packed_loop_trace(variant: str, n_words: int, mac2_lat: int = 1):
    """Pipeline trace of the INT16 packed dot product, two lanes per 32-bit word."""
    if variant not in PACKED_BODY:
        raise ValueError(variant)
    trace = []
    for i in range(n_words):
        last = i == n_words - 1
        if variant == "std_lh":
            body = [
                Ins("lh", "t0", ("a0",), ready_delay=2),
                Ins("lh", "t1", ("a3",), ready_delay=2),
                Ins("lh", "t2", ("a0",), ready_delay=2),
                Ins("lh", "t3", ("a3",), ready_delay=2),
                Ins("mul", "t4", ("t0", "t1")),
                Ins("mul", "t6", ("t2", "t3")),
                _alu("t5", "t5", "t4"),
                _alu("t5", "t5", "t6"),
            ]
        else:
            body = [
                Ins("lw", "t0", ("a0",), ready_delay=2),
                Ins("lw", "t1", ("a3",), ready_delay=2),
                Ins("mac2", "t5", ("t5", "t0", "t1"), lat=mac2_lat),
            ]
        body += [
            _alu("a0", "a0"),
            _alu("a3", "a3"),
            _alu("a2", "a2"),
            Ins("bnez", None, ("a2",), taken=not last),
        ]
        trace.extend(body)
    return trace


def scalar_int16_trace(variant: str, n: int, mac_lat: int = 1):
    """Pipeline trace of a scalar INT16 dot product (one element per iteration)."""
    if variant not in ("std", "mac"):
        raise ValueError(variant)
    trace = []
    for i in range(n):
        last = i == n - 1
        body = [
            Ins("lh", "t0", ("a0",), ready_delay=2),
            Ins("lh", "t1", ("a3",), ready_delay=2),
        ]
        if variant == "std":
            body += [Ins("mul", "t4", ("t0", "t1")), _alu("t5", "t5", "t4")]
        else:
            body += [Ins("mac", "t5", ("t5", "t0", "t1"), lat=mac_lat)]
        body += [
            _alu("a0", "a0"),
            _alu("a3", "a3"),
            _alu("a2", "a2"),
            Ins("bnez", None, ("a2",), taken=not last),
        ]
        trace.extend(body)
    return trace
