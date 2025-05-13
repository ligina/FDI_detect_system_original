# FDI 检测系统仓库说明

## 一、项目概述
本仓库实现了一个虚假数据注入（False Data Injection, FDI）检测系统，包含编码器、解码器以及一个用于展示检测结果的 Web 界面。编码器生成合成测量值并进行编码，解码器接收编码数据进行解码和 FDI 检测，Web 界面实时展示检测日志和 J 值变化趋势。算法基于论文呢"Optimal Coding Schemes for Detecting False Data Injection Attacks in Power System State Estimation "中的检测算法，并使用线性同余伪随机进行测量编码。

## 二、仓库结构
```plaintext
FDI_detect_system_original/
├── encoder_a.py
├── monitor_log.csv
├── libprng/
│   ├── Makefile
│   ├── libprng.so
│   ├── prng.c
│   ├── prng.h
│   └── prng.o
├── fdi_flask/
│   ├── app_with_decoder.py
│   ├── monitor_log.csv
│   └── templates/
│       └── index.html
└── model/
    ├── H.npy
    ├── H_pinv.npy
    ├── Sigma_inv.npy
    └── x.npy
```

### 各部分说明
- **`encoder_a.py`**：运行在发送端（编码器），生成合成测量值 `z`，对其进行编码得到 `z_c`，并将编码后的数据打包发送给解码器。支持可选的 FDI 攻击注入，用于测试检测系统。
- **`libprng/`**：包含一个伪随机数生成器（PRNG）的实现，用于生成加密所需的对角矩阵。通过共享的种子，编码器和解码器可以生成相同的对角矩阵，从而实现数据的加密和解密。
- **`fdi_flask/`**：
  - **`app_with_decoder.py`**：集成了 Flask Web 界面和实时接收功能，用于接收编码器发送的数据，进行解码和 FDI 检测，并将检测结果记录到日志文件中。同时提供 API 接口，用于前端获取最新的检测日志。
  - **`templates/index.html`**：FDI 检测系统的 Web 界面，使用 Bootstrap 和 Chart.js 库，展示实时检测日志和 J 值变化趋势图。
- **`model/`**：存储模型相关的数据文件，包括 `H.npy`、`H_pinv.npy`、`Sigma_inv.npy` 和 `x.npy`，这些文件包含了系统的状态矩阵、伪逆矩阵、协方差逆矩阵和状态向量等信息。

## 三、环境准备

### 依赖安装
本项目使用 Python 3 编写，需要安装以下依赖库：
```bash
pip install numpy scipy flask pandas
```

### 编译 PRNG 库
在 `libprng/` 目录下，执行以下命令编译生成共享库 `libprng.so`：
```bash
make
```

## 四、使用方法

### 1. 启动解码器
在 `fdi_flask/` 目录下，运行以下命令启动解码器和 Flask Web 服务器：
```bash
python3 app_with_decoder.py
```
解码器将监听端口 12345，接收编码器发送的数据。Flask 服务器将在 `http://0.0.0.0:5000` 上提供 Web 界面。

### 2. 启动编码器
在项目根目录下，运行以下命令启动编码器：
```bash
python3 encoder_a.py --ip <解码器 IP 地址> --port 12345 --seed 42 --attack 0
```
- `--ip`：解码器的 IP 地址，必填项。
- `--port`：解码器监听的端口号，默认为 12345。
- `--seed`：PRNG 的种子，默认为 1。
- `--attack`：是否注入 FDI 攻击进行测试，0 表示正常数据，1 表示注入攻击，默认为 0。

### 3. 访问 Web 界面
打开浏览器，访问 `http://<服务器 IP 地址>:5000`，即可查看实时检测日志和 J 值变化趋势图。

## 五、代码说明

### `encoder_a.py`
- **`prng_get(N, seed)`**：调用 PRNG 库生成长度为 `N` 的对角向量。
- **`load_model()`**：加载模型相关的数据文件，生成合成测量值 `z`。
- **`main()`**：解析命令行参数，生成对角向量 `d`，对测量值 `z` 进行编码得到 `z_enc`，可选地注入 FDI 攻击，将编码后的数据打包发送给解码器。

### `fdi_flask/app_with_decoder.py`
- **`prng_get(N, seed)`**：调用 PRNG 库生成长度为 `N` 的对角向量。
- **`log_result(jval, result)`**：将检测结果记录到日志文件中。
- **`decoder_loop()`**：监听端口 12345，接收编码器发送的数据，进行解码和 FDI 检测，计算检测统计量 `J`，并与阈值比较，判断是否存在 FDI 攻击。
- **`index()`**：返回 Web 界面的 HTML 文件。
- **`api_logs()`**：提供 API 接口，返回最新的 20 条检测日志。

### `fdi_flask/templates/index.html`
使用 JavaScript 定时调用 `/api/logs` 接口获取最新日志数据，并更新表格和图表。

### `libprng/prng.c`
- **`normalize(uint64_t x)`**：将随机数 `x` 归一化到 (0, 2] 区间，且不包含 1。
- **`gen_diag(double *dst, int N, uint64_t seed)`**：使用线性同余生成器生成长度为 `N` 的对角向量。

## 六、注意事项
- 编码器和解码器必须使用相同的种子，以确保生成相同的对角矩阵。
- 项目中的模型数据文件（`model/*.npy`）是为 14 - 总线示例保存的，实际使用时可根据需要替换。
- 日志文件 `monitor_log.csv` 记录了每次检测的时间、J 值、阈值和检测结果。

## 七、鸣谢
- 特别感谢刘臣胜教授、朱远明教授对本研究的大力支持 ！
