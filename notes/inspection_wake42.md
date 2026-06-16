# Inspection - Wake 42

## 阶段

第 42 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake41.md`，从 **新读者运行 RTL 实验 + 项目发布清洁度** 的角度复检第 41 轮改动：默认 runner 是否仍好用、`.vvp` 是否不再污染模块目录、文档里的手动命令是否和“清洁运行”目标一致。

## 检验方法

1. 读取入口与说明文档：
   - `README.md`
   - `rtl/README.md`
   - `rtl/xor_engine/README.md`
   - `rtl/lba_mapper/README.md`
   - `sim/README.md`
   - `.gitignore`
2. 按新读者的一键路径实跑两个 RTL runner：
   - `python rtl/xor_engine/run_tests.py`
   - `python rtl/lba_mapper/run_tests.py`
3. 额外模拟 `xor_engine` README 中的手动 Icarus Verilog 拆解命令：
   - `python rtl/xor_engine/gen_vectors.py`
   - `iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v`
   - `vvp rtl/xor_engine/tb_xor_engine.vvp`
4. 检查运行后的副产物：
   - `.vvp`
   - `.vcd`
   - `vectors.txt`

## 检验结果

### 1. 一键 runner 已达到第 41 轮目标

两个 runner 均能通过：

```text
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
```

运行后检查：

```text
after runner .vvp: []
```

结论：第 41 轮把默认 `.vvp` 输出改到临时目录是有效的。新读者只执行推荐的一键命令时，源码目录不会留下 Icarus 编译产物。

### 2. `.gitignore` 对仿真产物有兜底

当前 `.gitignore` 已包含：

```text
*.vvp
*.vcd
```

这能兜住手动仿真、后续波形导出或临时调试产生的常见 Icarus/Verilog 产物。即使读者自己生成 `.vvp`，也不容易误提交。

### 3. `vectors.txt` 是有意保留的教学产物，不建议立刻移入临时目录

当前运行后存在：

```text
rtl/lba_mapper/vectors.txt
rtl/xor_engine/vectors.txt
```

这不是同类问题：

- `.vvp` 是编译产物，读者通常不需要阅读；
- `vectors.txt` 是 golden vector，可读、可对拍、能帮助初学者理解输入/期望输出；
- 两个模块 README 都把 vector 文件作为模块组成部分说明。

结论：本轮不建议把 `vectors.txt` 改成临时文件。若后续 vector 规模变大，再考虑区分 `examples/` 与 generated vectors。

## 发现的问题

### P1：文档手动命令仍会在模块目录生成 `.vvp`

`rtl/xor_engine/README.md` 的手动拆解命令仍是：

```bash
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
```

实测结果：

```text
after README manual .vvp: ['rtl/xor_engine/tb_xor_engine.vvp']
```

虽然 `.gitignore` 会忽略它，但从“新读者运行后目录清爽”的体验看，这和第 41 轮清洁 runner 的方向不一致。

这不是功能错误，因为命令能通过并输出：

```text
PASS xor_engine cases=5
```

但它是体验瑕疵：推荐路径是干净的，手动教学路径却会制造残留。

### P2：手动命令只覆盖 `xor_engine`，`lba_mapper` README 没有对应拆解说明

`lba_mapper` README 目前只推荐：

```bash
python rtl/lba_mapper/run_tests.py
```

这保持了清洁，但两个 RTL 模块的说明粒度略不一致。考虑到 `xor_engine` 是第一块 RTL 小模块，保留手动拆解有教学价值；但如果继续保留，最好顺手说明“手动命令会生成可删除的 `.vvp`，一键 runner 不会残留”。

### P3：`sim/README.md` 仍保持克制，暂不需要实现 `sim/run_all.py`

`sim/README.md` 明确说当前 `sim/` 只是跨模块仿真预留区，不急着建立统一入口。结合当前只有两个独立 RTL runner，继续不实现 `sim/run_all.py` 是合理的。

但下一轮可以考虑补一个很小的“未来入口草图”，只放命令形态，不实现脚本，帮助读者理解什么时候会进入 `sim/`。

## 不够出色的点

当前项目已经能跑，但还不够“发布级顺滑”：

1. 推荐一键路径和手动教学路径的副产物行为不一致；
2. 读者看到 `.vvp` 残留时，虽然不会被 Git 跟踪，但不知道它是否可以删除；
3. `vectors.txt` 是保留的教学产物，但 README 没有明确把它和 `.vvp` 这类临时产物区分开。

## 下轮建议

第 43 轮进入改进阶段，建议只做一个小闭环：**补齐 RTL 仿真产物说明，而不是重写 runner**。

优先改动建议：

1. 在 `rtl/README.md` 增加一个很短的“仿真产物约定”：
   - 一键 runner 的 `.vvp` 放在系统临时目录，正常不会残留；
   - 手动 `iverilog -o .../*.vvp` 会生成可删除产物；
   - `.vvp`/`.vcd` 已被 `.gitignore` 忽略；
   - `vectors.txt` 是可读 golden vector，当前有意保留。
2. 在 `rtl/xor_engine/README.md` 的手动命令下面补一句：
   - 该手动命令会留下 `tb_xor_engine.vvp`，可以删除；若想保持目录清爽，用 `python rtl/xor_engine/run_tests.py`。
3. 暂不修改 `sim/run_all.py`，避免把说明修补扩大成新框架实现。
