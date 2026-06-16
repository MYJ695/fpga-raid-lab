# Changelog - Wake 27

## 阶段

第 27 次唤醒：改进阶段。

本轮根据 `notes/inspection_wake26.md` 的 P0 建议，只做一个小闭环：把空的 `rtl/xor_engine/` 变成第一块能生成向量、能编译、能仿真、能和 Python 思路对拍的 RTL 小实验。

## 本轮做了什么

- 新增 `xor_engine` 组合 RTL：参数化 `WORD_WIDTH` 和 `INPUT_COUNT`；
- 新增 Python vector 生成脚本，输出 4 输入 32-bit XOR 的 golden cases；
- 新增 Verilog testbench，用 `$fscanf` 读取 vector 并比较输出；
- 新增 `rtl/xor_engine/README.md`，说明接口、vector 格式和仿真命令；
- 更新根 `README.md`，把 RTL XOR 加入通关路线和可运行入口；
- 更新 `TODO.md`，标记组合 XOR 小实验完成，并把下一步推进到 `rtl/lba_mapper/`。

## 修改了哪些文件

```text
README.md
TODO.md
rtl/xor_engine/README.md
rtl/xor_engine/gen_vectors.py
rtl/xor_engine/vectors.txt
rtl/xor_engine/xor_engine.v
rtl/xor_engine/tb_xor_engine.v
notes/changelog_wake27.md
```

## 如何验证

已实测：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
python -m pytest -q labs/level0_python_model
```

结果：

```text
wrote .../rtl/xor_engine/vectors.txt cases=5
PASS xor_engine cases=5
12 passed in 0.05s
```

额外检查：

- `README.md` 已包含 `rtl/xor_engine/` 入口；
- `TODO.md` 已将组合版 `rtl/xor_engine` 标记完成；
- `vectors.txt` 没有注释表头，避免旧版 Icarus Verilog 在 `$fscanf` 遇到非 hex 行时卡住；
- 第一版保持纯组合逻辑，没有引入 `clk/rst/valid/ready`。

## 发现了什么问题

- 本机 Icarus Verilog 版本较旧，`$fscanf` 读到 `# input0 ...` 这种注释表头时会卡住；本轮已改成无表头纯数据文件。
- testbench 当前把 vector 路径写死为 `rtl/xor_engine/vectors.txt`，适合从仓库根目录运行；若以后支持从子目录运行，需要加 plusarg 或相对路径处理。
- 当前只覆盖 4 输入、32-bit 组合 XOR；参数化 RTL 有了，但 testbench 还不是多参数矩阵测试。

## 下轮建议做什么

第 28 次唤醒应进入检验阶段，建议用更苛刻的 RTL 测试工程师视角审查：

1. `xor_engine` 的参数化是否真的可信，是否需要 2/3/5 输入或 8/64-bit 变体测试；
2. testbench 是否应该在 EOF/空行/坏 vector 时更明确地失败；
3. README 的命令是否足够让第一次接触 Icarus 的读者跑通；
4. 下一块 `lba_mapper` 开工前，是否需要先抽一个统一的 `sim/` 运行脚本或 Makefile。
