#!/usr/bin/env python3
# app_with_decoder.py —— 集成 Flask UI + 实时接收 + 日志记录（自动路径修复版）

import threading, socket, struct, ctypes, os, time, csv, sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.stats import chi2
from flask import Flask, render_template, jsonify
import pandas as pd

# ===== 自动寻找路径 =====
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "model"
LIB_PATH = BASE_DIR.parent / "libprng" / "libprng.so"

# ===== PRNG 载入 =====
PRNG = ctypes.CDLL(str(LIB_PATH))
PRNG.gen_diag.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_uint64]

def prng_get(N, seed):
    buf = (ctypes.c_double * N)()
    PRNG.gen_diag(buf, N, seed)
    return np.frombuffer(buf, dtype=np.float64)

# ===== 模型载入 =====
H = np.load(MODEL_DIR / "H.npy")
Sigma_inv = np.load(MODEL_DIR / "Sigma_inv.npy")
H_pinv = np.load(MODEL_DIR / "H_pinv.npy")
m, N = H.shape
df = m - N
THRESH = chi2.ppf(0.99, df)
SEED = 42
LOG_PATH = BASE_DIR / "monitor_log.csv"

if not LOG_PATH.exists():
    with open(LOG_PATH, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "J", "threshold", "result"])

def log_result(jval, result):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", newline="") as f:
        csv.writer(f).writerow([timestamp, f"{jval:.4f}", f"{THRESH:.4f}", result])

def decoder_loop():
    print("🛰 decoder thread started on port 12345")
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 12345))
    srv.listen(1)
    while True:
        conn, addr = srv.accept()
        print("📡 connection from", addr)
        try:
            raw = conn.recv(4)
            if len(raw) < 4: continue
            m_recv = struct.unpack("<I", raw)[0]
            if m_recv != m: continue
            data = b''
            while len(data) < 8*m*2:
                chunk = conn.recv(8*m*2 - len(data))
                if not chunk: break
                data += chunk
            if len(data) != 8*m*2: continue
            d = np.frombuffer(data[:8*m], dtype=np.float64)
            z_c = np.frombuffer(data[8*m:], dtype=np.float64)
            d_full = np.ones(m); d_core = prng_get(N, SEED); d_full[:N] = d_core
            z = z_c / d_full
            x_hat = H_pinv @ z
            r = z - H @ x_hat
            J = r.T @ Sigma_inv @ r
            result = "ATTACK" if J > THRESH else "NORMAL"
            print(f"J = {J:.4f}  ({result})")
            log_result(J, result)
        except Exception as e:
            print("Decoder error:", e)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/logs")
def api_logs():
    if not LOG_PATH.exists(): return jsonify([])
    df = pd.read_csv(LOG_PATH)
    return jsonify(df.tail(20).to_dict(orient="records"))

if __name__ == "__main__":
    t = threading.Thread(target=decoder_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)
