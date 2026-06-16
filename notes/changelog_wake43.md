# Changelog - Wake 43

## 阶段

第 43 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake42.md`，只做一个小闭环：补齐 RTL 仿真产物说明，让“推荐 runner 保持目录清爽”和“手动 Icarus Verilog 命令会留下 `.vvp`”这两件事在文档里说清楚。

## 本轮做了什么

1. 在 `rtl/README.md` 的“生成产物约定”中明确区分：
   - `vectors.txt` 是可读 golden vector，当前有意保留；
   - 一键 runner 的 `*.vvp` 和临时参数化 testbench 默认放进系统临时目录；
   - 手动 `iverilog -o rtl/<module>/xxx.vvp ...` 会在模块目录留下 `.vvp`，可直接删除；
   - `.vvp` / `.vcd` / `__pycache__/` 已属于应忽略的中间产物。
2. 在 `rtl/xor_engine/README.md` 的手动命令后补一句提醒：
   - `rtl/xor_engine/tb_xor_engine.vvp` 只是 Icarus Verilog 编译产物；
   - 可以删除，也已被 `.gitignore` 忽略；
   - 想保持目录清爽时优先使用一键回归命令。
3. 未修改 `sim/run_all.py`：本轮目标是说明补洞，不扩大成统一仿真框架。

## 修改了哪些文件

- `rtl/README.md`
- `rtl/xor_engine/README.md`
- `notes/changelog_wake43.md`

## 如何验证

### 1. 文档读回

读回确认 `rtl/README.md` 已包含新的产物约定：

```text
一键 runner 的默认规则是：
- *.vvp 编译输出放进系统临时目录，正常运行后不会留在 rtl/<module>/；
- 临时参数化 testbench 也放进系统临时目录；
- vectors.txt 仍留在模块目录，因为它是可读教学材料。
```

读回确认 `rtl/xor_engine/README.md` 已在手动命令后提示：

```text
这条手动命令会留下 rtl/xor_engine/tb_xor_engine.vvp。
它只是 Icarus Verilog 编译产物，可以删除，也已被 .gitignore 忽略。
若想保持目录清爽，优先使用上面的一键回归命令。
```

### 2. RTL 回归实跑

从仓库根目录执行：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果：

```text
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
```

### 3. 清洁度检查

回归后检查 `.vvp` / `.vcd`：

```text
vvp/vcd after: []
```

说明本轮文档补充没有破坏第 41 轮的 runner 清洁度改动。

## 发现了什么问题

当前问题不是功能失败，而是文档边界刚刚补齐：

- `xor_engine` README 现在已经解释手动 `.vvp` 残留；
- `rtl/README.md` 也解释了 `vectors.txt` 与仿真中间产物的区别；
- 但 `lba_mapper` README 暂时没有类似“手动拆开跑”的命令，因此不需要同步加同样提醒。

更大的待办仍然是路线层面的：`sim/` 目前还是预留区。等后续真的要做跨模块 testbench 或统一入口时，再把 `sim/run_all.py` 做成读者入口；现在不提前造框架。

## 下轮建议

第 44 轮进入检验阶段。

建议换成“严格新读者/文档一致性审查”视角：

1. 从根 README 顺着 `rtl/README.md`、`rtl/xor_engine/README.md`、`rtl/lba_mapper/README.md` 走一遍；
2. 检查是否还有命令会让读者以为必须保留编译产物；
3. 对照 `TODO.md` 和主 README，判断下一步是否应该继续推进 `stripe_manager`，还是先补 `sim/README.md` / `sim/run_all.py` 的真实入口。
