# xor_engine - 第一块可对拍的 RTL 小模块

## 核心结论

`xor_engine` 是从 Python golden model 走向 RTL 的第一块砖。

它只做一件事：

```text
多个等宽数据字 -> XOR -> 一个 parity 字
```

对应 Python 模型里的：

```python
xor_blocks([block0, block1, block2, ...])
```

不过两者的接口粒度不同：Python baseline 是 byte/block 视角，`xor_engine` 是固定宽度 word 视角。它们验证的是同一个 XOR 性质，而不是复用同一个函数签名。

第一版故意保持简单：**纯组合逻辑**，没有 `clk`、`rst`、`valid/ready`，也不接真实磁盘接口。

## 接口

```verilog
module xor_engine #(
    parameter WORD_WIDTH = 32,
    parameter INPUT_COUNT = 4
)(
    input  [WORD_WIDTH*INPUT_COUNT-1:0] data_in,
    output [WORD_WIDTH-1:0]             xor_out
);
```

打包规则：

```text
data_in[31:0]    = input0
data_in[63:32]   = input1
data_in[95:64]   = input2
data_in[127:96]  = input3
```

也就是说，越靠低位，越像 vector 文件里越靠左的第一个输入。

## 文件

```text
rtl/xor_engine/
├── README.md          # 本说明
├── xor_engine.v       # 参数化组合 XOR RTL
├── tb_xor_engine.v    # Icarus Verilog testbench，固定验证 4 输入 32-bit
├── gen_vectors.py     # Python golden vector 生成器
├── run_tests.py       # 一键回归：默认 testbench + 参数矩阵
└── vectors.txt        # 生成出的 4 输入 32-bit 测试向量
```

## Vector 格式

`vectors.txt` 每行是 4 个输入和 1 个期望输出，均为 8 位十六进制。

为了兼容较老的 Icarus Verilog，本文件**不写表头、不写注释行**，只保留机器可读数据：

```text
00000000 11111111 22222222 33333333 00000000
```

期望值由 Python 计算：

```text
expected = input0 ^ input1 ^ input2 ^ input3
```

## 怎么跑

推荐先跑一键回归：

```bash
python rtl/xor_engine/run_tests.py
```

它会做三件事：

1. 重新生成默认 `4 x 32-bit` vector；
2. 编译并运行仓库里的 `tb_xor_engine.v`；
3. 临时生成参数化 testbench，额外覆盖 `8x2`、`16x3`、`64x5`。

期望最后看到：

```text
PASS xor_engine regression: default + parameter matrix
```

如果想手动拆开看 Icarus Verilog 命令，也可以在仓库根目录执行：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
```

期望输出：

```text
PASS xor_engine cases=<N>
```

注意：这条手动命令会留下 `rtl/xor_engine/tb_xor_engine.vvp`。它只是 Icarus Verilog 编译产物，可以删除，也已被 `.gitignore` 忽略。若想保持目录清爽，优先使用上面的一键回归命令。

建议同时确认 Python baseline 没坏：

```bash
python -m pytest -q labs/level0_python_model
```

## 为什么先做纯组合

因为第一关要验证的是 RAID5 parity 的核心事实：

```text
A ^ B ^ C = P
A ^ B ^ P = C
```

握手、流水线、吞吐量、时序约束都很重要，但它们会把第一关变复杂。等这个组合模块能和 Python 对拍后，再升级流水线版本。
