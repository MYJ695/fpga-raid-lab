# Inspection - Wake 38

## 阶段

第 38 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake37.md`，从 **新读者入口、RTL 综合审查、项目维护边界** 三个视角，复检第 37 轮对 `lba_mapper` 的收口改进是否真正闭环。

## 本轮检验了什么

1. 复读第 37 轮交付物：
   - `README.md`
   - `rtl/README.md`
   - `rtl/lba_mapper/README.md`
   - `rtl/lba_mapper/run_tests.py`
   - `rtl/lba_mapper/tb_lba_mapper.v`
   - `labs/level0_python_model/raid_model.py`
2. 实际执行回归：
   - `python rtl/lba_mapper/run_tests.py`
   - `python rtl/xor_engine/run_tests.py`
   - `python -m pytest -q labs/level0_python_model`
3. 补查项目维护状态：
   - 根 `README.md` 的快速命令块；
   - `rtl/` 当前模块状态表；
   - `.gitignore`；
   - `rtl/*/*.vvp` 仿真产物是否已经落盘。

## 及格线结果

通过。

```text
python rtl/lba_mapper/run_tests.py
PASS lba_mapper regression: default + parameter matrix

python rtl/xor_engine/run_tests.py
PASS xor_engine regression: default + parameter matrix

python -m pytest -q labs/level0_python_model
12 passed in 0.05s
```

第 37 轮针对 Wake 36 的三个主要问题已经收口：

- 根 `README.md` 的快速命令块已包含 `python rtl/lba_mapper/run_tests.py`；
- `rtl/lba_mapper/README.md` 已说明 `/`、`%` 是教学版写法，不是最终高性能 datapath；
- `rtl/lba_mapper/run_tests.py` 已引入 `cross_check_python_raid0()`，对 `CHUNK_SHIFT=0` 用 `RAID0.map_lba()` 做交叉校验。

## 质量判断

当前 `lba_mapper` 小关卡已经从“能跑”推进到“读者知道它为什么这么写、边界在哪里”。

比较好的点：

1. **入口闭环更完整**  
   新读者按根 `README.md` 的命令块执行时，会同时跑 Python 模型、XOR RTL 和 LBA mapper RTL，不会漏掉新增模块。

2. **教学边界讲清楚了**  
   `rtl/lba_mapper/README.md` 明确把当前实现定位为教学版：先用公式把 RAID0 映射讲清楚，再提醒真实硬件里 `/`、`%` 需要资源友好的替代实现。

3. **golden 漂移风险下降了**  
   runner 仍保留带 `CHUNK_SHIFT` 的独立公式，但在 `CHUNK_SHIFT=0` 场景下会额外对拍 Python `RAID0.map_lba()`。这对当前模型能力来说是合适的折中。

## 发现的问题

### P1：仿真产物 `.vvp` 已经落盘，但 `.gitignore` 没有忽略

当前目录里已经出现：

```text
rtl/lba_mapper/tb_lba_mapper.vvp
rtl/xor_engine/tb_xor_engine.vvp
```

它们是 Icarus Verilog 编译产物，不应作为长期教学源码的一部分。当前 `.gitignore` 只忽略了 Python 缓存、虚拟环境和编辑器噪声，没有覆盖 Verilog/VCD/仿真输出。

建议第 39 轮做一个很小的维护补丁：

```gitignore
# Verilog/Icarus simulation outputs
*.vvp
*.vcd
```

是否删除已经生成的 `.vvp` 文件要看项目管理策略：

- 如果这些文件还未被纳入版本管理，只需 `.gitignore` 防止后续误加入；
- 如果它们已经被跟踪，后续应单独做一次清理提交；
- 当前 `fpga-raid-lab` 位于上层 GA 仓库内，直接用上层 `git status` 会混入大量无关改动，因此清理前最好先明确本项目的版本管理边界。

### P2：README 路线开始变长，但尚未到必须拆分

根 `README.md` 的通关路线已经到 Step 12。当前仍可接受，因为每一步都短、顺序清楚。

但如果继续加入 `stripe_manager`、系统级仿真、RAID5 RTL，建议提前拆成两层：

- **15 分钟快速路线**：只跑 demo、pytest、两个 RTL runner；
- **完整学习路线**：逐页阅读 docs，再进入 RTL 和 sim。

这不是本轮必须改的问题，等下一个 RTL 模块出现时再处理更自然。

### P2：Python golden helper 还没统一成共享抽象

第 37 轮的 `cross_check_python_raid0()` 已经降低了漂移风险，但 `CHUNK_SHIFT>0` 仍只存在于 RTL runner 的公式里。

后续如果继续扩展映射逻辑，建议把 RAID0 映射抽成共享纯函数，例如：

```python
map_raid0_lba(lba, disk_count, chunk_size_blocks=1)
```

然后：

- Python `RAID0.map_lba()` 复用它；
- RTL runner 复用它生成 golden；
- 文档示例也围绕同一个函数解释。

当前不建议立刻做，因为现有 Python 模型是“每 block 条带”的教学模型，强行加入 chunk 参数会扩大改动半径。

## 不够出色的点

`lba_mapper` 的功能质量已经合格，但项目维护层还有两个小毛刺：

1. 生成物和源码边界还没完全干净；
2. `fpga-raid-lab` 没有独立 Git 边界，导致 `git status` 容易看到上层 GA 仓库的大量无关变化。

这两个问题不影响仿真正确性，但会影响后续长期迭代时的可维护性。

## 下轮建议

第 39 轮建议进入改进阶段，做一个低风险维护闭环：**清理仿真产物边界**。

建议修改：

1. `.gitignore`
   - 增加 `*.vvp`；
   - 增加 `*.vcd`；
   - 可选增加 `sim_build/` 或 `build/`，但不要过度扩展。
2. 可选：runner 输出路径
   - 继续输出到模块目录也可以；
   - 更干净的方案是输出到临时目录或统一 `sim_build/`，但这会比 `.gitignore` 补丁更大。
3. 记录版本管理边界
   - 在下一轮 changelog 里说明：本项目目前位于上层 GA 仓库工作区内，暂不处理上层无关改动。

验证建议：

```bash
python rtl/lba_mapper/run_tests.py
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```
