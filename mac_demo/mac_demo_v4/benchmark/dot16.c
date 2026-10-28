#include <stddef.h>
#include <stdint.h>

int32_t dot16(const int16_t *a, const int16_t *b, size_t n)
{
    int32_t acc = 0;
    for (size_t i = 0; i < n; i++)
        acc += (int32_t)a[i] * (int32_t)b[i];
    return acc;
}
