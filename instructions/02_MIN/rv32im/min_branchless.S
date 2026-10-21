/* RV32IM signed minimum without a conditional branch.
 * Inputs: a0 = rs1, a1 = rs2 (signed 32-bit)
 * Output: a0 = min(rs1, rs2)
 * Clobbers: a0, t0, t1 (all caller-saved).
 * This is an alternative for branch trade-off analysis, not an assertion
 * that this routine is faster than a conditional-branch implementation.
 */
    .text
    .balign 4
    .globl min_branchless
    .type min_branchless, @function
min_branchless:
    slt  t0, a0, a1       /* t0 = 1 iff rs1 < rs2 (SIGNED) */
    sub  t0, zero, t0     /* t0 = 0xFFFFFFFF if true, else 0 */
    xor  t1, a0, a1       /* bits differing between operands */
    and  t1, t1, t0       /* select differences when rs1 is smaller */
    xor  a0, a1, t1       /* choose rs1 if smaller; else rs2 */
    jalr zero, 0(ra)
    .size min_branchless, .-min_branchless
