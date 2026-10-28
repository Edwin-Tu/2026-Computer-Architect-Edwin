#include "mac.h"

#include <stdint.h>
#include <stdio.h>

static int failures;

#define EXPECT_EQ_U32(actual, expected)                                              \
    do {                                                                             \
        uint32_t a_ = (uint32_t)(actual), e_ = (uint32_t)(expected);                 \
        if (a_ != e_) {                                                              \
            printf("FAIL %s:%d: %s = 0x%08x, expected 0x%08x\n", __FILE__, __LINE__, \
                   #actual, a_, e_);                                                 \
            failures++;                                                              \
        }                                                                            \
    } while (0)

#define EXPECT_EQ_I32(actual, expected) EXPECT_EQ_U32((int32_t)(actual), (int32_t)(expected))

static void test_mac_insn_basic(void)
{
    EXPECT_EQ_U32(mac_insn(10, 3, 4), 22);
    EXPECT_EQ_U32(mac_insn(0, 0, 0), 0);
    EXPECT_EQ_U32(mac_insn(5, 0, 123), 5);
}

static void test_mac_insn_negative_operands(void)
{
    EXPECT_EQ_I32(mac_insn(0, (uint32_t)-3, 4), -12);
    EXPECT_EQ_I32(mac_insn((uint32_t)-5, (uint32_t)-3, (uint32_t)-4), 7);
}

static void test_mac_insn_wraparound(void)
{
    EXPECT_EQ_U32(mac_insn(0x7FFFFFFFu, 1, 1), 0x80000000u);
    EXPECT_EQ_U32(mac_insn(0, 0x40000000u, 4), 0);
}

static void test_dot_empty(void)
{
    int32_t a[1] = {7}, b[1] = {9};
    EXPECT_EQ_I32(dot_ref(a, b, 0), 0);
    EXPECT_EQ_I32(dot_mac(a, b, 0), 0);
}

static void test_dot_known_values(void)
{
    int32_t a[] = {1, 2, 3, 4}, b[] = {5, 6, 7, 8};
    EXPECT_EQ_I32(dot_ref(a, b, 4), 70);
    EXPECT_EQ_I32(dot_mac(a, b, 4), 70);

    int32_t c[] = {-3, 4, -5}, d[] = {7, -8, 9};
    EXPECT_EQ_I32(dot_ref(c, d, 3), -98);
    EXPECT_EQ_I32(dot_mac(c, d, 3), -98);
}

static void test_dot_overflow_matches_reference(void)
{
    int32_t a[] = {0x7FFFFFFF, 0x7FFFFFFF}, b[] = {0x7FFFFFFF, 2};
    EXPECT_EQ_I32(dot_ref(a, b, 2), -1);
    EXPECT_EQ_I32(dot_mac(a, b, 2), -1);
}

static void test_dot_random_matches_reference(void)
{
    uint32_t seed = 12345;
    for (int trial = 0; trial < 200; trial++) {
        int32_t a[64], b[64];
        size_t n = (size_t)(trial % 64);
        for (size_t i = 0; i < n; i++) {
            seed = seed * 1664525u + 1013904223u;
            a[i] = (int32_t)seed;
            seed = seed * 1664525u + 1013904223u;
            b[i] = (int32_t)seed;
        }
        EXPECT_EQ_I32(dot_mac(a, b, n), dot_ref(a, b, n));
    }
}

int main(void)
{
    test_mac_insn_basic();
    test_mac_insn_negative_operands();
    test_mac_insn_wraparound();
    test_dot_empty();
    test_dot_known_values();
    test_dot_overflow_matches_reference();
    test_dot_random_matches_reference();

    if (failures) {
        printf("%d C test(s) failed\n", failures);
        return 1;
    }
    printf("all C tests passed\n");
    return 0;
}
