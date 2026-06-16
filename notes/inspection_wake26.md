# Inspection - Wake 26

## 阶段

第 26 次唤醒：检验阶段。

本轮不改交付物，重点从两个视角审查第 25 轮新增的 `docs/fpga_architecture.md` 是否足够支撑下一步进入 `rtl/xor_engine/`：

1. **第一次准备写 RTL 的读者**：能不能知道下一步写什么、为什么先写它、不要写什么；
2. **仿真测试工程师**：能不能据此设计 test vector、testbench 和可重复运行的仿真命令。

## 检验范围

- `docs/fpga_architecture.md`
- `README.md`
- `TODO.md`
- `rtl/`
- `sim/`
- 本机 RTL 仿真工具可用性
- Python baseline 测试

## 实测记录

### 1. Python baseline 仍然通过

执行：

```bash
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.05s
```

结论：第 25 轮文档接入没有破坏已有 Python 模型。

### 2. 本机 RTL 工具边界

探测结果：

```text
iverilog: found, Icarus Verilog version 0.9.7
vvp: found, Icarus Verilog runtime version 0.9.7
verilator: NOT_FOUND
yosys: NOT_FOUND
```

结论：下一轮若要做最小 RTL 闭环，最现实的选择是 **Verilog + Icarus Verilog**，不要一开始依赖 SystemVerilog、Verilator 或综合工具。

### 3. RTL / sim 目录现状

探测结果：

```text
rtl/xor_engine exists, file_count = 0
rtl/lba_mapper exists, file_count = 0
rtl/stripe_manager exists, file_count = 0
sim/golden_model exists, file_count = 0
sim/testbenches exists, file_count = 0
```

结论：目录已经存在，但没有 README、RTL、testbench 或 vector。读者从 README 走到 `rtl/xor_engine/` 仍会遇到空房间。

### 4. README 接入情况

检查结果：

```text
README contains docs/fpga_architecture.md: True
README contains “FPGA 架构边界”: True
README contains literal rtl/xor_engine: False
```

结论：README 已经把读者带到 FPGA 架构页，但还没有直接暴露 `rtl/xor_engine` 路径。这不是当前 P0，因为架构页已有下一步说明；但等 `rtl/xor_engine/` 有内容后，README 应该增加直接入口。

## 及格线判断

### 已达标

1. **方向正确**：`docs/fpga_architecture.md` 明确拒绝一上来做完整 RAID 控制器，符合“每轮小闭环”的目标。
2. **技术边界清楚**：明确暂不做 SATA / NVMe / PCIe / DMA / 驱动 / 掉电恢复，避免把真实接口问题提前混入算法实验。
3. **Python 到 RTL 的映射关系建立了**：`xor_blocks()`、`RAID0.map_lba()`、`RAID5.map_lba()`、`write_full_stripe()` 都能找到未来 RTL 对应物。
4. **下一步优先级合理**：先做 `xor_engine`，再做 `lba_mapper`，再做 `stripe_manager`，符合从简单可验证逻辑到控制逻辑的路径。
5. **已有 Python 测试仍通过**：没有破坏现有可运行基础。

### 未达出色

1. **`xor_engine` 的最小接口仍不够可执行**  
   架构页说“输入 N 个 word，输出 XOR 结果”，但没有定：
   - 参数名；
   - word 宽度；
   - 输入展平方式；
   - 是否纯组合；
   - 是否有 clk/rst；
   - 如何处理 N=1、N=2、N=4。

2. **握手策略仍摇摆**  
   文档同时提到 `valid/ready` 或 `start/done`，但对第一关来说这会增加选择成本。作为第一个 RTL 小实验，建议先做 **纯组合 XOR**，不引入握手；后续再加 `xor_engine_pipe` 或 `xor_engine_stream`。

3. **test vector 文件格式未定**  
   架构页建议 `sim/vectors/xor_engine_cases.txt`，但没有规定格式。测试工程师还不知道每行应该是：
   - hex 输入 + hex 期望输出；
   - JSON；
   - CSV；
   - 还是 Verilog `$readmemh` 格式。

4. **仿真入口缺失**  
   本机有 Icarus Verilog，但仓库没有 `sim/README.md` 或 `rtl/xor_engine/README.md` 写明：

   ```bash
   iverilog ...
   vvp ...
   ```

   对“闯关式实验室”来说，下一关必须能复制命令直接跑。

5. **空目录造成心理落差**  
   `rtl/xor_engine/` 已存在但为空。读者会以为这里应该有东西，却没有引导。下一轮应优先填这个目录，而不是继续扩文档。

6. **TODO 有轻微重复**  
   `rtl/xor_engine` 同时出现在 Next 和 Later。当前还能接受，因为 Next 是“创建第一块可对拍实验”，Later 是 RTL 模块清单；但下一轮实现后应把 Later 条目拆成：组合版、流水线版、对拍版，避免重复感。

## 更苛刻视角：第一次写 RTL 的读者会卡在哪里？

读者当前能理解：

```text
Python xor_blocks() -> rtl/xor_engine -> testbench 对拍
```

但读者还不能立刻动手，因为缺少“第一关任务卡”：

```text
文件要放哪里？
模块名叫什么？
端口怎么定义？
测试向量怎么生成？
命令怎么跑？
期望输出是什么？
失败时怎么看？
```

这说明第 25 轮架构桥是必要且有效的，但还只是桥面，没有铺第一块可踩的砖。

## 建议的下一轮改进闭环

第 27 次唤醒应进入改进阶段，建议只做一个小闭环：**创建并跑通 `rtl/xor_engine` 最小组合 XOR 实验**。

建议范围：

```text
rtl/xor_engine/README.md
rtl/xor_engine/xor_engine.v
rtl/xor_engine/tb_xor_engine.v
rtl/xor_engine/gen_vectors.py
rtl/xor_engine/vectors.txt
```

建议技术选择：

1. 使用 Verilog-2001，不用 SystemVerilog；
2. 使用 Icarus Verilog + vvp，因为本机已存在；
3. 第一版使用纯组合逻辑，不加 clk/rst/valid/ready；
4. 参数建议：

```verilog
parameter WORD_WIDTH = 32;
parameter INPUT_COUNT = 4;
input  [WORD_WIDTH*INPUT_COUNT-1:0] data_in;
output [WORD_WIDTH-1:0] xor_out;
```

5. vector 格式建议先用简单文本，便于 Python 和 Verilog 都读：

```text
# input0 input1 input2 input3 expected
00000000 11111111 22222222 33333333 00000000
```

6. testbench 使用 `$fscanf` 读取每行 hex，比较 RTL 输出和 expected。

## 下轮验收标准

下一轮改进完成后，至少应能执行：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
```

期望输出应包含类似：

```text
PASS xor_engine cases=<N>
```

并且 Python baseline 仍然通过：

```bash
python -m pytest -q labs/level0_python_model
```

## 优先级结论

- P0：补 `rtl/xor_engine` 最小可运行实验，而不是继续扩写架构文档；
- P1：明确本仓库当前 RTL 选择为 Verilog-2001 + Icarus Verilog；
- P1：定义 vector 格式，保证 Python golden model 和 Verilog testbench 可共用；
- P2：实现后更新 README 直接入口；
- P2：TODO 中消除 `rtl/xor_engine` 重复表达。
