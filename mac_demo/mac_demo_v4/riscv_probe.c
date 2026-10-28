#include <stdint.h>

#include "mac.h"

uint32_t mac_probe(uint32_t acc, uint32_t a, uint32_t b)
{
    return mac_insn(acc, a, b);
}
