"""Class-based CPI model for the dot-product loop (no pipeline).

Each mix is a list of (instruction, CPI, count) per element.
cycles_per_element = sum(CPI * count); CPU Time ratio = (cycles_mac * T_mac) / (cycles_std * T_std).
"""

LOAD_CPI = 2
ALU_CPI = 1
BRANCH_CPI = 1


def mix_standard(mul_cpi: int):
    return [
        ("lw", LOAD_CPI, 2),
        ("mul", mul_cpi, 1),
        ("add", ALU_CPI, 1),
        ("addi", ALU_CPI, 3),
        ("bnez", BRANCH_CPI, 1),
    ]


def mix_mac(mac_cpi: int):
    return [
        ("lw", LOAD_CPI, 2),
        ("mac", mac_cpi, 1),
        ("addi", ALU_CPI, 3),
        ("bnez", BRANCH_CPI, 1),
    ]


def cycles_per_element(mix) -> int:
    return sum(cpi * n for _, cpi, n in mix)


def breakeven_ratio(mul_cpi: int, mac_cpi: int) -> float:
    """Largest T_mac / T_std at which the MAC version still ties on CPU Time."""
    return cycles_per_element(mix_standard(mul_cpi)) / cycles_per_element(mix_mac(mac_cpi))


def cpu_time_ratio(mul_cpi: int, mac_cpi: int, t_ratio: float) -> float:
    """CPU Time of MAC divided by CPU Time of standard (below 1 means MAC is faster)."""
    return cycles_per_element(mix_mac(mac_cpi)) * t_ratio / cycles_per_element(mix_standard(mul_cpi))
