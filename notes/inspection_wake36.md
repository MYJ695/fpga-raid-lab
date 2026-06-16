# Inspection - Wake 36

## 阶段

第 36 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake35.md`，从 **硬件综合 / RTL 代码审查者 + 新读者跑通路线** 两个视角检查 `rtl/lba_mapper` 小闭环是否既能跑、又讲清楚边界。

## 本轮检验了什么

1. 复读第 35 轮交付物：
   - `rtl/lba_mapper/lba_mapper.v`
   - `rtl/lba_mapper/tb_lba_mapper.v`
   - `rtl/lba_mapper/run_tests.py`
   - `rtl/lba_mapper/README.md`
   - 根 `README.md`
   - `TODO.md`
2. 实际执行回归：
   - `python rtl/lba_mapper/run_tests.py`
   - `python -m pytest labs/level0_python_model -q`
3. 对照 Python 模型：
   - `labs/level0_python_model/raid_model.py` 中 `RAID0.map_lba()` 目前定义为 `lba % len(disks), lba // len(disks)`；
   - `rtl/lba_mapper` 在 `CHUNK_SHIFT=0` 时与此一致；
   - `CHUNK_SHIFT>0` 是 RTL 关卡新增的 chunk-size 泛化，Python `RAID0.map_lba()` 还没有等价参数。

## 及格线结果

通过。

```text
python rtl/lba_mapper/run_tests.py
PASS lba_mapper regression: default + parameter matrix

python -m pytest labs/level0_python_model -q
12 passed in 0.05s
```

当前 `lba_mapper` 至少满足：

- 默认 `DISK_COUNT=4, CHUNK_SHIFT=0` 可由固定 testbench 读取 vector 检查；
- `DISK_COUNT=3, CHUNK_SHIFT=2` 覆盖非 2 的幂盘数 + 4-LBA chunk 边界；
- `DISK_COUNT=5, CHUNK_SHIFT=0` 覆盖另一个非 2 的幂盘数组合；
- 修复后的 `chunk_offset = lba - (logical_chunk << CHUNK_SHIFT)` 没有复现第 35 轮发现的 offset 丢失问题。

## 发现的问题

### P1：根 README 的快速命令块漏掉了 lba_mapper

根 `README.md` 的通关路线已经有：

```text
Step 11：跑 RTL LBA mapper：执行 python rtl/lba_mapper/run_tests.py
```

但紧跟着的 bash 快速命令块仍只列出：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
```

这会让按命令块复制执行的新读者漏跑新模块。第 37 轮应把 `python rtl/lba_mapper/run_tests.py` 加进去，并顺手调整下面那句“当前 RTL 关卡的一键入口”不要只说 `xor_engine`。

### P1：`/` 和 `%` 的硬件代价没有在交付物中讲透

`lba_mapper.v` 现在是：

```verilog
assign disk_index   = logical_chunk % DISK_COUNT;
assign stripe_index = logical_chunk / DISK_COUNT;
```

对学习来说很清楚，但对 FPGA 读者来说，这等于把“常量除法/取模”的综合代价交给工具。尤其 `DISK_COUNT=3/5` 这类非 2 的幂参数，可能生成比移位/掩码更重的组合逻辑。

这不是功能 bug，但如果文档不提醒，读者可能误以为这就是最终 datapath 写法。第 37 轮应在 `rtl/lba_mapper/README.md` 增加“教学版 vs 可综合优化版”的小节：

- power-of-two `DISK_COUNT` 可用低位选择和右移；
- 非 2 的幂可考虑固定常量除法优化、查表、递减比较、或前级调度约束；
- 第一版保留 `/`、`%` 是为了让公式可读、可测，不是最终高频实现。

### P2：`run_tests.py` 的 golden 公式和 Python 模型存在漂移风险

`rtl/lba_mapper/run_tests.py` 内部有独立 `golden()`：

```python
disk_index = logical_chunk % disk_count
stripe_index = logical_chunk // disk_count
disk_lba = (stripe_index << chunk_shift) + chunk_offset
```

它与 RTL README 的公式一致，但没有直接复用 `labs/level0_python_model/raid_model.py`。当前原因可以理解：Python `RAID0.map_lba()` 只支持 `CHUNK_SHIFT=0` 的每块条带，没有 chunk-size 参数。

但长期看，Python 模型、文档公式、RTL runner 三处各自维护，容易产生“测试和 RTL 一起错”的风险。第 37 或后续轮可选两种小改法：

1. 给 Python 模型补一个纯函数，例如 `map_raid0_lba(lba, disk_count, chunk_size_blocks=1)`，runner 复用它；
2. 或在 runner 里至少对 `CHUNK_SHIFT=0` 的 case 交叉调用 `RAID0.map_lba()`，保留 `CHUNK_SHIFT>0` 的扩展公式。

### P2：端口宽度策略过于粗糙，但尚可接受

`disk_index` 固定为 `[7:0]`，对教学足够；但 README 没有说明这意味着：

- `DISK_COUNT` 实际应小于等于 256；
- 更严谨 RTL 会从 `DISK_COUNT` 推导 `$clog2(DISK_COUNT)` 宽度；
- 当前坚持 Verilog-2001 + Icarus 简洁路线，所以先不用 SystemVerilog 风格参数化端口宽度。

第 37 轮可以在 README 的参数/端口表里补一句限制，不必急着改 RTL。

## 不够出色的点

`lba_mapper` 现在“能跑”，但还没有做到“硬件读者一眼知道哪些是教学简化”。

如果目标是 FPGA RAID 学习实验室，而不仅是跑过 testbench，那么每个 RTL 小模块都应该明确分三层：

1. **数学公式**：先保证 RAID 逻辑对；
2. **教学 RTL**：直接可读、可仿真；
3. **未来硬件化方向**：哪些表达式需要换成 pipeline、LUT、FSM 或调度约束。

`xor_engine` 天然简单，所以这个边界不明显；`lba_mapper` 一出现 `/`、`%`，这个边界就必须写出来。

## 下轮建议

第 37 轮进入改进阶段，建议只做一个小闭环：**把 lba_mapper 的读者入口和硬件边界补清楚**。

建议修改：

1. `README.md`
   - 在 bash 快速命令块加入 `python rtl/lba_mapper/run_tests.py`；
   - 把“当前 RTL 关卡的一键入口”改成同时提 `xor_engine` 和 `lba_mapper`。
2. `rtl/lba_mapper/README.md`
   - 增加“教学版除法/取模，不是最终高性能 datapath”小节；
   - 补 `disk_index [7:0]` 的教学限制；
   - 说明 `DISK_COUNT=3/5` 是为了抓边界，不代表推荐真实硬件直接这样做。
3. 可选小改：`rtl/lba_mapper/run_tests.py`
   - 对 `CHUNK_SHIFT=0` 的 golden 增加与 `RAID0.map_lba()` 的交叉检查，降低漂移风险。

验证建议：

```bash
python rtl/lba_mapper/run_tests.py
python rtl/xor_engine/run_tests.py
python -m pytest labs/level0_python_model -q
```
