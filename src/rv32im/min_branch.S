/* RV32IM signed minimum (educational CP2 implementation).
 * Inputs: a0 = rs1, a1 = rs2 (signed 32-bit)
 * Output: a0 = min(rs1, rs2)
 * Clobbers: a0 only.  Caller-saved ABI, no stack frame.
 */
    .text
    .balign 4
    .globl min_branch
    .type min_branch, @function
min_branch:
    blt  a0, a1, .Lbranch_done  /* retain a0 when rs1 < rs2 */
    addi a0, a1, 0              /* otherwise return rs2 */
.Lbranch_done:
    jalr zero, 0(ra)             /* ret */
    .size min_branch, .-min_branch
