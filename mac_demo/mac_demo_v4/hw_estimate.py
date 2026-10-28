"""Rough hardware cost proxy: number of multiplier partial-product bits.

An n x n array multiplier forms n*n partial-product bits. This ignores adder trees,
registers, and control, so it is only a relative indicator.
"""


def partial_products(variant: str) -> int:
    if variant == "mac":
        return 32 * 32
    if variant == "mac2":
        return 2 * 16 * 16
    raise ValueError(variant)
