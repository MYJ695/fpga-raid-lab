# FPGA RAID Lab

> 把 FPGA RAID 这件事，从“听起来很硬核”拆成一张可以通关的地图。

## 一句话目标

本仓库用于维护 FPGA RAID 存储模块的早期调研、知识补课、实验代码和设计路线。

我们暂时不追求一上来做完整硬件 RAID 控制器，而是先把三件事理顺：

1. RAID 到底在解决什么问题；
2. FPGA 里哪些逻辑值得硬件化；
3. 从 Python 模型到 RTL 仿真，如何一步步跑通。

## 项目定位

这是一个 **学习型 + 设计型 + 实验型** 仓库。

不是资料堆场，也不是论文复读机。

每个阶段都要留下可检查产出：

- 一页解释；
- 一张图；
- 一个可运行模型；
- 一个 RTL 小模块或 testbench；
- 一条踩坑记录。

## 通关地图

| Level | 主题 | 核心问题 | 产出 |
|---|---|---|---|
| 0 | RAID 世界观 | 多块盘为什么要组队？ | Python 虚拟磁盘模型 |
| 1 | RAID0 | 怎么把数据条带化？ | LBA 映射 + 条带读写 |
| 2 | RAID1 | 怎么做镜像和故障切换？ | 双盘写入 + 单盘降级读 |
| 3 | RAID5 | XOR 校验怎么保护数据？ | full-stripe write + degraded read |
| 4 | 小写问题 | partial write 为什么麻烦？ | RMW / reconstruct write + write hole demo |
| 5 | 重建 | 坏盘换新盘怎么补数据？ | rebuild engine 模型 |
| 6 | RAID6 | 双校验为什么需要 GF？ | P/Q parity 学习实验 |
| 7 | 接真实设备 | 怎么接 SATA/NVMe/PCIe？ | 接口方案调研 |

## 当前优先级

先做 **Level 0 ~ Level 5** 的 Python/文档闭环：

```text
Python golden model → RAID0/1/5 行为跑通 → RAID5 写路径风险 → rebuild/scrub 维护路径 → FPGA 架构边界 → RTL XOR/lba_mapper → testbench 对拍
```

当前可运行入口背后的分工很简单：

```text
Python demo：先把 RAID 行为演给你看；
Python pytest：保证这些行为模型能作为 golden reference；
RTL runner：把同一条规则翻译成 Verilog，再用 vector/testbench 对拍。
```

当前可运行入口：

- [`TODO.md`](TODO.md)：小任务板；
- [`docs/raid_basics.md`](docs/raid_basics.md)：RAID0/1/5 入门桥接页；
- [`docs/raid0_mapping.md`](docs/raid0_mapping.md)：RAID0 LBA 到 disk/chunk 的映射公式；
- [`docs/raid1_mirror.md`](docs/raid1_mirror.md)：RAID1 镜像、故障切换和容量代价；
- [`docs/raid5_parity.md`](docs/raid5_parity.md)：RAID5 XOR 校验、轮转 parity 和降级读；
- [`docs/raid5_write_path.md`](docs/raid5_write_path.md)：RAID5 full-stripe write、RMW 和 reconstruct write；
- [`docs/write_hole.md`](docs/write_hole.md)：RAID5 partial write 被打断后的 data/parity 不一致风险；
- [`docs/rebuild_and_scrub.md`](docs/rebuild_and_scrub.md)：rebuild/scrub 如何发现或放大潜伏 mismatch；
- [`docs/fpga_architecture.md`](docs/fpga_architecture.md)：从 Python golden model 过渡到第一批 RTL 小模块；
- [`rtl/README.md`](rtl/README.md)：RTL 小模块目录约定和 runner 约定；
- [`rtl/xor_engine/`](rtl/xor_engine/)：第一块可仿真的组合 XOR RTL，对拍 Python golden vector；
- [`rtl/lba_mapper/`](rtl/lba_mapper/)：RAID0 LBA 映射组合 RTL、testbench 和一键 runner；
- [`sim/README.md`](sim/README.md)：跨模块仿真预留区说明；
- [`labs/level0_python_model/`](labs/level0_python_model/)：RAID0/1/5 Python golden model。

建议按这条小路线通关：

1. **Step 0：先看 RAID 基础**：打开 `docs/raid_basics.md`，知道多盘组队在取舍什么；
2. **Step 1：看 RAID0 映射**：打开 `docs/raid0_mapping.md`，理解 LBA 怎么落到具体硬盘；
3. **Step 2：看 RAID1 镜像**：打开 `docs/raid1_mirror.md`，理解为什么复制能换来故障切换；
4. **Step 3：看 RAID5 parity**：打开 `docs/raid5_parity.md`，理解 XOR 怎么提供单盘容错；
5. **Step 4：看 RAID5 write path**：打开 `docs/raid5_write_path.md`，区分 full-stripe write、RMW 和 reconstruct write；
6. **Step 5：看 write hole**：打开 `docs/write_hole.md`，理解 partial write 被打断后为什么会留下潜伏风险；
7. **Step 6：看 rebuild/scrub**：打开 `docs/rebuild_and_scrub.md`，理解潜伏 mismatch 什么时候被发现、如何上报；
8. **Step 7：跑可视化 demo**：观察 RAID0/1/5 的布局，并亲眼看到 write hole 如何潜伏到降级恢复时才爆；
9. **Step 8：对照源码看映射、镜像和校验**：打开 `labs/level0_python_model/raid_model.py`，找到 `RAID0.map_lba()`、`RAID1.write()`、`RAID1.read()`、`RAID5.layout_row()`、`RAID5.write_full_stripe()`；
10. **Step 9：看 FPGA 架构边界**：打开 `docs/fpga_architecture.md`，理解为什么先做 `xor_engine`、`lba_mapper`、`stripe_manager`；
11. **Step 10：跑 RTL XOR**：执行 `python rtl/xor_engine/run_tests.py`，用 Icarus Verilog 跑第一块可对拍小模块；
12. **Step 11：跑 RTL LBA mapper**：执行 `python rtl/lba_mapper/run_tests.py`，观察 RAID0 LBA 如何落到 disk 和 disk_lba；
13. **Step 12：跑 Python 测试**：确认模型行为没有坏。

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

其中 `python rtl/xor_engine/run_tests.py` 和 `python rtl/lba_mapper/run_tests.py` 是当前 RTL 关卡的一键入口：它们会生成/读取 golden vector、编译对应 RTL、运行 testbench，并覆盖少量参数化形状。若想手动拆开看 Icarus Verilog 命令，可以先从 XOR 这个最小模块开始：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
```

这条手动命令会在 `rtl/xor_engine/` 留下 `tb_xor_engine.vvp`。它只是 Icarus Verilog 编译产物，可以删除，也已被 `.gitignore` 忽略；若想保持目录清爽，优先使用上面的一键 runner。

当前策略：单个 RTL 模块的 runner 先放在模块目录，便于读者就地理解；等 RTL 模块继续增多后，再考虑把多模块总入口收敛到 `sim/run_all.py`。

## 仓库结构

```text
fpga-raid-lab/
├── docs/                 # 概念、架构、资料
├── labs/                 # 分关卡实验
├── rtl/                  # RTL 小模块
├── sim/                  # 仿真和 golden model
├── notes/                # 术语、问题、踩坑
└── roadmap/              # 里程碑
```

## 当前判断

公开资料里，完整可用的 FPGA RAID 控制器 RTL 很少。更现实的路线是：

```text
自己实现 RAID 层
复用/参考 SATA、PCIe、DMA、Reed-Solomon、GF 等开源或厂商 IP
控制逻辑参考 Linux MD RAID
```
