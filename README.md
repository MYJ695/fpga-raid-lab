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

## 先看这里：一眼通关顺序

如果你第一次打开这个仓库，不要从文件树里乱点。

按下面 4 段走就行：

```text
第 1 段：先看 7 篇文档，建立概念地图
第 2 段：再跑 3 个 Python demo，把 RAID 行为看见
第 3 段：再跑 1 个 pytest，确认模型没坏
第 4 段：最后跑 2 个 RTL runner，看硬件小模块怎么验证
```

你可以把它当成一个小游戏：

```text
先知道规则 → 再看动画 → 再做检查 → 最后看硬件实现
```

### 第 1 段：按顺序看文档

先只看这些文档。不要急着看 Python 和 RTL。

| 顺序 | 文件 | 你要搞懂的问题 |
|---:|---|---|
| 1 | [`docs/raid_basics.md`](docs/raid_basics.md) | RAID 到底想解决什么问题？容量、性能、可靠性怎么取舍？ |
| 2 | [`docs/raid0_mapping.md`](docs/raid0_mapping.md) | 一笔连续数据，为什么会被切到多块盘上？ |
| 3 | [`docs/raid1_mirror.md`](docs/raid1_mirror.md) | 为什么“复制一份”能让坏一块盘后继续读？ |
| 4 | [`docs/raid5_parity.md`](docs/raid5_parity.md) | XOR parity 为什么能在坏一块盘后把数据算回来？ |
| 5 | [`docs/raid5_write_path.md`](docs/raid5_write_path.md) | RAID5 写入为什么比读更麻烦？full-stripe、RMW、reconstruct write 分别是什么？ |
| 6 | [`docs/write_hole.md`](docs/write_hole.md) | 为什么写到一半断电，会留下 data/parity 不一致的坑？ |
| 7 | [`docs/rebuild_and_scrub.md`](docs/rebuild_and_scrub.md) | 坏盘重建和巡检 scrub 到底在检查什么？ |

看到这里，你只需要形成一个直觉：

```text
RAID 不是“几块盘绑一起”这么简单。
它真正难的地方，是映射、校验、故障、写入一致性和恢复。
```

### 第 2 段：跑 Python demo，把抽象规则看见

文档看完后，进入仓库根目录，依次执行：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
```

这 3 个脚本分别看这些东西：

| 顺序 | 命令 | 你会看到什么 |
|---:|---|---|
| 1 | `python labs/level0_python_model/demo_layout.py` | RAID0/1/5 的数据布局长什么样 |
| 2 | `python labs/level0_python_model/demo_write_hole.py` | write hole 怎么发生，为什么它是潜伏风险 |
| 3 | `python labs/level0_python_model/demo_rebuild_and_scrub.py` | rebuild/scrub 怎么把问题暴露出来 |

如果你只想先体验项目，跑完这 3 个 demo 就够了。

### 第 3 段：跑 Python 测试，确认模型是可信的

然后执行：

```bash
python -m pytest -q labs/level0_python_model
```

它的作用不是给初学者“增加负担”。

它是在告诉你：

```text
前面那些 Python demo 不是随手打印。
它们背后有一套可检查的 RAID 行为模型。
```

### 第 4 段：最后再看 RTL，不要一上来就看 Verilog

等你理解了 Python 模型，再进入 FPGA/RTL 部分。

先看这篇：

| 顺序 | 文件 | 你要搞懂的问题 |
|---:|---|---|
| 1 | [`docs/fpga_architecture.md`](docs/fpga_architecture.md) | 哪些 RAID 逻辑适合放进 FPGA？为什么先做小模块？ |
| 2 | [`rtl/README.md`](rtl/README.md) | RTL 目录怎么组织？每个 runner 是干什么的？ |

然后执行：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

这两个命令分别验证：

| 顺序 | 命令 | 它在验证什么 |
|---:|---|---|
| 1 | `python rtl/xor_engine/run_tests.py` | XOR parity 这个最小硬件积木是否正确 |
| 2 | `python rtl/lba_mapper/run_tests.py` | RAID0 的 LBA 映射能不能翻译成组合逻辑 |

如果这里能跑通，你就完成了第一轮通关：

```text
文档理解 → Python 行为模型 → 自动测试 → RTL 小模块仿真
```

## 你现在应该先做什么？

如果你不知道从哪里开始，只做这 5 件事：

```bash
# 1. 先读 README 这一节
# 2. 再读 docs/raid_basics.md
# 3. 再读 docs/raid0_mapping.md
# 4. 然后跑第一个 demo
python labs/level0_python_model/demo_layout.py

# 5. 最后回来继续读 docs/raid1_mirror.md
```

不要一开始就打开 `rtl/`。

也不要一开始就研究所有 Python 源码。

先建立直觉，再看实现。

## 项目定位

这是一个 **学习型 + 设计型 + 实验型** 仓库。

不是资料堆场，也不是论文复读机。

每个阶段都要留下可检查产出：

- 一页解释；
- 一个可运行模型；
- 一个 RTL 小模块或 testbench；
- 一条踩坑记录。

## 当前路线图

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
