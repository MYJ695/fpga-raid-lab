# Inspection - Wake 28

## 阶段

第 28 次唤醒：检验阶段。

本轮以 **RTL 测试工程师 + 第一次跑 RTL 的读者** 两个视角，检查第 27 次唤醒新增的 `rtl/xor_engine/` 小实验。重点不是继续加功能，而是确认它是否真的适合作为“从 Python golden model 走到 RTL”的第一块砖。

## 本轮检验了什么

1. 文档入口是否能让读者从 README 跑到 `xor_engine`；
2. `xor_engine.v` 的参数化组合 XOR 是否只是“看起来参数化”，还是能通过更多宽度/输入数测试；
3. `tb_xor_engine.v` 对空文件、短行、注释行、空行等坏 vector 的行为；
4. `gen_vectors.py` 生成的 vector 是否和当前 testbench 假设一致；
5. TODO / 架构文档 / README 之间的路线是否一致。

## 实测结果

### 1. 文档命令仍然可跑

在仓库根目录重新执行：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o notes/_inspection_wake28_tmp/tb_doc.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp notes/_inspection_wake28_tmp/tb_doc.vvp
python -m pytest -q labs/level0_python_model
```

结果：

```text
wrote .../rtl/xor_engine/vectors.txt cases=5
PASS xor_engine cases=5
12 passed in 0.05s
```

结论：第 27 轮的主路径是可运行的，README/`rtl/xor_engine/README.md` 给出的核心命令没有失效。

### 2. 参数化 RTL 本体通过了额外探针

临时生成额外 testbench，覆盖了非默认参数：

| WORD_WIDTH | INPUT_COUNT | 结果 |
|---:|---:|---|
| 8 | 2 | `PASS_PARAM ww=8 ic=2 cases=2` |
| 16 | 3 | `PASS_PARAM ww=16 ic=3 cases=1` |
| 64 | 5 | `PASS_PARAM ww=64 ic=5 cases=1` |

结论：`xor_engine.v` 的核心写法 `data_in[i*WORD_WIDTH +: WORD_WIDTH]` 在本机 Icarus Verilog 下对 2/3/5 输入和 8/16/64 位都能工作。它不是只为默认 4x32 硬编码的假参数化。

但注意：这些探针是本轮临时检验，没有沉淀为仓库里的回归测试。当前仓库自带 testbench 仍只覆盖 4 输入、32-bit。

### 3. 坏 vector 行为不够像“教学级测试台”

用临时替换路径的方式测试 `tb_xor_engine.v`：

| 输入文件形态 | 当前行为 | 评价 |
|---|---|---|
| 空文件 | `FAIL xor_engine: no vector cases loaded` | 可以接受 |
| 少一列的短行 | `FAIL xor_engine: no vector cases loaded` | 能失败，但错误信息不准确；读者不知道是“列数不对” |
| 注释表头 | `vvp` 超时/卡住 | 已知旧 Icarus + `$fscanf` 风险仍存在；靠 vector 无注释规避，不够健壮 |
| 末尾空行 | `PASS xor_engine cases=1` | 可接受，但没有显式说明会忽略空行 |

结论：当前 testbench 对“正确 vector”足够，但对“坏输入”的失败解释不够好。作为学习项目，下一步应该让错误消息更像老师：告诉读者第几行、读到了几列、应该是什么格式，而不是沉默、误报或卡住。

## 及格线判断

通过。

理由：

- 主路径能跑通；
- RTL 组合逻辑简洁，和 `docs/fpga_architecture.md` 的第一阶段边界一致；
- README / TODO / 架构页都把 `xor_engine` 放在 `lba_mapper` 前，路线一致；
- 参数化本体经临时更难测例验证，没有暴露明显逻辑错误。

## 不够出色的地方

### P0：缺少仓库内的参数矩阵回归

第 27 轮说 `WORD_WIDTH` 和 `INPUT_COUNT` 参数化，但仓库自带验证只测默认 `32 x 4`。本轮临时证明了 RTL 有潜力，但读者或 CI 不能一键复现这些参数探针。

建议下一轮改进：新增一个轻量脚本，例如：

```text
rtl/xor_engine/run_xor_engine_tests.py
```

它负责：

1. 生成默认 vector；
2. 编译运行默认 testbench；
3. 自动生成 8x2、16x3、64x5 等参数化临时 testbench；
4. 最后再跑 Python baseline。

这样比马上写 Makefile 更适合本仓库当前的 Python-first 学习风格。

### P1：testbench 对坏 vector 的失败信息太弱

当前 `$fscanf` 直接跑在 `while (!$feof(fd))` 里，遇到注释行可能卡住；短行最终只表现为“没有加载任何 case”。这对第一次接触 Verilog testbench 的读者不友好。

建议下一轮改进：

- testbench 继续要求纯 hex 文件，不支持注释行；
- 但应在 README 里明确“不要加注释/表头”；
- 更推荐把坏输入检查放在 Python 生成/验证脚本里，避免旧 Icarus 的 `$fscanf` 陷阱；
- 如果仍在 Verilog 侧做检查，至少加最大循环保护或逐行 `$fgets` 后再 `$sscanf`。

### P1：vector 生成器和 Python golden model 的连接还偏弱

`gen_vectors.py` 自己实现了 `xor_words()`，没有直接复用 `labs/level0_python_model` 里的 `xor_blocks()`。这不是错误，因为 RTL word-level XOR 和 Python block-level XOR 的粒度不同；但文档上说“对拍 Python golden model”，现在更像“用 Python 写了一个局部 golden 函数”。

建议下一轮不要强行 import 旧模型，而是在 README 里讲清楚：

```text
Python 模型里的 xor_blocks 是 byte/block 视角；
RTL xor_engine 是固定 word 视角；
两者验证的是同一个 XOR 性质，但接口粒度不同。
```

### P2：缺少统一仿真入口，但现在还不必上 Makefile

`sim/` 目录在 README 结构中存在，但当前 RTL 命令散落在 README 和 `rtl/xor_engine/README.md`。如果马上做 Makefile，可能会把学习者拖进工具链细节。

更合适的小步是：先给 `xor_engine` 一个 Python runner。等 `lba_mapper` 也出现后，再把公共逻辑上移到 `sim/`。

## 下轮建议做什么

第 29 次唤醒应进入改进阶段，建议只做一个闭环：

> 给 `rtl/xor_engine` 增加一键回归脚本，沉淀本轮临时发现的参数矩阵测试，并改善坏 vector/使用说明。

推荐范围：

1. 新增 `rtl/xor_engine/run_tests.py`；
2. 保留现有 Verilog RTL，不重写；
3. `run_tests.py` 至少覆盖默认 `32x4`、`8x2`、`16x3`、`64x5`；
4. README 增加“一键跑”和“vector 不支持注释/表头”的说明；
5. 最后跑：

```bash
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```

这样下一块 `lba_mapper` 开工前，RTL 实验会更像一个可持续扩展的实验室，而不是只跑一次的演示。
