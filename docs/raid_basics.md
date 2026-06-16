# RAID Basics - 多块盘为什么要组队？

## 核心结论

RAID 的本质不是“把硬盘变快”的魔法，而是把多块盘组织成一个有规则的小队，在 **容量、性能、可用性** 之间做取舍。

在 FPGA RAID 里，控制器最先要学会三件事：

1. **映射**：逻辑 LBA 应该落到哪块盘、哪个 chunk；
2. **冗余**：坏一块盘时，哪些数据还能读；
3. **恢复**：换新盘后，缺失块如何被重新算出来。

Level 0 的 Python 模型就是这三件事的“沙盘”。先在沙盘里看清规则，再把规则搬到 RTL。

## RAID 在解决什么问题

| 目标 | 直觉说法 | 代价 |
|---|---|---|
| 容量 | 多块盘拼成更大的逻辑空间 | 需要映射规则 |
| 性能 | 多块盘并行读写不同 chunk | 请求会被切分和调度 |
| 可用性 | 坏一块盘时仍能读数据 | 需要镜像或校验，写路径更复杂 |

一个好的 RAID 教学项目不应该只说“RAID5 有校验”，而要回答：

```text
Host 说：我要读 LBA 5
Controller 问：LBA 5 在哪块盘？如果那块盘坏了，用谁把它算回来？
```

## RAID0 / RAID1 / RAID5 一句话对比

| RAID | 它像什么 | 优点 | 代价 | Level 0 对应实验 |
|---|---|---|---|---|
| RAID0 | 把数据轮流发给多个队员 | 容量利用率高，容易并行 | 任意成员盘坏了，部分数据就丢 | `RAID0` 条带映射与坏盘测试 |
| RAID1 | 每个数据复制给镜像队员 | 单盘坏了还能读 | 容量成本高，写入要复制 | `RAID1` 双盘镜像与降级读 |
| RAID5 | 数据 + 轮转 XOR 侦探 | 单盘故障可恢复，容量比镜像省 | 写路径复杂，partial write 会引出 write hole | `RAID5` full-stripe write、degraded read、rebuild |

## 三个最小概念

### 1. Chunk：RAID 的积木块

RAID 不会把“一个文件”直接丢给某块盘。它先把逻辑空间切成固定大小的 chunk，再决定每个 chunk 放到哪里。

在 Level 0 里，一个 block 默认只有 4 bytes，比如：

```python
b"A000"
b"B111"
```

这不真实，但很适合看清映射。

### 2. Stripe：一排队员共同完成的一组 chunk

RAID0 的一个 stripe 可能长这样：

```text
stripe 0: disk0=D0  disk1=D1  disk2=D2
stripe 1: disk0=D3  disk1=D4  disk2=D5
```

RAID5 会把其中一个位置留给 parity：

```text
stripe 0: disk0=P   disk1=D0  disk2=D1  disk3=D2
stripe 1: disk0=D3  disk1=P   disk2=D4  disk3=D5
```

Parity 轮转的目的，是避免某一块盘永远承担校验写入压力。

### 3. XOR parity：丢一块，还能拼回来

XOR 有一个很适合 RAID5 的性质：

```text
P = A xor B xor C
A = P xor B xor C
B = P xor A xor C
C = P xor A xor B
```

也就是说，只要一个 stripe 里只丢了一个块，就可以用剩下的块把它算回来。

这也是为什么 Level 0 的 RAID5 只承诺“单盘降级读取”和“单盘重建”：同时坏两块盘时，信息不够了。

## FPGA 视角：这些概念会变成什么模块？

| RAID 概念 | FPGA/RTL 里的影子 |
|---|---|
| LBA 到 disk/chunk 的映射 | `lba_mapper` |
| 把一次读写切成多个成员盘动作 | `stripe_manager` |
| XOR parity 计算 | `xor_engine` |
| 坏盘后用剩余块重构读取 | degraded read datapath |
| 换新盘后逐 stripe 补数据 | rebuild engine |

所以，Level 0 不是“玩具代码”而已。它是后续 RTL 小模块的 golden model。

## 下一步怎么跑

先看布局，再跑测试：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

如果想看代码，从这里开始：

- [`../labs/level0_python_model/README.md`](../labs/level0_python_model/README.md)
- [`../labs/level0_python_model/raid_model.py`](../labs/level0_python_model/raid_model.py)
- [`../labs/level0_python_model/test_raid_model.py`](../labs/level0_python_model/test_raid_model.py)

## 当前边界

这一页只讲 RAID0/1/5 的入门直觉，不覆盖：

- RAID6 的 P/Q parity；
- partial write、read-modify-write、reconstruct write；
- write hole 与掉电一致性；
- 真实 SATA/NVMe/PCIe 接口；
- Linux MD RAID 的完整元数据和恢复策略。

这些会在后续关卡逐步补上。

---

## 继续阅读

👉 [下一篇：RAID0 映射](raid0_mapping.md)
