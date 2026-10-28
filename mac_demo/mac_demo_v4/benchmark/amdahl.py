"""Amdahl's law: a kernel speedup diluted by the fraction of the program it covers."""


def amdahl_speedup(f: float, s: float) -> float:
    return 1.0 / ((1.0 - f) + f / s)


def dilution_table(s: float, fractions=(1.0, 0.5, 0.25)):
    return [{"fraction": f, "kernel": s, "overall": amdahl_speedup(f, s)} for f in fractions]
