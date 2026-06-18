# RAID5 Write Hole - 最危险的是“看起来没坏”

## 先抓住这句话

RAID5 的 write hole 不是“XOR 算错了”，而是：**partial write 需要分别写 data 和 parity，只要中途掉电、复位或控制器失联，就可能留下一个 data/parity 不一致的 stripe**。

最麻烦的地方在于：

1. 正常读那个被写过的数据块，可能还能读到“看起来正确”的新数据；
2. parity 却可能已经不再匹配这个 stripe；
3. 等到将来某块盘坏了，degraded read 或 rebuild 依赖 parity 恢复数据时，错误才爆出来。

一句话记住：**write hole 是 RAID5 partial write 的一致性窗口，不是每次 partial write 必然损坏。**

上一关 `raid5_write_path.md` 讲了 RMW / reconstruct write 为什么要同时改 data 和 parity。本页只盯住一个问题：如果这两个写入没有一起完成，会发生什么？

## 固定一个小 stripe

还是用 4 盘 RAID5，stripe 0 的 parity 在 `disk0`：

| disk0 | disk1 | disk2 | disk3 |
|---|---|---|---|
| P | D0 | D1 | D2 |

旧状态：
```text
D0 = 0xaa
D1 = 0xcc
D2 = 0x00
P  = D0 XOR D1 XOR D2 = 0x66
```

现在主机只想把 `D1` 从 `0xcc` 改成 `0x0f`。

正确的新 parity 应该是：
```text
new_P = D0 XOR new_D1 XOR D2
      = 0xaa XOR 0x0f XOR 0x00
      = 0xa5
```

也可以用 RMW delta 算：
```text
new_P = old_P XOR old_D1 XOR new_D1
      = 0x66 XOR 0xcc XOR 0x0f
      = 0xa5
```

理想完成后，stripe 应该变成：

| 块 | 值 | 状态 |
|---|---:|---|
| D0 | 0xaa | unchanged |
| D1 | 0x0f | new |
| D2 | 0x00 | unchanged |
| P | 0xa5 | matches new data |

## 坑 1：data 新了，parity 还是旧的

这一坑的状态可以直译成：**data 已写新值、parity 仍是旧值**。

假设控制器先写 data，再写 parity：
```text
write D1 <- 0x0f   # 成功
write P  <- 0xa5   # 还没写，掉电了
```

掉电后磁盘上的状态是：

| 块 | 实际值 | 应该是谁 | 问题 |
|---|---:|---|---|
| D0 | 0xaa | old/new 都一样 | 没问题 |
| D1 | 0x0f | new data | 看起来写成功 |
| D2 | 0x00 | old/new 都一样 | 没问题 |
| P | 0x66 | old parity | 已经不匹配新 data |

这时正常读 `D1`，会读到 `0x0f`，用户可能觉得写入成功了。

但如果之后 `disk1` 坏了，系统要用 `D0 XOR D2 XOR P` 恢复 D1：
```text
recovered_D1 = D0 XOR D2 XOR P
             = 0xaa XOR 0x00 XOR 0x66
             = 0xcc
```

恢复出来的是旧值 `0xcc`，不是新值 `0x0f`。

这就是 write hole 的典型恶心点：**坏的不是当下那次正常读，而是未来依赖 parity 的恢复路径。**

## 坑 2：parity 新了，data 还是旧的

这一坑的状态可以直译成：**parity 已写新值、data 仍是旧值**。

再反过来，假设控制器先写 parity，再写 data：
```text
write P  <- 0xa5   # 成功
write D1 <- 0x0f   # 还没写，掉电了
```

掉电后磁盘上的状态是：

| 块 | 实际值 | 应该是谁 | 问题 |
|---|---:|---|---|
| D0 | 0xaa | old/new 都一样 | 没问题 |
| D1 | 0xcc | old data | 数据没有更新 |
| D2 | 0x00 | old/new 都一样 | 没问题 |
| P | 0xa5 | new parity | 已经不匹配旧 data |

这时正常读 `D1`，会读到旧值 `0xcc`。如果上层文件系统或应用以为写入已经完成，就会出一致性问题。

如果之后 `disk1` 坏了，系统用 parity 恢复 D1：
```text
recovered_D1 = D0 XOR D2 XOR P
             = 0xaa XOR 0x00 XOR 0xa5
             = 0x0f
```

恢复出来的是新值 `0x0f`，但磁盘上原本留下的是旧数据 `0xcc`。这说明 stripe 已经没有一个清晰的“同一时刻状态”。

## 两种坏法放在一起看

| 中断位置 | 磁盘上 D1 | 磁盘上 P | 正常读 D1 | 未来用 parity 恢复 D1 | 直觉 |
|---|---:|---:|---:|---:|---|
| data 写完，parity 未写 | 0x0f | 0x66 | 0x0f | 0xcc | 现在看似成功，坏盘后回到旧值 |
| parity 写完，data 未写 | 0xcc | 0xa5 | 0xcc | 0x0f | data/parity 像来自两个时间线 |
| data 和 parity 都写完 | 0x0f | 0xa5 | 0x0f | 0x0f | 正常 |
| data 和 parity 都没写 | 0xcc | 0x66 | 0xcc | 0xcc | 仍是旧状态 |

所以 write hole 的本质不是“谁先写更好”。只要 data/parity 不是原子地一起提交，就有窗口。

## 为什么 full-stripe write 也要小心？

full-stripe write 不需要读旧 data/parity，但它仍然会写多个 data block 和一个 parity block。只要这些成员盘写入不能被当作一个原子事务，就仍然需要考虑掉电恢复。

不过 partial write 更容易暴露这个问题，因为它必须先基于旧状态算新 parity：
```text
读 old data / old parity
算 new parity
写 new data / new parity
```

读、算、写之间隔得越远，一致性窗口越明显。

## 为什么正常运行时不一定马上发现？

因为 RAID5 正常读一个没有故障的数据块时，通常直接读对应 data disk，不会每次都重新 XOR parity 验算。

也就是说：
```text
normal read D1 -> read disk2/blockX
```

而不是：
```text
normal read D1 -> read D0, D2, P -> XOR check
```

这样做是为了性能。代价是：parity mismatch 可能潜伏很久，直到：

- 某块盘故障，进入 degraded read；
- 换盘后开始 rebuild；
- 后台 scrub / check 终于扫到这个 stripe。

## FPGA 视角：这不是一个 XOR engine 能解决的

| 问题 | FPGA/控制器里对应的模块 |
|---|---|
| data/parity 必须成组提交 | write scheduler + completion tracker |
| 掉电后要知道哪些 stripe 可疑 | metadata bitmap / dirty stripe table |
| 恢复时要决定重放还是回滚 | recovery state machine |
| 不能无限缓存所有写 | stripe buffer + backpressure |
| parity mismatch 要被发现 | scrub / check engine |

因此 FPGA RAID5 设计里，XOR engine 只负责“怎么算”。write hole 逼你回答的是“什么时候算这次写真的完成”。

## 常见缓解思路，只先记名字

这个项目还没实现这些机制，本页只把路标放出来：

| 机制 | 直觉 | 代价 |
|---|---|---|
| battery-backed / power-loss-protected cache | 掉电后仍能把未完成写刷完 | 需要硬件保护和恢复流程 |
| journal / write-ahead log | 先记录“我要改什么”，恢复时重放或回滚 | 多一次元数据写，控制复杂 |
| PPL / partial parity log | 专门记录 partial write 的 parity 变化 | 适合 RAID5/6，但实现细节复杂 |
| dirty bitmap / stripe bitmap | 记住哪些区域可能不干净，恢复后重点检查 | 只能缩小检查范围，不等于自动修好 |
| scrub / parity check | 后台重新计算并发现 mismatch | 需要带宽，发现时可能已经晚了 |

下一关 `rebuild_and_scrub.md` 会继续讲：坏盘后怎么读、怎么重建、为什么 scrub 能把“潜伏错误”提前暴露。

## 自己算一遍

1. `D0=0xaa, old_D1=0xcc, D2=0x00, old_P=0x66, new_D1=0x0f`，正确的 `new_P` 是多少？
2. 如果 data 已写成 `0x0f`，parity 仍是 `0x66`，`disk2` 坏了以后恢复出的 D1 是多少？
3. 如果 parity 已写成 `0xa5`，data 仍是 `0xcc`，正常读 D1 会看到多少？恢复读又会算出多少？
4. 为什么“正常读没报错”不代表 parity 一定正确？
5. 放到 FPGA RAID 控制器里看，write completion tracker 要证明什么？

参考答案：

1. `0xa5`；
2. `0xaa XOR 0x00 XOR 0x66 = 0xcc`，恢复出旧值；
3. 正常读看到 `0xcc`，恢复读算出 `0x0f`；
4. 因为正常读通常直接读 data disk，不会每次读出整个 stripe 重新 XOR parity；
5. 要证明 data/parity 这组写要么都完成并可认为 committed，要么恢复流程知道它处在可疑/未完成状态。

## 如果你想动手验证

从仓库根目录运行：
```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

`demo_write_hole.py` 会把上面的手算变成可运行输出：正常读直接读 data block，看起来可能没坏；一旦 disk2 缺失，恢复路径只能拿其它 data 和 parity XOR，于是 mismatch 立刻变成错误数据。

---

## 继续阅读

⬅️ [上一篇：RAID5 写路径](raid5_write_path.md)<br>
🏠 [回到课程目录](index.md)<br>
➡️ [下一篇：Rebuild 和 Scrub](rebuild_and_scrub.md)
