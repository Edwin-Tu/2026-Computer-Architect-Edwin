#include "min.h"

#include <inttypes.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

typedef struct {
    const char *name;
    int32_t rs1;
    int32_t rs2;
    int32_t expected;
} min_test_case;

int main(void)
{
    static const min_test_case cases[] = {
        {"teacher example: mixed signs", 3, -2, -2},
        {"teacher example: equal positive", 5, 5, 5},
        {"ascending positive", 10, 20, 10},
        {"descending positive", 20, 10, 10},
        {"two negative values", -10, -20, -20},
        {"both zero", 0, 0, 0},
        {"zero and negative", 0, -1, -1},
        {"zero and positive", 0, 100, 0},
        {"symmetric signs", -100, 100, -100},
        {"full signed range", INT32_MAX, INT32_MIN, INT32_MIN},
        {"minimum and zero", INT32_MIN, 0, INT32_MIN},
        {"maximum and zero", INT32_MAX, 0, 0},
        {"equal minimum", INT32_MIN, INT32_MIN, INT32_MIN},
        {"equal maximum", INT32_MAX, INT32_MAX, INT32_MAX},
    };

    size_t failures = 0;
    const size_t case_count = sizeof(cases) / sizeof(cases[0]);

    for (size_t i = 0; i < case_count; ++i) {
        const int32_t actual = min_s32(cases[i].rs1, cases[i].rs2);
        const int passed = (actual == cases[i].expected);

        printf("[%s] %2zu %-31s min(%" PRId32 ", %" PRId32
               ") = %" PRId32 ", expected %" PRId32 "\n",
               passed ? "PASS" : "FAIL", i + 1, cases[i].name,
               cases[i].rs1, cases[i].rs2, actual, cases[i].expected);

        if (!passed) {
            ++failures;
        }
    }

    printf("\nResult: %zu/%zu tests passed.\n", case_count - failures,
           case_count);
    return failures == 0 ? 0 : 1;
}
