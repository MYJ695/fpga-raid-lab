# FPGA RAID 网页学习目录

> 如果你主要是在网页上看教程，就从这里开始。先不用 clone 仓库，也不用急着跑 Python。

## 怎么读最省力

1. 从第 1 篇点进去；
2. 每篇先看“核心结论”，不要一开始就钻所有细节；
3. 读到末尾后，用“上一篇 / 回目录 / 下一篇”继续导航；
4. 如果术语看不懂，先回到 [`notes/glossary.md`](../notes/glossary.md)。

## 推荐阅读顺序

| 顺序 | 文档 | 大概用时 | 看完要能说清 |
|---:|---|---:|---|
| 1 | [需求对齐](requirements_alignment.md) | 10 min | 工程文档到底要求什么？本教程覆盖哪些前期知识？ |
| 2 | [验收清单](acceptance_checklist.md) | 8 min | 哪些内容是教程自测，哪些还需要后续工程证据？ |
| 3 | [费曼学习路线](feynman_learning_path.md) | 10 min | 怎样把复杂系统讲成新人能听懂的故事？ |
| 4 | [学习计划](study_plan.md) | 8 min | 20/60/120 分钟分别应该看什么、跳过什么？ |
| 5 | [系统大图](00_big_picture.md) | 12 min | 8 路数据、FPGA、RAID、NVMe SSD 如何连成一张图？ |
| 6 | [工作模式](working_modes.md) | 10 min | 自检、待机、记录、回放、边记边放如何组成状态机？ |
| 7 | [AXIS / AXI-Lite 基础](axis_axi_lite_basics.md) | 12 min | 数据面和控制面分别管什么？ |
| 8 | [控制寄存器](control_plane_registers.md) | 10 min | 软件如何配置阵列、读状态、注入错误、看重建进度？ |
| 9 | [NVMe Host 方案](nvme_host_options.md) | 10 min | 为什么真实 NVMe Host 是独立大工程？第一阶段为什么先抽象？ |
| 10 | [RAID 基础](raid_basics.md) | 10 min | RAID 在容量、性能、可靠性之间做什么取舍？ |
| 11 | [RAID0 映射](raid0_mapping.md) | 10 min | 连续数据为什么会被切到多块盘上？ |
| 12 | [RAID1 镜像](raid1_mirror.md) | 8 min | 复制一份为什么能支持坏一块盘后继续读？ |
| 13 | [RAID5 校验](raid5_parity.md) | 12 min | XOR parity 为什么能恢复单盘缺失数据？ |
| 14 | [RAID5 写路径](raid5_write_path.md) | 12 min | RAID5 写入为什么比读取更麻烦？ |
| 15 | [Write Hole](write_hole.md) | 10 min | 写到一半断电为什么会留下 data/parity 不一致？ |
| 16 | [Rebuild 和 Scrub](rebuild_and_scrub.md) | 10 min | 坏盘重建和巡检 scrub 到底在检查什么？ |

## 读到什么程度就可以先停？

如果你现在只是做前期调研，先别追求把所有细节吃透。能达到下面这个程度，就可以先往后走：
```text
能用自己的话解释：
8 路数据为什么需要 FPGA 调度，
RAID0/1/5 分别解决什么问题，
AXIS 数据面和 AXI-Lite 控制面为什么要分开，
NVMe Host 为什么不是教程第一阶段要硬写的东西。
```

## 开始

先点这一篇：👉 [第 1 篇：需求对齐](requirements_alignment.md)
