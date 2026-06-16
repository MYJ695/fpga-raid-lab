# Changelog - Wake 41

## 阶段

第 41 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake40.md`，只做一个小闭环：把两个 RTL runner 的默认 Icarus Verilog 编译输出从模块源码目录移到临时目录，减少新读者运行仿真后的目录噪声。

## 本轮做了什么

1. 调整 `rtl/xor_engine/run_tests.py`：
   - 默认 testbench 仍使用已签入的 `tb_xor_engine.v`；
   - 编译出的 `tb_xor_engine.vvp` 改为放入 `tempfile.TemporaryDirectory(prefix="xor_engine_default_")`；
   - `vvp` 直接运行临时目录中的产物，退出后自动清理。
2. 调整 `rtl/lba_mapper/run_tests.py`：
   - 默认 testbench 仍使用已签入的 `tb_lba_mapper.v`；
   - 编译出的 `tb_lba_mapper.vvp` 改为放入 `tempfile.TemporaryDirectory(prefix="lba_mapper_default_")`；
   - 保持参数化矩阵原有临时目录策略不变。
3. 清理本轮之前遗留在模块目录里的旧 `.vvp`：
   - `rtl/xor_engine/tb_xor_engine.vvp`
   - `rtl/lba_mapper/tb_lba_mapper.vvp`

## 修改了哪些文件

- `rtl/xor_engine/run_tests.py`
- `rtl/lba_mapper/run_tests.py`
- `notes/changelog_wake41.md`

## 如何验证

先删除旧的模块目录 `.vvp`，确认运行前没有残留：

```text
remaining before run: []
```

然后实际执行：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
12 passed
```

最后检查 RTL 模块目录下是否又生成 `.vvp`：

```text
rtl vvp artifacts after run: []
```

说明：默认 testbench 仍然可运行，但编译产物不再污染 `rtl/*/` 源码目录。

## 发现的问题

1. 第一次验证时误用了 Bash here-doc 写法 `python - <<'PY'`，但当前执行环境是 PowerShell，导致语法错误。
   - 已改用 Python 脚本统一调度命令，验证通过；
   - 后续在 Windows/PowerShell 环境下避免混用 Bash 重定向语法。
2. `temp/fpga-raid-lab` 仍不是独立 Git 仓库。
   - `git status` 显示的是上层 GA 仓库状态，且包含大量与本项目无关的修改；
   - 因此本轮没有用 Git diff 作为最终判据，而是用文件读回、回归运行、产物残留检查闭环。

## 下轮建议

第 42 轮进入检验阶段，建议从 **新读者运行 RTL 实验 + 项目发布清洁度** 的角度复检：

1. 重新按 README/RTL README 路线运行两个 RTL runner，确认输出信息对初学者仍清楚；
2. 检查 `.vvp` 不再残留后，是否还有其他运行副产物会污染教学目录，例如生成的 `.mem` 向量文件是否应继续保留；
3. 对照 `sim/README.md`，判断是否需要下一轮补一个很小的统一仿真入口草图，而不是直接实现完整 `sim/run_all.py`；
4. 继续避免扩大范围，不要把 runner 清理和新的 RTL 模块开发混在同一轮。
