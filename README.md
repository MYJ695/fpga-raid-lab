# FPGA RAID Lab

> 把“星载 NVMe SSD 阵列固存工程样机”拆成一条能学、能跑、能继续扩展的路线。

## 一句话目标

本仓库用于做 **基于 NVMe SSD 阵列的星载固存样机** 的前期调研和基础知识补课。

它不直接交付完整工程样机，也不一上来写完整 NVMe Host 或 FPGA RAID 控制器；它先回答更基础的问题：

1. 工程文档到底要求什么系统？
2. RAID0/1/5 分别解决什么问题？
3. FPGA 里哪些逻辑适合先做成小模块？
4. 从 Python 行为模型到 RTL 仿真，如何一步步验证？

## 项目定位

这是一个 **学习型 + 调研型 + 小实验型** 仓库。

边界很重要：

- 做：需求拆解、RAID/NVMe/AXI 基础解释、Python demo、小 RTL 实验；
- 不做：完整 NVMe Host、8 路高速 AXIS 数据面、板级时序收敛、掉电保护、72 小时稳定性验收。

你可以把它理解成工程样机之前的“地图课”和“热身实验”。

## 背景：技术要求在说什么

最新文档是 `D:\work\2601s\raid\固存样机技术要求.docx`。它描述的目标可以简化成：

```text
8 路载荷数据流
    -> FPGA 数据接入、流控、RAID 管理
    -> 不少于 4/6 块 NVMe SSD
    -> 支持 RAID0 / RAID1 / RAID5
    -> 可监控、可故障注入、可重建、可验收
```

几项关键要求：

| 类别 | 文档要求里的关键词 | 本仓库怎么处理 |
|---|---|---|
| 存储设备 | NVMe SSD、PCIe Gen3 x4、NVMe 1.2/1.3 | 先做概念地图，不实现协议栈 |
| 数据输入 | 8 路输入，AXIS 64-bit，valid/ready | 先解释数据面与背压，暂不写完整汇聚器 |
| RAID | RAID0/1/5、条带大小、成员盘映射、重建 | Python 模型 + 文档 + 小 RTL 积木 |
| 控制管理 | AXI-Lite、状态、错误计数、重建进度 | 先列为控制面学习主题 |
| 验收 | 功能、性能、稳定性、异常恢复、资料一致 | 先解释验收含义，不冒充工程交付 |

详细对齐见：[`docs/requirements_alignment.md`](docs/requirements_alignment.md)。

## 先看这里：一眼通关顺序

如果你第一次打开这个仓库，不要从文件树里乱点。

按下面 4 段走就行：

```text
第 1 段：先看工程需求和费曼路线，知道为什么学
第 2 段：再看 RAID 基础文档，建立概念地图
第 3 段：跑 Python demo，把 RAID 行为看见
第 4 段：跑 RTL runner，理解最小硬件积木怎么验证
```

### 第 1 段：先建立工程背景

| 顺序 | 文件 | 你要搞懂的问题 |
|---:|---|---|
| 1 | [`docs/requirements_alignment.md`](docs/requirements_alignment.md) | 技术要求到底要什么？哪些是本仓库能覆盖的前期知识？ |
| 2 | [`docs/feynman_learning_path.md`](docs/feynman_learning_path.md) | 如果把系统讲给新人听，应该怎么讲？ |
| 3 | [`docs/00_big_picture.md`](docs/00_big_picture.md) | FPGA RAID/NVMe 固存的整体框架是什么？ |

### 第 2 段：按顺序看 RAID 文档

| 顺序 | 文件 | 你要搞懂的问题 |
|---:|---|---|
| 4 | [`docs/raid_basics.md`](docs/raid_basics.md) | RAID 到底想解决什么问题？容量、性能、可靠性怎么取舍？ |
| 5 | [`docs/raid0_mapping.md`](docs/raid0_mapping.md) | 一笔连续数据，为什么会被切到多块盘上？ |
| 6 | [`docs/raid1_mirror.md`](docs/raid1_mirror.md) | 为什么“复制一份”能让坏一块盘后继续读？ |
| 7 | [`docs/raid5_parity.md`](docs/raid5_parity.md) | XOR parity 为什么能在坏一块盘后把数据算回来？ |
| 8 | [`docs/raid5_write_path.md`](docs/raid5_write_path.md) | RAID5 写入为什么比读更麻烦？ |
| 9 | [`docs/write_hole.md`](docs/write_hole.md) | 为什么写到一半断电，会留下 data/parity 不一致的坑？ |
| 10 | [`docs/rebuild_and_scrub.md`](docs/rebuild_and_scrub.md) | 坏盘重建和巡检 scrub 到底在检查什么？ |

看到这里，你只需要形成一个直觉：

```text
工程样机难点 = 高速数据流 + 多盘调度 + 校验恢复 + 状态控制 + 可验证交付。
RAID 是核心之一，但不是全部。
```

### 第 3 段：跑 Python demo，把抽象规则看见

在仓库根目录执行：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```

这些 demo 的目的不是教你写大工程，而是让你亲眼看到：

- LBA 如何落到不同盘；
- RAID5 parity 如何保护单盘故障；
- write hole 为什么危险；
- scrub/rebuild 为什么是工程样机验收会关心的能力。

### 第 4 段：跑 RTL 小模块

如果你已经理解 Python 行为，再执行：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

这两个命令分别验证：

| 顺序 | 命令 | 它在验证什么 |
|---:|---|---|
| 1 | `python rtl/xor_engine/run_tests.py` | XOR parity 这个最小硬件积木是否正确 |
| 2 | `python rtl/lba_mapper/run_tests.py` | RAID0 的 LBA 映射能不能翻译成组合逻辑 |

如果本机没有 Icarus Verilog，runner 会提示缺少 `iverilog`。这不是教程失败，而是外部仿真工具未安装。

## 当前路线图

| Level | 主题 | 核心问题 | 产出 |
|---|---|---|---|
| 0 | 工程需求地图 | 固存样机到底要解决什么？ | 需求对齐 + 费曼学习路径 |
| 1 | RAID 世界观 | 多块盘为什么要组队？ | Python 虚拟磁盘模型 |
| 2 | RAID0/1/5 | 条带、镜像、校验怎么工作？ | 文档 + demo + pytest |
| 3 | 小写与维护 | partial write、write hole、rebuild 为什么难？ | 故障演示 + scrub/rebuild 解释 |
| 4 | RTL 最小积木 | 哪些 RAID 逻辑适合硬件化？ | xor_engine、lba_mapper |
| 5 | 工程接口调研 | AXIS/AXI-Lite/NVMe/PCIe 怎么接入地图？ | 架构说明和后续调研清单 |

## 仓库结构

```text
fpga-raid-lab/
├── docs/                 # 概念、架构、需求对齐、资料
├── labs/                 # Python 小实验
├── rtl/                  # RTL 小模块
├── sim/                  # 跨模块仿真预留区
├── notes/                # 术语、问题、踩坑
└── roadmap/              # 里程碑
```

## 当前判断

公开资料里，完整可用的 FPGA RAID + NVMe SSD 阵列工程 RTL 很少。更现实的路线是：

```text
自己实现/验证 RAID 层核心逻辑
复用或采购 NVMe/PCIe 等复杂接口 IP
用 Python golden model + RTL testbench 做早期闭环
把控制寄存器、状态遥测、错误注入纳入架构设计
```

本仓库先把这些判断变成可学习、可验证的材料。
