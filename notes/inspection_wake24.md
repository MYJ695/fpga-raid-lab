# Inspection - Wake 24

## 阶段

第 24 次唤醒：检验阶段。

本轮不改交付物，重点从“准备进入 RTL 前的架构审查”视角检查：现有 Python/文档闭环是否已经足够自然地过渡到 `rtl/xor_engine`、`lba_mapper`、`stripe_manager` 等小实验。

## 检验范围

- `README.md`
- `TODO.md`
- `docs/00_big_picture.md`
- `docs/references.md`
- `docs/rebuild_and_scrub.md`
- `labs/level0_python_model/README.md`
- `labs/level0_python_model/raid_model.py`
- `labs/level0_python_model/demo_layout.py`
- `labs/level0_python_model/demo_write_hole.py`
- `labs/level0_python_model/demo_rebuild_and_scrub.py`
- `rtl/`
- `sim/`

## 实测验证

从仓库根目录执行了：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.06s
```

同时检查了 `README.md` 和 `docs/*.md` 中的本地 Markdown 链接，当前链接均存在。

## 及格线结论

当前仓库作为 Level 0~5 的 Python/文档闭环已经及格：

1. RAID0/1/5、write path、write hole、rebuild/scrub 的学习路线能顺着 README 跑下来；
2. 三个 demo 都能从仓库根目录运行，且 pytest 通过；
3. `docs/00_big_picture.md` 已经给出 FPGA RAID Controller 的大模块图，包含 `lba_mapper`、`stripe_manager`、`parity_engine`、`rebuild_engine`；
4. TODO 已经列出后续 RTL 小实验方向：`rtl/xor_engine`、`rtl/lba_mapper`、`rtl/stripe_manager`、`sim/` 对拍。

但从“马上开始 RTL 小实验”的标准看，还不够出色。现在的问题不是 Python 模型不够，而是缺少一座明确的桥：读者知道下一步要做 RTL，却不知道第一个 RTL 模块为什么从 XOR 开始、它的输入输出应该长什么样、应该如何和 Python golden model 对拍。

## 发现的问题

### P0：`docs/fpga_architecture.md` 缺失，README 到 RTL 的过渡仍然太跳

目标任务列表中明确提到应补：

```text
docs/fpga_architecture.md
```

但当前 `docs/` 下不存在该文件。仓库里有 `docs/00_big_picture.md`，它适合作为世界观入口，但还不是 RTL 前置架构页。

`00_big_picture.md` 当前讲的是：

- FPGA RAID Controller 是调度官；
- 里面有 `cmd_queue`、`lba_mapper`、`stripe_manager`、`read/write_engine`、`parity_engine`、`rebuild_engine`；
- 第一阶段先用 Python/BRAM 模拟多块盘。

缺口是：它没有把这些名字落成“下一步要实现的最小 RTL 边界”。例如：

- `xor_engine` 先做组合逻辑还是流水线？
- `lba_mapper` 的输入是 logical LBA，输出应包含哪些字段？
- `stripe_manager` 和 `lba_mapper` 的边界如何区分？
- `scrub/rebuild FSM` 现在只在文档里出现，是否进入第一批 RTL？
- Python 的哪些函数是 golden model 参考？

影响：读者跑完 Level 5 后，会从“我懂了 RAID5 行为”突然跳到“rtl/ 目录是空的”。这不符合“闯关式实验室”的节奏。

### P1：README 说到 `RTL XOR/lba_mapper`，但没有可点击的架构入口

README 第 47 行已经写出路线：

```text
Python golden model → RAID0/1/5 行为跑通 → RAID5 写路径风险 → rebuild/scrub 维护路径 → RTL XOR/lba_mapper → testbench 对拍
```

这条路线方向正确，但“RTL XOR/lba_mapper”目前只是文字。当前可运行入口列表中没有：

- `docs/fpga_architecture.md`
- `rtl/xor_engine/README.md`
- `sim/README.md`

因此 README 对新读者的下一步引导会停在 Level 5，无法自然进入 Level 1 RTL。

### P1：TODO 缺少“RTL 前置任务”层，容易直接跳去写 Verilog

TODO 现在从：

```text
## Now：Level 0 Python 模型
```

直接跳到：

```text
## Later：RTL 小实验
- [ ] rtl/xor_engine
- [ ] rtl/lba_mapper
- [ ] rtl/stripe_manager
- [ ] sim/：记录 Icarus/Verilator 仿真命令，和 Python golden model 对拍
```

这比之前清楚，但仍少一层“Level 1 RTL 前置任务”。在进入 Verilog/SystemVerilog 前，至少应先完成：

1. 写 `docs/fpga_architecture.md`，定义最小模块边界；
2. 明确第一批 RTL 只做纯算法/控制片段，不碰 SATA/NVMe/PCIe；
3. 决定 RTL 语言和仿真工具；
4. 为 `xor_engine` 定义 test vector 来源：直接复用 Python `xor_blocks()`；
5. 为 `lba_mapper` 定义 test vector 来源：复用 `RAID0.map_lba()` 和 `RAID5.layout_row()`。

否则下一轮如果直接创建 RTL，很容易写出一个“能综合但教学上下文不够”的孤立模块。

### P2：Python 到 RTL 的映射关系尚未被显式列出

当前最适合映射的 Python/文档锚点如下：

| Python / 文档锚点 | 可映射 RTL 小模块 | 说明 |
|---|---|---|
| `xor_blocks()` | `rtl/xor_engine` | 多输入 XOR，是 RAID5 parity/rebuild 的核心数据通路 |
| `RAID0.map_lba()` | `rtl/lba_mapper` 第一版 | `disk_idx = lba % disk_count`，`disk_lba = lba // disk_count` |
| `RAID5.parity_disk()` / `layout_row()` | `rtl/lba_mapper` 第二版 | 计算 rotating parity 和数据盘位置 |
| `RAID5.write_full_stripe()` | `stripe_manager` / `parity_engine` | full-stripe write 的动作拆分和 parity 生成 |
| `demo_write_hole.py` | write ordering / fault injection 思考题 | 暂不急着 RTL 化，但用于说明 partial write 风险 |
| `demo_rebuild_and_scrub.py` | scrub/rebuild FSM 后续版 | 适合作为第二批 RTL，不应抢在 XOR/lba_mapper 前面 |

这张表目前不在交付物中。它应该进入 `docs/fpga_architecture.md`，让读者知道：不是为了写 RTL 而写 RTL，而是把已经跑通的 Python 行为逐块硬件化。

### P2：`rtl/` 和 `sim/` 为空，但仓库结构已经把它们列为正式目录

这不是错误，因为当前阶段还没开始 RTL。但对“持续扩展”的目标而言，空目录需要一个最小 README 或架构页承接，否则读者会误以为漏提交了文件。

建议不要下一轮就大规模补 RTL。更稳的小闭环是先补 `docs/fpga_architecture.md`，并在 README/TODO 里接入它。等架构边界清楚后，再创建第一个 `rtl/xor_engine`。

## 不够出色的地方

当前项目已经能“讲清楚 RAID5”，但还没有把“FPGA RAID”四个字里的 FPGA 部分真正点亮。

更苛刻地说：

- Python 模型已经像实验室；
- 文档路线已经像教程；
- 但 RTL 入口还像占位符。

如果目标读者是“懂 FPGA 但不懂 RAID 的人”，他现在会觉得前半段很友好，但到 RTL 前会问：

> 我应该先写哪个模块？这个模块的接口从哪里来？怎么证明它和前面的 Python 行为一致？

这就是下一轮最值得补的缺口。

## 建议第 25 轮怎么改

第 25 次唤醒应进入改进阶段，建议只做一个小闭环：**补一页轻量 `docs/fpga_architecture.md`，把 Python 行为映射到第一批 RTL 小模块，并接入 README/TODO。**

建议修改：

1. 新增 `docs/fpga_architecture.md`：
   - 说明第一阶段 RTL 边界：只做算法和控制小模块，不碰真实 SATA/NVMe/PCIe；
   - 画出最小路径：Host request → LBA mapper → stripe manager → XOR/parity engine → virtual disk ports；
   - 列出 Python 到 RTL 的映射表；
   - 明确第一批模块顺序：`xor_engine` → `lba_mapper` → `stripe_manager` → `sim` 对拍；
   - 把 scrub/rebuild FSM 放到第二批，不要抢跑。
2. 更新 `README.md`：
   - 在当前可运行入口中加入 `docs/fpga_architecture.md`；
   - 在通关路线 Step 9 后增加 “Step 10：看 FPGA 架构边界”。
3. 更新 `TODO.md`：
   - 新增 `Next：Level 1 RTL 前置架构`；
   - 把 `docs/fpga_architecture.md` 标为待做/完成；
   - 明确后续第一个 RTL 小闭环是 `rtl/xor_engine`，不是直接做完整 RAID 控制器。

验证建议：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```

并检查：

- README 新增链接存在；
- `docs/fpga_architecture.md` 没有把真实接口工作提前承诺；
- TODO 中 RTL 任务粒度仍然保持“小闭环”。
