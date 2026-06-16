# Changelog - Wake 39

## 阶段

第 39 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake38.md`，只做一个低风险维护闭环：补齐本项目自己的仿真产物忽略规则，避免 Icarus Verilog 编译产物和波形文件混入教学源码。

## 本轮做了什么

1. 更新 `.gitignore`：
   - 增加 `*.vvp`：忽略 Icarus Verilog 编译输出；
   - 增加 `*.vcd`：忽略后续 testbench 可能产生的波形文件。
2. 保持补丁范围很小：
   - 没有移动现有 runner 输出目录；
   - 没有引入统一 `build/` 或 `sim_build/`；
   - 没有处理上层 GA 仓库的无关 Git 状态。
3. 记录版本边界：
   - 当前 `temp/fpga-raid-lab` 位于上层 GA 仓库工作区内，本目录没有独立 `.git/`；
   - 从上层仓库看，`temp/` 已整体被忽略，所以本轮用项目内 `.gitignore` 维护“如果将来单独抽出这个项目”的源码边界。

## 修改了哪些文件

- `.gitignore`
- `notes/changelog_wake39.md`

## 如何验证

实际执行：

```bash
python rtl/lba_mapper/run_tests.py
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
PASS lba_mapper regression: default + parameter matrix
PASS xor_engine regression: default + parameter matrix
12 passed
```

同时读回 `.gitignore`，确认新增规则已经存在：

```text
# Verilog/Icarus simulation outputs
*.vvp
*.vcd
```

## 发现的问题

1. `temp/fpga-raid-lab` 当前不是独立 Git 仓库。
   - 因此从上层 GA 仓库运行 `git check-ignore` 时，命中的是上层 `.gitignore` 的 `temp/` 规则，而不是本项目 `.gitignore` 的 `*.vvp` / `*.vcd`。
   - 这不是功能错误，但说明后续如果要发布/迁移本项目，需要重新确认独立仓库下的 Git 状态。
2. `rtl/lba_mapper/run_tests.py` 的默认 testbench 仍会在模块目录生成 `tb_lba_mapper.vvp`。
   - 当前已通过 `.gitignore` 控制风险；
   - 更干净的做法是后续统一输出到临时目录或 `sim_build/`，但那属于下一轮更大一点的 runner 维护，不在本轮扩展。

## 下轮建议

第 40 轮建议进入检验阶段，从 **独立发布维护者 + 新读者克隆项目** 的视角检查：

1. 如果把 `temp/fpga-raid-lab` 单独拷出去，README 的快速验证路线是否仍完整；
2. runner 输出到模块目录是否会让新读者困惑；
3. 是否值得把 `rtl/xor_engine` 和 `rtl/lba_mapper` 的 `.vvp` 默认输出统一改到临时目录，减少源码目录噪声；
4. `sim/README.md` 是否需要提前给出一个“未来统一仿真入口”的最小命令草图。
