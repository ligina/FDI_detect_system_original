#include "prng.h"
#include <math.h>

#define MOD 281474976710656ULL   // 2^48
#define A   25214903917ULL
#define C   11ULL

static double normalize(uint64_t x)
{
    double v = (double)(x % MOD) / (double)MOD;   //基于论文中的算法，不能取1
    /* Map (0,1) -> (0,2] but skip 1.0 exactly */
    double y = 0.5 + v*1.5;      // (0.5,2.0)
    if (fabs(y-1.0) < 1e-12) y += 1e-6;
    return y;
}

void gen_diag(double *dst, int N, uint64_t seed)
{
    uint64_t state = seed ? seed : 1ULL;
    for(int i=0;i<N;++i){
        state = (A*state + C) % MOD;
        dst[i] = normalize(state);
    }
}
