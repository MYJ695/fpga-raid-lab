# Milestones - 里程碑

## Milestone 0：建地图

目标：把问题空间整理清楚。

产出：

- README
- big picture
- glossary
- references

状态：进行中。

## Milestone 1：Python RAID 小队

目标：不用 FPGA，先用 Python 把 RAID0/1/5 行为跑通。

产出：

- virtual disk model
- RAID0 mapping
- RAID1 mirror
- RAID5 full-stripe write
- degraded read

验收：

- 随机写入后读回一致；
- 模拟坏一块盘后 RAID5 能恢复读。

## Milestone 2：RTL 基础模块

目标：把最核心的硬件模块单独做出来。

产出：

- lba_mapper
- xor_engine
- simple stripe splitter
- testbench

验收：

- RTL 输出与 Python golden model 对齐。

## Milestone 3：RAID5 最小闭环

目标：用 RTL/仿真实现 RAID5 full-stripe write + read。

暂不做：

- partial write；
- write hole；
- 真实硬盘接口。

## Milestone 4：小写与一致性

目标：理解 RAID5 真正难点。

产出：

- read-modify-write
- reconstruct write
- stripe lock
- write hole 分析

## Milestone 5：真实接口调研

目标：决定接真实设备的路线。

候选：

- SATA HBA；
- PCIe DMA + 主机模拟盘；
- NVMe 由 CPU 管，FPGA 做数据面；
- DDR/BRAM 继续模拟。
