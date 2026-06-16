# 00 - 一张图看懂 FPGA RAID

## 核心结论

FPGA RAID 不是“写一个 XOR 模块”，而是做一个多盘存储小队的调度官。

它要回答四个问题：

1. 数据放哪块盘？
2. 多块盘怎么并行读写？
3. 坏一块盘怎么恢复？
4. 写到一半出事，怎么不把阵列搞坏？

## 整体视角

```text
Host / CPU
   |
   |  read/write command: LBA + length + buffer
   v
+-----------------------+
| FPGA RAID Controller  |
|                       |
| cmd_queue             |
| lba_mapper            |
| stripe_manager        |
| read/write_engine     |
| parity_engine         |
| rebuild_engine        |
+-----------------------+
   |        |        |
   v        v        v
Disk0    Disk1    Disk2 ...
```

## 几个角色

- **Host**：老板，只说“我要读/写 LBA”。
- **RAID Controller**：调度官，把逻辑地址拆成多盘动作。
- **Disk**：队员，负责保存自己的 chunk。
- **Parity**：侦探，某个队员失踪时帮忙还原数据。
- **Metadata**：账本，记录阵列状态、坏盘、重建进度。

## FPGA 值得做什么

适合硬件化：

- LBA 映射；
- 多通道数据搬运；
- XOR 校验；
- AXI-Stream 流水线；
- 简单读写状态机；
- 故障读重构。

不适合一开始全硬件化：

- 复杂元数据；
- 掉电恢复；
- 热插拔策略；
- 完整 NVMe/SATA 协议栈；
- 管理界面。

## 第一阶段边界

我们先不用真实硬盘。

用 Python/BRAM 模拟多块盘：

```text
virtual disk0 = bytearray()
virtual disk1 = bytearray()
virtual disk2 = bytearray()
virtual disk3 = bytearray()
```

先证明 RAID 算法和映射逻辑是对的，再考虑真实接口。
