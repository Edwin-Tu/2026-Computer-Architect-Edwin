    .section .text
    .align  2
    .globl  min_s32
    .type   min_s32, @function

# int32_t min_s32(int32_t rs1, int32_t rs2)
# a0 = rs1, a1 = rs2, a0 = result
# Signed comparison is required by the MIN specification.
min_s32:
    blt     a0, a1, .Lreturn_rs1
    mv      a0, a1
.Lreturn_rs1:
    ret
    .size   min_s32, .-min_s32

    .section .note.GNU-stack,"",@progbits
