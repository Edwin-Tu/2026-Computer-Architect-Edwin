/* Host timing experiment: time the reference dot product on this machine.
 * Not a RISC-V or custom-instruction measurement.
 *
 * Build: cc -std=c11 -O1 -Wall -Wextra -Werror -o host_timing host_timing.c ../mac.c -I..
 * Run:   ./host_timing [N] [reps_per_trial] [trials]
 */
#include "mac.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static volatile int32_t sink;

static double now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1e9 + (double)ts.tv_nsec;
}

static int cmp_double(const void *x, const void *y)
{
    double a = *(const double *)x, b = *(const double *)y;
    return (a > b) - (a < b);
}

int main(int argc, char **argv)
{
    size_t n = argc > 1 ? (size_t)strtoul(argv[1], NULL, 10) : 1024;
    int reps = argc > 2 ? atoi(argv[2]) : 2000;
    int trials = argc > 3 ? atoi(argv[3]) : 15;

    int32_t *a = malloc(n * sizeof *a), *b = malloc(n * sizeof *b);
    if (!a || !b)
        return 1;
    uint32_t seed = 2026;
    for (size_t i = 0; i < n; i++) {
        seed = seed * 1664525u + 1013904223u;
        a[i] = (int32_t)seed;
        seed = seed * 1664525u + 1013904223u;
        b[i] = (int32_t)seed;
    }

    if (dot_ref(a, b, n) != dot_mac(a, b, n)) {
        printf("self-check FAIL: dot_ref != dot_mac\n");
        return 1;
    }

    for (int i = 0; i < reps / 10; i++)
        sink = dot_ref(a, b, n);

    double *per_call = malloc((size_t)trials * sizeof *per_call);
    for (int t = 0; t < trials; t++) {
        double start = now_ns();
        for (int r = 0; r < reps; r++)
            sink = dot_ref(a, b, n);
        per_call[t] = (now_ns() - start) / reps;
    }
    qsort(per_call, (size_t)trials, sizeof *per_call, cmp_double);

    double median = per_call[trials / 2];
    printf("N=%zu reps=%d trials=%d\n", n, reps, trials);
    printf("min_ns_per_call=%.1f\n", per_call[0]);
    printf("median_ns_per_call=%.1f\n", median);
    printf("max_ns_per_call=%.1f\n", per_call[trials - 1]);
    printf("median_ns_per_element=%.3f\n", median / (double)n);
    printf("spread_pct=%.1f\n", (per_call[trials - 1] - per_call[0]) / median * 100.0);

    free(per_call);
    free(a);
    free(b);
    return 0;
}
