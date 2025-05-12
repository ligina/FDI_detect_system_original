#ifndef PRNG_H
#define PRNG_H
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Generate a length-N diagonal vector using a linear congruential generator.
 * dst  : pointer to double array of length N
 * N    : length
 * seed : same seed must be used on encoder & decoder
 * Each element is in (0,2] and not equal to 1.
 */
void gen_diag(double *dst, int N, uint64_t seed);

#ifdef __cplusplus
}
#endif
#endif
