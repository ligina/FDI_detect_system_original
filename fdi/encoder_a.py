#!/usr/bin/env python3
"""
encoder_a.py  -- run on the sending board (Encoder)

Usage:
    python3 encoder_a.py --ip 192.168.x.x --port 12345 --seed 42 --attack 0 or attack 1 (when 0,noraml data; when 1, attack)

- Generates synthetic measurements z = H x  (replace with real sensor later)
- Encodes z_c = diag * z  (diag from shared PRNG and seed)
- Sends a binary packet: [uint32 m | double[m] diag | double[m] z_c]
- Optional: injects an FDI attack a = H Δx before encoding to test detection
"""

import argparse, ctypes, os, socket, struct, sys, time
import numpy as np
from pathlib import Path

# Load shared library
LIB = str(Path(__file__).resolve().parent / "libprng" / "libprng.so")
PRNG = ctypes.CDLL(LIB)
PRNG.gen_diag.argtypes = [ctypes.POINTER(ctypes.c_double),
                          ctypes.c_int, ctypes.c_uint64]

def prng_get(N, seed):
    buf = (ctypes.c_double * N)()
    PRNG.gen_diag(buf, N, seed)
    return np.frombuffer(buf, dtype=np.float64)

def load_model():
    # load H, x, Sigma saved as .npy for 14‑bus demo
    H = np.load("model/H.npy")         # shape (m, N)
    x = np.load("model/x.npy")         # shape (N,)
    z = H @ x                          # shape (m,)
    return H, z

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", required=True)
    ap.add_argument("--port", type=int, default=12345)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--attack", type=int, default=0,
                    help="1 to inject FDI for test")
    args = ap.parse_args()

    H, z = load_model()
    m, N = H.shape

    # Generate diag vector of length m
    d_core = prng_get(N, args.seed)    # 对 N 个状态相关测量加水印
    d = np.ones(m, dtype=np.float64)   # 其余保留为 1
    d[:N] = d_core                     # 假设 essential measurements 在前 N 行

    z_enc = d * z.copy()

    # Optional: inject stealthy FDI attack
    if args.attack:
        k = 3
        idx = np.random.choice(N, k, replace=False)
        delta = np.zeros(N)
        delta[idx] = 0.01 * np.random.randn(k)
        a = H @ delta
        z_enc += a
        print("Injected FDI on states", idx)

    # 打包数据: [uint32 m] + diag[m] + z_enc[m]
    pkt = struct.pack("<I", m) + d.tobytes() + z_enc.tobytes()

    sock = socket.create_connection((args.ip, args.port))
    sock.sendall(pkt)
    print("Sent packet with {} bytes to {}:{}".format(len(pkt), args.ip, args.port))

if __name__ == "__main__":
    main()
