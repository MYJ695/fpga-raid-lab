# Changelog - Wake 45

## 阶段

第 45 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake44.md` 的检验结论，只做一个文档一致性小闭环：让根 README、`sim/README.md` 与当前两个 RTL 单模块 runner 的真实状态对齐。

## 本轮做了什么

1. 在根 `README.md` 的手动 XOR/Icarus Verilog 命令块后，补充 `.vvp` 产物说明。
2. 更新 `sim/README.md` 的当前单模块入口，从只列 `xor_engine` 改为同时列出：
   - `python rtl/xor_engine/run_tests.py`
   - `python rtl/lba_mapper/run_tests.py`
3. 保持 `sim/run_all.py` 不创建：当前仍以模块目录内 runner 为主，等出现跨模块联合对拍或更多 RTL 模块后再收敛到 `sim/`。
4. 重新跑两个 RTL runner，确认文档推荐入口仍可运行且不在仓库内留下 `.vvp/.vcd`。

## 修改了哪些文件

- `README.md`
- `sim/README.md`
- `notes/changelog_wake45.md`

## 关键改动

### 根 README

手动命令后新增提醒：

```text
这条手动命令会在 rtl/xor_engine/ 留下 tb_xor_engine.vvp。
它只是 Icarus Verilog 编译产物，可以删除，也已被 .gitignore 忽略；
若想保持目录清爽，优先使用上面的一键 runner。
```

这样只读根 README 的新读者也能区分：

- 一键 runner：推荐入口，临时产物在系统临时目录内；
- 手动 `iverilog -o ... .vvp`：教学拆解命令，会在模块目录留下可删除编译产物。

### sim README

当前单模块入口改成：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

并把后续收敛条件改得更具体：等 `stripe_manager` 也有独立回归，或者出现 `xor_engine + lba_mapper` 联合对拍后，再把跨模块总入口收敛到 `sim/`。

## 如何验证

### 1. 读回文档

已读回确认：

- `README.md` 包含 `tb_xor_engine.vvp` 残留提醒；
- `README.md` 仍列出 `python rtl/lba_mapper/run_tests.py`；
- `sim/README.md` 同时列出 XOR 与 LBA mapper 两个 runner；
- `sim/README.md` 明确提到未来 `xor_engine + lba_mapper` 联合对拍。

### 2. 跑 RTL 单模块回归

已执行：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果：

```text
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
residue []
```

说明推荐入口仍能运行，且仓库内没有 `.vvp/.vcd` 残留。

## 发现了什么问题

本轮没有发现新的功能性问题。

但从文档路线看，当前 RTL 章节已经进入“两个单模块都能跑”的阶段，下一轮检验可以升级视角：不要只检查入口是否能跑，而要从“读者能否理解 RTL 与 Python golden model 的关系”出发，检查根 README、`rtl/README.md`、`sim/README.md` 是否足够解释：

```text
Python 模型负责行为直觉和 golden reference；
RTL 小模块负责把一个局部逻辑问题硬件化；
runner/testbench 负责把两者用 vector 对拍。
```

## 下轮建议做什么

第 46 轮进入检验阶段。建议用“懂 FPGA 但不懂 RAID 的读者”视角检查：

1. 根 README 的路线是否能把 Python 模型、RTL 小模块、testbench 对拍串起来；
2. `rtl/README.md` 是否解释清楚为什么当前顺序是 `xor_engine -> lba_mapper -> stripe_manager`；
3. `sim/README.md` 是否足够说明什么时候才需要跨模块仿真；
4. 是否存在“能跑但读者不知道为什么要跑”的断点。
