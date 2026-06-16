# RAID5 Parity - 少丢一块盘容量的安全网

## 核心结论

RAID5 的核心只有一句话：**像 RAID0 一样把数据拆到多块盘，再给每个 stripe 加一块 XOR 校验块**。

它夹在 RAID0 和 RAID1 中间：

| 项目 | RAID0 | RAID1 | RAID5 |
|---|---|---|---|
| 数据放法 | 拆散 | 复制 | 拆散 + 校验 |
| 容量代价 | 几乎没有 | 复制几份就少几份 | 少 1 块盘容量 |
| 单盘故障 | 部分数据不可读 | 仍可读 | 可用 XOR 算回来 |
| FPGA 重点 | LBA mapper | 写入扇出/健康盘选择 | XOR engine + stripe layout |

如果把 RAID0 想成“大家分头搬砖”，RAID1 是“每份文件复印一份”，RAID5 就是“每组砖额外留一张校验清单”：少一个人时，可以用其他人的记录把缺的那份推回来。

> 本页先只讲 full-stripe write：一次写满一个 stripe 的所有数据块。partial write / write hole 会在后续页面单独拆。

## XOR 为什么能当校验？

XOR 有一个很好用的性质：**同一个值 XOR 两次会抵消**。

```text
A XOR A = 0
A XOR 0 = A
```

所以如果 parity 是：

```text
P = D0 XOR D1
```

那么坏掉 `D0` 时：

```text
D0 = D1 XOR P
```

坏掉 `D1` 时：

```text
D1 = D0 XOR P
```

这就是 RAID5 degraded read 的直觉：只坏一块盘时，缺的块可以由同一 stripe 里剩下的块 XOR 回来。

## 一个 3 块盘的手算例子

假设每个 block 只有 1 byte：

| 块 | 二进制 | 十六进制 |
|---|---|---|
| D0 | `10101010` | `0xaa` |
| D1 | `11001100` | `0xcc` |
| P = D0 XOR D1 | `01100110` | `0x66` |

如果 `D0` 所在硬盘坏了：

```text
D1 XOR P = 11001100 XOR 01100110 = 10101010 = D0
```

如果 `D1` 所在硬盘坏了：

```text
D0 XOR P = 10101010 XOR 01100110 = 11001100 = D1
```

这不是 RAID5 独有的魔法，底层只是 XOR 可逆性。FPGA 里真正要做的是把同一 stripe 的多个 block 送进 XOR engine。

## 为什么 parity 要轮转？

如果 parity 永远放在同一块盘，那块盘会变成热点：每个 stripe 都要写它。

RAID5 会让 parity 在不同成员盘之间轮转。当前 Python 模型的规则很直接：

```python
parity_disk = stripe % disk_count
```

4 块盘时，`RAID5.layout_row()` 会得到：

| stripe | disk0 | disk1 | disk2 | disk3 |
|---|---|---|---|---|
| 0 | P | D0 | D1 | D2 |
| 1 | D3 | P | D4 | D5 |
| 2 | D6 | D7 | P | D8 |
| 3 | D9 | D10 | D11 | P |

这里的 `P` 是当前 stripe 的 XOR parity，不是某个固定逻辑块。`D0`、`D1` 这些标签是 demo 里为了方便人眼观察而写的逻辑数据块编号。

## LBA 怎么落到 RAID5？

RAID5 仍然要做映射，只是比 RAID0 多了 parity 位置。

4 块盘时，每个 stripe 有 3 个数据块：

```text
data_disks = disk_count - 1 = 3
stripe     = lba // data_disks
offset     = lba % data_disks
parity     = stripe % disk_count
disk       = data_disk_order(stripe)[offset]
disk_lba   = stripe
```

其中 `data_disk_order(stripe)` 的意思是：跳过 parity 盘，剩下的盘按编号放数据。

例如 4 块盘、LBA 0~8：

| LBA | stripe | parity disk | data disk | disk_lba |
|---:|---:|---:|---:|---:|
| 0 | 0 | disk0 | disk1 | 0 |
| 1 | 0 | disk0 | disk2 | 0 |
| 2 | 0 | disk0 | disk3 | 0 |
| 3 | 1 | disk1 | disk0 | 1 |
| 4 | 1 | disk1 | disk2 | 1 |
| 5 | 1 | disk1 | disk3 | 1 |
| 6 | 2 | disk2 | disk0 | 2 |
| 7 | 2 | disk2 | disk1 | 2 |
| 8 | 2 | disk2 | disk3 | 2 |

这张表对应模型里的：

```python
RAID5.map_lba(lba) -> (disk_index, disk_lba, parity_disk_index)
```

## full-stripe write 做了什么？

当前 Level 0 模型故意只实现 full-stripe write：一次写满一个 stripe 的所有数据块。

以 stripe 0 为例：

```text
host data: D0, D1, D2
parity:    P = D0 XOR D1 XOR D2
layout:    disk0=P, disk1=D0, disk2=D1, disk3=D2
```

对应源码：

```python
RAID5.write_full_stripe(stripe, data_blocks)
```

它做两件事：

1. 按 `data_disk_order(stripe)` 把数据块写到非 parity 盘；
2. 用 `xor_blocks(data_blocks)` 算出 parity，写到 `parity_disk(stripe)`。

## degraded read：坏一块盘怎么读？

假设 stripe 0 的 `disk1` 坏了，缺的是 `D0`：

```text
已知：disk0=P, disk2=D1, disk3=D2
缺失：disk1=D0
恢复：D0 = P XOR D1 XOR D2
```

模型里的 `RAID5.read(lba)` 会先看目标 data disk 是否健康：

```text
目标盘健康：直接读目标盘
目标盘故障：读取同 stripe 其他盘，XOR 重建目标块
```

如果坏的是 parity 盘，读普通数据不需要重建；但 rebuild 这个坏 parity 盘时，仍然可以用所有数据块 XOR 重新算出 parity。

## rebuild：换新盘后怎么补回来？

`RAID5.rebuild_disk(disk_idx)` 的直觉是：

```text
for each stripe:
    new_block = XOR(同一 stripe 里除了坏盘之外的所有块)
    write new_block to replacement disk
```

这和 degraded read 是同一件事，只是 degraded read 重建一个被读的块，rebuild 要把整块替换盘的每个 stripe 都补齐。

限制也很重要：RAID5 只能容忍 **一块盘** 故障。如果 rebuild 时还有第二块盘坏了，同一 stripe 里会缺两个未知数，单个 XOR parity 不够解。

## 对 FPGA 来说意味着什么？

RAID5 parity 页对应的硬件模块会比 RAID0/RAID1 更接近真实控制器：

| 软件模型概念 | FPGA 里的影子 |
|---|---|
| `map_lba()` | LBA mapper：算 stripe、offset、data disk、parity disk |
| `xor_blocks()` | XOR engine：多输入 XOR 组合或流水线 |
| `write_full_stripe()` | stripe manager：收齐数据块，发起多盘写 |
| `read()` degraded path | degraded read controller：发现坏盘后读其他盘并 XOR |
| `rebuild_disk()` | rebuild engine：顺序扫 stripe，把替换盘补齐 |

Level 0 先把这些行为跑通。后面进入 RTL 时，可以先做最小 `xor_engine`，再做 `lba_mapper`。

## 手算小练习

1. 4 块盘时，`stripe 3` 的 parity 在哪块盘？
2. 4 块盘时，`LBA 7` 落在哪个 stripe、哪块 data disk？
3. 如果 `D0=0xaa`、`D1=0xcc`、`P=0x66`，坏了 `D1`，能不能算回 `D1`？
4. RAID5 同时坏两块盘，为什么单个 XOR parity 不够？

参考答案：

1. `stripe 3 % 4 = 3`，parity 在 `disk3`；
2. `7 // 3 = 2`，`7 % 3 = 1`，stripe 2 parity 在 `disk2`，data order 是 `disk0,disk1,disk3`，所以 LBA 7 在 `disk1:block2`；
3. 可以，`D1 = D0 XOR P = 0xaa XOR 0x66 = 0xcc`；
4. 因为同一个等式里有两个未知数据块，`P = A XOR B XOR C` 只够恢复一个未知数。

## 动手检查

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

重点观察：

- demo 里的 RAID5 parity 是否在 `disk0,disk1,disk2,disk3` 之间轮转；
- `RAID5.layout_row()` 是否和本页表格一致；
- 测试里的 RAID5 单盘故障读、坏盘重建是否符合“只坏一块可以 XOR 回来”。

下一关建议看 `docs/raid5_write_path.md`：RAID5 最麻烦的不是会不会 XOR，而是 partial write 时怎么避免 write hole。
