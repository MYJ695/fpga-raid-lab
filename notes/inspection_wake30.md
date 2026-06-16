# Inspection - Wake 30

## 阶段

第 30 次唤醒：检验阶段。

本轮换成 **新读者 + RTL 回归维护者** 视角，检验第 29 轮新增的 `rtl/xor_engine/run_tests.py` 是否已经足够承担“第一块 RTL 小模块的一键回归入口”。重点不是再证明 XOR 正确，而是检查它作为后续 `lba_mapper`、`stripe_manager` 的范式是否清晰、可发现、可维护。

## 检验范围

读取并检查：

- `README.md`
- `TODO.md`
- `notes/changelog_wake29.md`
- `rtl/xor_engine/README.md`
- `rtl/xor_engine/run_tests.py`
- `rtl/xor_engine/xor_engine.v`
- `rtl/xor_engine/tb_xor_engine.v`

实际执行/模拟：

```bash
python rtl/xor_engine/run_tests.py
```

并额外模拟：

- `PATH` 中找不到 `iverilog` / `vvp`；
- 编译时传入不存在的 RTL 文件；
- 临时把 `xor_engine` 输出改坏，观察 testbench 的失败信息；
- 查看 `sim/` 目录是否已经有能承接 RTL 回归的统一入口。

## 结论

第 29 轮改进达到了“单模块可一键回归”的及格线：真实环境下 `run_tests.py` 能跑通默认 testbench 和参数矩阵，参数覆盖也比第 27 轮更可信。

但从“闯关式实验室”和“后续 RTL 模块可持续扩展”的标准看，还不够出色。主要短板是：**入口可发现性不足、工具缺失错误不友好、回归结构仍停留在单模块脚本，没有形成下一关可复用的仿真路线。**

## 发现的问题

### P0 - 根 README 仍然没有把新读者带到 RTL 一键回归

根 `README.md` 的项目结构里提到了：

```text
rtl/                  # RTL 小模块
sim/                  # 仿真和 golden model
```

但没有出现：

```bash
python rtl/xor_engine/run_tests.py
```

这会导致第一次进入仓库的读者按根 README 只能知道“有 RTL 小模块”，却不知道现在已经有一个可跑的 RTL 回归入口。对闯关式项目来说，根 README 应该有一条最短路线：

```text
先跑 Python baseline -> 再跑 xor_engine RTL regression
```

否则第 29 轮新增 runner 的教学价值被埋在子目录里。

### P1 - 缺少 Icarus Verilog 时，错误信息对新手不友好

我用只保留 Python 目录的 `PATH` 模拟缺少 `iverilog` / `vvp`，执行：

```bash
python rtl/xor_engine/run_tests.py
```

结果不是项目级提示，而是 Python traceback，核心错误为：

```text
FileNotFoundError: [WinError 2] 系统找不到指定的文件。
```

这对熟悉 Python/subprocess 的维护者能看懂，但对第一次接触 RTL 仿真的读者不够友好。理想提示应直接说明：

```text
Missing tool: iverilog
Install Icarus Verilog and make sure iverilog/vvp are in PATH.
```

同时最好在 README 写清楚 Windows 下安装后需要重新打开终端。

### P1 - runner 对仿真失败的退出码依赖不够严谨

当前 `tb_xor_engine.v` 在发现 mismatch 时会打印：

```text
FAIL xor_engine cases=5 errors=2
```

但仿真进程本身仍可能返回 `0`。第 29 轮的 runner 通过扫描输出中是否包含 `PASS xor_engine` 来补了一层判断，这是有效的；但维护者视角看，testbench 本身最好在失败时 `$fatal` 或 `$finish` 前给出非零语义。

风险不是当前 runner 立刻失效，而是后续有人绕开 runner 直接执行：

```bash
vvp rtl/xor_engine/tb_xor_engine.vvp
```

可能只看退出码而忽略输出里的 `FAIL`。

### P1 - 参数化 testbench 仍由 Python 字符串临时生成，不宜直接复制给后续模块

第 29 轮临时生成参数化 testbench 的方式适合快速闭环，但如果 `lba_mapper`、`stripe_manager` 继续沿用“Python 拼 Verilog 字符串”的方式，后续会出现几个问题：

1. Verilog 测试逻辑难以被单独阅读；
2. 多模块共享检查逻辑困难；
3. 错误定位会混在 Python 生成器和 Verilog testbench 之间；
4. 学习者看不到稳定的 RTL testbench 模板。

更好的下一步不是大重构，而是先给 `xor_engine` 提炼一个轻量固定模板，例如：

```text
sim/testbenches/tb_xor_engine_param.v
```

或至少把 Python 中的临时模板抽成清晰函数并注明“只适用于小型参数矩阵，不作为复杂模块范式”。

### P2 - `sim/` 目录存在但没有统一说明，容易让读者困惑

实际查看发现：

```text
sim/
  golden_model/
  testbenches/
```

但当前 `xor_engine` 回归仍完全位于：

```text
rtl/xor_engine/run_tests.py
```

这不是错误；单模块阶段放在模块目录内可以接受。问题是根 README 已经把 `sim/` 描述为“仿真和 golden model”，读者会自然期待这里有仿真入口。现在 `sim/` 与 `rtl/xor_engine/run_tests.py` 的关系尚未解释。

建议不要马上重构全部目录，但需要加一个轻量说明：当前先用模块内 runner，等出现第二个 RTL 模块后再统一 `sim/run_all.py`。

## 验证记录

### 正常回归

执行：

```bash
python rtl/xor_engine/run_tests.py
```

结果通过，包含：

```text
PASS xor_engine cases=5
PASS_PARAM ww=8 ic=2 cases=3
PASS_PARAM ww=16 ic=3 cases=2
PASS_PARAM ww=64 ic=5 cases=1
PASS xor_engine regression: default + parameter matrix
```

说明第 29 轮的核心功能可运行。

### 缺工具模拟

模拟 `PATH` 中没有 `iverilog` / `vvp` 后，脚本退出并打印 Python traceback。该行为可定位问题，但不适合新手教学。

### 输出错误模拟

临时把 `xor_engine` 输出改为全 0 后，testbench 能打印具体失败用例：

```text
FAIL case 3: ffffffff ^ 00000000 ^ 12345678 ^ 12345678 => got 00000000 expected ffffffff
FAIL case 4: deadbeef ^ cafebabe ^ 01020304 ^ 11223344 => got 00000000 expected 04733411
FAIL xor_engine cases=5 errors=2
```

这个失败信息是有价值的：它包含输入、实际输出、期望输出。短板只在退出码语义和 runner 错误包装。

## 不够出色的地方

当前产物更像“模块作者能跑的回归脚本”，还不是“闯关读者自然会跑的关卡入口”。

一个更出色的版本应该让读者从根 README 看到：

1. 第一关：Python RAID 模型；
2. 第二关：RTL XOR 小模块；
3. 每关一条命令；
4. 如果缺工具，错误提示直接告诉怎么修；
5. 后续 RTL 模块会逐步汇入同一仿真路线。

## 下轮建议做什么

第 31 次唤醒应进入改进阶段，建议只做一个小闭环：**把 RTL 回归入口变得可发现、失败更友好。**

优先顺序：

1. 在根 `README.md` 增加“快速验证路线”或“当前可运行关卡”，加入：
   ```bash
   python -m pytest -q labs/level0_python_model
   python rtl/xor_engine/run_tests.py
   ```
2. 在 `rtl/xor_engine/run_tests.py` 中捕获 `FileNotFoundError`，对 `iverilog` / `vvp` 缺失输出项目级提示；
3. 在 `rtl/xor_engine/tb_xor_engine.v` 中让失败路径产生更明确的失败语义，至少文档提醒不要只看 `vvp` 退出码；
4. 暂不大迁移目录，只在 README 或 `sim/` 说明当前策略：单模块 runner 先放模块目录，第二个 RTL 模块出现后再考虑统一 `sim/run_all.py`。
