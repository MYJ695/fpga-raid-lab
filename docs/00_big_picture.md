# 00 - 一张图看懂星载 NVMe RAID 固存

## 先抓住这句话

这套系统不是“写一个 XOR 模块”，而是让 FPGA 做一个高速数据仓库的调度员：
```text
多路载荷数据进来，要被分流、排队、校验、写入多块 NVMe SSD；
同时还要能监控状态、处理掉盘、控制重建、支持验收测试。
```

## 整体视角
```text
8x Payload Streams
AXIS 64-bit, valid/ready
        |
        v
+-----------------------------+
| FPGA Solid-State Recorder   |
|                             |
| Data Plane                  |
|  - stream ingress           |
|  - buffering / arbitration  |
|  - lba/stripe mapper        |
|  - raid read/write engine   |
|  - xor/parity engine        |
|  - rebuild/scrub datapath   |
|                             |
| Control Plane               |
|  - AXI-Lite registers       |
|  - mode/config/status       |
|  - error injection          |
|  - telemetry/counters       |
+-----------------------------+
        |
        v
+-----------------------------+
| NVMe Host / PCIe subsystem  |
+-----------------------------+
        |
        v
SSD0  SSD1  SSD2  SSD3  SSD4  SSD5 ...
```

## 用费曼法解释

把它想成仓库：

- **8 路输入流**：8 条传送带同时送箱子；
- **FPGA**：仓库调度员，决定箱子放到哪个货架；
- **RAID0**：轮流放，速度快，但坏一个货架就缺货；
- **RAID1**：每箱放两份，可靠但占空间；
- **RAID5**：多数箱子正常放，再放一份“校验线索”，坏一个货架还能推理回来；
- **AXI-Lite 寄存器**：仓库看板和控制台；
- **NVMe Host**：真正和 SSD 货架对话的叉车系统。

## 四个层次

### 1. 数据面

回答：数据怎么高速流动？

关键词：AXIS、valid/ready、帧边界、字节有效、缓存、仲裁、背压、吞吐统计。

### 2. RAID 面

回答：数据怎么分到多块盘，坏盘后怎么读？

关键词：LBA 映射、chunk、stripe、RAID0/1/5、parity、degraded read、rebuild、scrub。

### 3. 控制面

回答：系统怎么配置、监控、定位问题？

关键词：AXI-Lite、阵列模式、成员盘状态、错误计数、重建进度、关键告警、错误注入。

### 4. 设备面

回答：FPGA 怎么和真实 SSD 对话？

关键词：NVMe 1.2/1.3、PCIe Gen3 x4、namespace、admin command、I/O queue、SMART/health log。

这个仓库第一阶段重点在 **RAID 面 + 少量数据面/控制面概念**。NVMe Host 是后面独立大课题。

## FPGA 值得先做什么

适合早期硬件化小实验：

- LBA 到 disk/chunk 的映射；
- RAID5 XOR parity；
- full-stripe write 的动作拆分；
- valid/ready 级别的小握手；
- 状态计数器、错误注入开关的寄存器概念；
- 简化的 rebuild/scrub 数据路径。

不适合一开始全硬件化：

- 完整 NVMe Host 协议栈；
- PCIe 复杂事务层；
- 真实 8 路 40Gbps 数据面；
- 掉电保护和完整元数据日志；
- 板级热设计、时序收敛和 72 小时稳定性。

## 第一阶段边界

我们先不用真实 SSD。

用 Python/BRAM/仿真模型代表多块盘：
```text
virtual disk0 = bytearray()
virtual disk1 = bytearray()
virtual disk2 = bytearray()
virtual disk3 = bytearray()
```

先证明 RAID 算法和映射逻辑是对的，再逐步讨论 AXIS、AXI-Lite、NVMe 和板级工程。

---

## 继续阅读

⬅️ [上一篇：学习计划](study_plan.md)<br>
🏠 [回到课程目录](index.md)<br>
➡️ [下一篇：工作模式](working_modes.md)
