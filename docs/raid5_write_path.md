# RAID5 Write Path - 真正麻烦的是“小写”

## 核心结论

RAID5 写入分三种路径：

| 写路径 | 适合场景 | 需要读旧数据吗？ | 直觉 |
|---|---|---|---|
| full-stripe write | 一次写满整个 stripe 的所有 data block | 不需要 | 新数据直接 XOR 出新 parity |
| read-modify-write | 只改少数 data block | 需要读 old data + old parity | 用“变化量 delta”修补 parity |
| reconstruct write | 改较多但没写满 stripe | 需要读没被改的其他 data block | 拼出完整新 stripe，再 XOR 出新 parity |

一句话：**RAID5 不怕算 XOR，怕的是 partial write 时 parity 必须和数据一起保持一致**。

上一页 `raid5_parity.md` 讲的是“XOR 为什么能恢复一块坏盘”。本页讲写入控制器真正要面对的问题：主机只写一个小块时，RAID5 不能只改数据块，还必须把 parity 改对。

## 先固定一个 4 盘 stripe

假设 4 块盘，stripe 0 的 parity 在 `disk0`：

| disk0 | disk1 | disk2 | disk3 |
|---|---|---|---|
| P | D0 | D1 | D2 |

parity 定义是：

```text
P = D0 XOR D1 XOR D2
```

如果写满整个 stripe，事情很简单；如果只改 `D1`，麻烦就来了。

## 路径 1：full-stripe write

主机一次给出完整 data stripe：

```text
new_D0, new_D1, new_D2
```

控制器直接做：

```text
new_P = new_D0 XOR new_D1 XOR new_D2
write disk1 <- new_D0
write disk2 <- new_D1
write disk3 <- new_D2
write disk0 <- new_P
```

这就是当前 Python 模型里的 `RAID5.write_full_stripe()`：

```text
1. data_disk_order(stripe) 找到 D0/D1/D2 应该写到哪些盘；
2. xor_blocks(data_blocks) 算出 parity；
3. 数据块和 parity 块写到对应成员盘。
```

这个路径最像 RAID0 加一个 XOR engine：收齐数据，算 parity，扇出写盘。

## 路径 2：read-modify-write

现在主机只改 `D1`：

```text
old stripe: D0, old_D1, D2, old_P
new write :      new_D1
```

不能只写 `new_D1`，因为 `P = D0 XOR D1 XOR D2` 里的 D1 变了，P 也必须变。

read-modify-write 的关键公式是：

```text
new_P = old_P XOR old_D1 XOR new_D1
```

如果一次 partial write 同时改多个 data block，就把每个被修改块的 old/new 都 XOR 进去：

```text
new_P = old_P
        XOR old_Di XOR new_Di
        XOR old_Dj XOR new_Dj
        ...
```

为什么成立？

```text
old_P = D0 XOR old_D1 XOR D2
new_P = D0 XOR new_D1 XOR D2

old_P XOR old_D1 XOR new_D1
= D0 XOR old_D1 XOR D2 XOR old_D1 XOR new_D1
= D0 XOR D2 XOR new_D1
= new_P
```

因为同一个值 XOR 两次会抵消：

```text
old_D1 XOR old_D1 = 0
x XOR 0 = x
```

所以 RMW 只需要读两个旧块：

```text
read old_D1
read old_P
new_P = old_P XOR old_D1 XOR new_D1
write new_D1
write new_P
```

### RMW 的硬件味道

| 动作 | FPGA 里的模块影子 |
|---|---|
| 找到 D1 和 P 的成员盘 | LBA mapper |
| 同时读 old data / old parity | read scheduler |
| 计算 `old_P XOR old_D1 XOR new_D1` | XOR engine |
| 写 new data / new parity | write scheduler |

它适合“小改动”：比如一个 stripe 有 7 个 data block，但主机只改 1 个。

## 路径 3：reconstruct write

如果主机改的不是 1 个块，而是很多块，但还没写满 stripe，RMW 未必划算。

还是 4 盘 stripe：

```text
old stripe: old_D0, old_D1, old_D2, old_P
new write : new_D0, new_D1
```

RMW 做法会读：

```text
old_D0, old_D1, old_P
```

然后分别把两个变化修到 parity 上。

reconstruct write 换个想法：既然新 `D0` 和新 `D1` 已经有了，只要再读没被改的 `old_D2`，就能拼出完整的新 data stripe：

```text
new_P = new_D0 XOR new_D1 XOR old_D2
```

也就是：

```text
read old_D2
new_P = XOR(所有新数据块 + 没被改的旧数据块)
write new_D0
write new_D1
write new_P
```

它适合“改得比较多”的 partial stripe。读旧 parity 反而不是必须的，因为可以重新构造整个 stripe 的 parity。

## RMW 和 reconstruct 怎么选？

假设一个 stripe 有 `N` 个 data block，本次要写 `W` 个 data block。

| 路径 | 需要读什么 | 读数量直觉 |
|---|---|---|
| read-modify-write | W 个 old data + 1 个 old parity | W + 1 |
| reconstruct write | N-W 个未改 data | N - W |

简单选择规则：

```text
if W + 1 <= N - W:
    用 read-modify-write
else:
    用 reconstruct write
```

这只是教学级直觉。真实控制器还会考虑并发、缓存命中、盘队列、写合并、故障状态、flush/FUA、bitmap/journal 等因素。

## 最小手算例子

给定：

```text
old_D0 = 0xaa
old_D1 = 0xcc
old_P  = old_D0 XOR old_D1 = 0x66
new_D1 = 0x0f
```

只改 `D1`，RMW 算：

```text
new_P = old_P XOR old_D1 XOR new_D1
      = 0x66 XOR 0xcc XOR 0x0f
      = 0xa5
```

检查完整公式：

```text
old_D0 XOR new_D1 = 0xaa XOR 0x0f = 0xa5
```

两边一致。

## write hole：为什么下一关很重要？

partial write 至少要写两个地方：

```text
new data block
new parity block
```

如果只写完 data，掉电了，parity 还是旧的；如果只写完 parity，掉电了，data 还是旧的。这样阵列看起来每块盘都“没坏”，但同一个 stripe 内的数据和 parity 已经对不上。

这就是 RAID5 经典的 **write hole** 直觉：

```text
数据写了一半 + parity 写了一半 + 掉电/复位/超时
=> stripe 内部不再自洽
=> 未来坏一块盘时，XOR 可能恢复出错误数据
```

所以真实 RAID5 控制器不能只会 XOR，还要处理写入原子性和恢复策略。常见方向包括：

- 写日志或 journal；
- bitmap 标记哪些 stripe 可能不干净；
- PPL / partial parity log 一类技术；
- 使用带掉电保护的缓存；
- 定期 scrub，尽早发现 parity 不一致。

这些不在本页展开，下一关 [`write_hole.md`](write_hole.md) 再专门拆。

## 对 FPGA 来说意味着什么？

| RAID5 写路径问题 | FPGA 里的影子 |
|---|---|
| 判断 full stripe / partial stripe | request coalescer / stripe buffer |
| 选择 RMW 或 reconstruct | write path controller |
| 读 old data / old parity | multi-disk read scheduler |
| XOR 计算 delta 或完整 parity | XOR engine / pipeline |
| data 和 parity 写入顺序 | write scheduler + completion tracking |
| 掉电或复位中断 | metadata / journal / recovery state machine |

在 FPGA 里，RAID5 write path 不是一个“XOR 模块”就结束，而是一条小流水线：

```text
host write request
    -> LBA mapper
    -> stripe buffer / coalescer
    -> choose full-stripe / RMW / reconstruct
    -> schedule reads if needed
    -> XOR engine
    -> schedule data + parity writes
    -> completion / recovery metadata
```

## 手算小练习

1. 一个 6 盘 RAID5 stripe 有几个 data block？
2. 6 盘 RAID5 中，一次 partial write 改 1 个 data block，RMW 和 reconstruct 分别要读几个旧块？
3. 6 盘 RAID5 中，一次 partial write 改 4 个 data block，RMW 和 reconstruct 分别要读几个旧块？
4. `old_P=0x66, old_D1=0xcc, new_D1=0x0f`，RMW 得到的 `new_P` 是多少？
5. 为什么 data 和 parity 分两次写会引出 write hole？

参考答案：

1. 5 个 data block；
2. RMW 读 `1+1=2` 个旧块，reconstruct 读 `5-1=4` 个旧 data block，所以 RMW 更少；
3. RMW 读 `4+1=5` 个旧块，reconstruct 读 `5-4=1` 个旧 data block，所以 reconstruct 更少；
4. `0x66 XOR 0xcc XOR 0x0f = 0xa5`；
5. 因为 data 和 parity 必须表达同一个 stripe 状态，掉电打断后可能一个新一个旧，阵列表面健康但 parity 已经不可信。

## 动手检查

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

当前 Python 模型只实现 `write_full_stripe()`，没有实现 partial write。这样设计是刻意的：先把 RAID5 parity 的正确性跑通，再单独学习 RMW、reconstruct write 和 write hole。

---

## 继续阅读

👉 [下一篇：Write Hole](write_hole.md)
