"""MAC custom instruction: encoding, golden model, and instruction-count comparison.

Instruction:  mac rd, rs1, rs2   ->   rd = rd + rs1 * rs2   (32-bit, low 32 bits)
Format:       R-type on custom-0 opcode (0b0001011 = 0x0B)
"""

OPCODE_CUSTOM0 = 0b0001011
FUNCT3_MAC = 0b000
FUNCT7_MAC = 0b0000000
MASK32 = 0xFFFF_FFFF


def encode_mac(rd: int, rs1: int, rs2: int) -> int:
    for name, r in (("rd", rd), ("rs1", rs1), ("rs2", rs2)):
        if not 0 <= r <= 31:
            raise ValueError(f"{name} out of range: {r}")
    return (
        (FUNCT7_MAC << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (FUNCT3_MAC << 12)
        | (rd << 7)
        | OPCODE_CUSTOM0
    )


def decode_mac(word: int):
    """Return (rd, rs1, rs2) if the word is a MAC instruction, else None."""
    if word & 0x7F != OPCODE_CUSTOM0:
        return None
    if (word >> 12) & 0x7 != FUNCT3_MAC or (word >> 25) != FUNCT7_MAC:
        return None
    return (word >> 7) & 0x1F, (word >> 15) & 0x1F, (word >> 20) & 0x1F


def mac_golden(acc: int, a: int, b: int) -> int:
    """Golden model: rd = acc + a*b, wrapped to signed 32-bit."""
    v = (acc + a * b) & MASK32
    return v - (1 << 32) if v & 0x8000_0000 else v


def dot_product_golden(a, b) -> int:
    acc = 0
    for x, y in zip(a, b):
        acc = mac_golden(acc, x, y)
    return acc


def instruction_count_per_element():
    """Dynamic instructions in the inner loop, per element.

    Standard RV32IM:  lw, lw, mul, add, addi(a), addi(b), addi(n), bnez  -> 8
    With MAC:         lw, lw, mac,       addi(a), addi(b), addi(n), bnez  -> 7
    """
    return {"standard_rv32im": 8, "custom_mac": 7}


if __name__ == "__main__":
    import sys

    word = encode_mac(10, 11, 12)  # mac a0, a1, a2
    print(f"mac a0, a1, a2  ->  0x{word:08x}  {word:032b}")
    print("decode:", decode_mac(word))

    n = 1000
    counts = instruction_count_per_element()
    std, cus = counts["standard_rv32im"] * n, counts["custom_mac"] * n
    print(f"N={n}: standard={std} instr, custom={cus} instr, "
          f"reduction={(1 - cus / std) * 100:.1f}%")
    sys.exit(0)


FUNCT3_MAC_R4 = 0b001


def encode_mac_r4(rd: int, rs1: int, rs2: int, rs3: int) -> int:
    """R4-form variant: rd = rs3 + rs1 * rs2 (funct2 = 0, funct3 = 1)."""
    for name, r in (("rd", rd), ("rs1", rs1), ("rs2", rs2), ("rs3", rs3)):
        if not 0 <= r <= 31:
            raise ValueError(f"{name} out of range: {r}")
    return (
        (rs3 << 27)
        | (0 << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (FUNCT3_MAC_R4 << 12)
        | (rd << 7)
        | OPCODE_CUSTOM0
    )


def decode_mac_r4(word: int):
    """Return (rd, rs1, rs2, rs3) for an R4-form MAC word, else None."""
    if word & 0x7F != OPCODE_CUSTOM0:
        return None
    if (word >> 12) & 0x7 != FUNCT3_MAC_R4 or (word >> 25) & 0x3 != 0:
        return None
    return (
        (word >> 7) & 0x1F,
        (word >> 15) & 0x1F,
        (word >> 20) & 0x1F,
        (word >> 27) & 0x1F,
    )


def apply_mac(regs, rd: int, rs1: int, rs2: int) -> None:
    """Architectural effect of `mac rd, rs1, rs2` on a 32-entry register file.

    Reads of x0 return 0 and writes to x0 are discarded.
    """
    regs[0] = 0
    if rd == 0:
        return
    regs[rd] = mac_golden(regs[rd], regs[rs1], regs[rs2])


FUNCT3_MAC2 = 0b010


def encode_mac2(rd: int, rs1: int, rs2: int) -> int:
    """Packed dual-16-bit form: rd = rd + lo16(rs1)*lo16(rs2) + hi16(rs1)*hi16(rs2)."""
    for name, r in (("rd", rd), ("rs1", rs1), ("rs2", rs2)):
        if not 0 <= r <= 31:
            raise ValueError(f"{name} out of range: {r}")
    return (FUNCT7_MAC << 25) | (rs2 << 20) | (rs1 << 15) | (FUNCT3_MAC2 << 12) | (rd << 7) | OPCODE_CUSTOM0


def decode_mac2(word: int):
    """Return (rd, rs1, rs2) for a packed MAC word, else None."""
    if word & 0x7F != OPCODE_CUSTOM0:
        return None
    if (word >> 12) & 0x7 != FUNCT3_MAC2 or (word >> 25) != FUNCT7_MAC:
        return None
    return (word >> 7) & 0x1F, (word >> 15) & 0x1F, (word >> 20) & 0x1F


def _sext16(x: int) -> int:
    x &= 0xFFFF
    return x - 0x10000 if x & 0x8000 else x


def mac2_golden(acc: int, a: int, b: int) -> int:
    """Dual 16-bit signed lanes: acc + lo*lo + hi*hi, wrapped to signed 32-bit."""
    lo = _sext16(a) * _sext16(b)
    hi = _sext16(a >> 16) * _sext16(b >> 16)
    return mac_golden(acc, lo + hi, 1)
