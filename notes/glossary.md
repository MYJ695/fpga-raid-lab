# Glossary - 术语小抄

## 固存 / Solid-State Recorder

星载固态存储系统。可以理解成卫星上负责接收、保存、回放载荷数据的高速数据仓库。

## 载荷数据流

来自相机、雷达或其他载荷的连续数据。技术要求里抽象为 8 路输入数据流。

## FPGA

现场可编程门阵列。本项目里把它理解成高速数据调度员：接收数据、做 RAID 映射/校验、连接 SSD 控制逻辑。

## NVMe SSD

基于 NVMe 协议的固态硬盘。NVMe 比传统 SATA 更适合高并发、高吞吐场景，但 Host 侧实现复杂。

## PCIe Gen3 x4

常见 NVMe SSD 的高速总线形态。Gen3 x4 理论带宽很高，但实际系统还受协议、队列、缓存和 FPGA 资源限制。

## NVMe Host

主动控制 NVMe SSD 的一侧，负责初始化控制器、管理队列、提交读写命令、读取状态和健康信息。它本身是独立大工程。

## AXIS / AXI-Stream

适合数据流传输的接口。可以理解成“传送带”：`valid` 表示我有货，`ready` 表示你能收货。

## AXI-Lite

适合低速寄存器访问的接口。可以理解成“控制台”：配置模式、读状态、清告警、做错误注入。

## RAID

Redundant Array of Independent Disks。把多块盘组织成一个逻辑盘。

## LBA

Logical Block Address。主机看到的逻辑块地址。

## Chunk

一个条带单元。比如 64KB 数据放在某一块盘上。

## Stripe

一组 chunk。RAID 的基本组织单位。

## Parity

校验块。RAID5 里通常是 XOR 校验。

## RAID0

条带化。把连续数据轮流写到多块盘，提高吞吐和容量利用率，但坏一块盘就会丢失映射到该盘的数据。

## RAID1

镜像。每份数据写到两块盘，坏一块仍能读，但容量利用率低。

## RAID5

分布式校验。数据和 parity 分散在多块盘上，任意一块盘故障时可用其他盘和 parity 重构。

## Full-stripe write

一次写满整个 stripe，可以直接计算新校验。

## Partial write

只写 stripe 的一部分。RAID5 中会触发 read-modify-write 或 reconstruct write。

## Read-Modify-Write

RAID5 小写常用流程：

```text
new_parity = old_parity XOR old_data XOR new_data
```

## Write Hole

数据和校验没有原子更新，掉电后可能不一致。

## Degraded Mode

阵列坏了一块盘，但仍然能靠校验继续工作。

## Rebuild

换新盘后，根据其他盘和校验恢复缺失数据。

## Scrub

后台巡检，检查数据和校验是否一致。

## 错误注入

人为制造掉盘、超时、校验不一致等故障，让测试过程可复现。工程样机验收和联调通常需要它。

## 遥测 / Telemetry

系统状态数据，例如温度、错误计数、SSD 健康、阵列模式、重建进度。它让系统“看得见”。
