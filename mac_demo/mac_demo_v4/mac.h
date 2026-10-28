#ifndef MAC_H
#define MAC_H

#include <stddef.h>
#include <stdint.h>

/* mac rd, rs1, rs2 : rd = rd + rs1 * rs2  (custom-0, R-type, funct3=0, funct7=0) */
static inline uint32_t mac_insn(uint32_t acc, uint32_t a, uint32_t b)
{
#if defined(__riscv)
    __asm__ volatile(".insn r 0x0b, 0, 0, %0, %1, %2"
                     : "+r"(acc)
                     : "r"(a), "r"(b));
    return acc;
#else
    return acc + a * b;
#endif
}

int32_t dot_ref(const int32_t *a, const int32_t *b, size_t n);
int32_t dot_mac(const int32_t *a, const int32_t *b, size_t n);

#endif
