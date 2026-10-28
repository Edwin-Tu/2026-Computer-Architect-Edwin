#include "mac.h"

int32_t dot_ref(const int32_t *a, const int32_t *b, size_t n)
{
    uint32_t acc = 0;
    for (size_t i = 0; i < n; i++)
        acc = acc + (uint32_t)a[i] * (uint32_t)b[i];
    return (int32_t)acc;
}

int32_t dot_mac(const int32_t *a, const int32_t *b, size_t n)
{
    uint32_t acc = 0;
    for (size_t i = 0; i < n; i++)
        acc = mac_insn(acc, (uint32_t)a[i], (uint32_t)b[i]);
    return (int32_t)acc;
}
