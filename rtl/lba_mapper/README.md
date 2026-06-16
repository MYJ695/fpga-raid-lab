# lba_mapper - RAID0 LBA 映射小模块

## 核心结论

`lba_mapper` 的第一关不做完整 RAID5 映射。

它只回答一个能被 testbench 抓住的小问题：

```text
RAID0 logical block address -> disk_index + disk_lba
```

也就是把 `docs/raid0_mapping.md` 和 Python golden model 里的 RAID0 映射公式，变成一块纯组合 Verilog RTL。

## 为什么先从 RAID0 开始

RAID5 的完整映射还要同时处理：

- data disk 选择；
- parity disk rotation；
- stripe row；
- full-stripe / degraded read / rebuild 对映射的不同需求。

这些都重要，但第一版 `lba_mapper` 应该先把“LBA 怎么落到某块盘的某个位置”讲清楚。

先 RAID0，再 RAID5，可以避免把读者一次推进公式迷宫。

## 第一版 RTL 规格

第一版是 **纯组合逻辑**：没有 clock、reset、valid-ready，也不接 AXI。

```verilog
module lba_mapper #(
    parameter LBA_WIDTH   = 32,
    parameter DISK_COUNT  = 4,
    parameter CHUNK_SHIFT = 0
)(
    input  [LBA_WIDTH-1:0] lba,
    output [7:0]           disk_index,
    output [LBA_WIDTH-1:0] stripe_index,
    output [LBA_WIDTH-1:0] disk_lba
);
```

参数策略：

| 参数 | 第一版含义 | 为什么这样定 |
|---|---|---|
| `LBA_WIDTH` | LBA 位宽，默认 32 | 方便后续扩大测试范围 |
| `DISK_COUNT` | 参与条带化的数据盘数量，默认 4 | **parameter 固定**，不是运行时输入，避免第一关解释可变除法器 |
| `CHUNK_SHIFT` | 一个 chunk 含 `1 << CHUNK_SHIFT` 个连续 LBA | **parameter 固定**，testbench 通过多次编译覆盖不同 chunk 大小 |

输出含义：

| 输出 | 含义 |
|---|---|
| `disk_index` | 这笔 LBA 落到第几块盘，从 0 开始；第一版固定为 `[7:0]`，教学上等价于假设 `DISK_COUNT <= 256` |
| `stripe_index` | 这是第几行 RAID0 stripe/chunk row |
| `disk_lba` | 该盘内部看到的 LBA，已经把 `chunk_offset` 加回去 |

命名提醒：

- `stripe_index` 是“第几行 chunk”；
- `disk_lba` 是最终给单盘的地址；
- 当 `CHUNK_SHIFT=0` 时，一个 LBA 就是一个 chunk，所以 `disk_lba == stripe_index`。

## RAID0 公式

当：

```text
chunk_size = 1 << CHUNK_SHIFT
```

公式为：

```text
logical_chunk = lba >> CHUNK_SHIFT
chunk_offset  = lba & (chunk_size - 1)
disk_index    = logical_chunk % DISK_COUNT
stripe_index  = logical_chunk / DISK_COUNT
disk_lba      = stripe_index * chunk_size + chunk_offset
```

`rtl/lba_mapper/lba_mapper.v` 直接实现这组公式。

## 建议测试点

### 基础条带：4 盘、单 LBA chunk

```text
DISK_COUNT=4, CHUNK_SHIFT=0
LBA 0 -> disk0, stripe0, disk_lba0
LBA 1 -> disk1, stripe0, disk_lba0
LBA 2 -> disk2, stripe0, disk_lba0
LBA 3 -> disk3, stripe0, disk_lba0
LBA 4 -> disk0, stripe1, disk_lba1
LBA 7 -> disk3, stripe1, disk_lba1
LBA 8 -> disk0, stripe2, disk_lba2
```

这组对齐 Python 模型：

```python
RAID0.map_lba(lba) == (lba % disk_count, lba // disk_count)
```

### 边界条带：3 盘、4-LBA chunk

```text
DISK_COUNT=3, CHUNK_SHIFT=2  # chunk_size=4
```

逐 LBA 期望表：

| LBA | logical_chunk | chunk_offset | disk_index | stripe_index | disk_lba |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 1 | 0 | 0 | 1 |
| 2 | 0 | 2 | 0 | 0 | 2 |
| 3 | 0 | 3 | 0 | 0 | 3 |
| 4 | 1 | 0 | 1 | 0 | 0 |
| 5 | 1 | 1 | 1 | 0 | 1 |
| 6 | 1 | 2 | 1 | 0 | 2 |
| 7 | 1 | 3 | 1 | 0 | 3 |
| 8 | 2 | 0 | 2 | 0 | 0 |
| 9 | 2 | 1 | 2 | 0 | 1 |
| 10 | 2 | 2 | 2 | 0 | 2 |
| 11 | 2 | 3 | 2 | 0 | 3 |
| 12 | 3 | 0 | 0 | 1 | 4 |
| 13 | 3 | 1 | 0 | 1 | 5 |
| 14 | 3 | 2 | 0 | 1 | 6 |
| 15 | 3 | 3 | 0 | 1 | 7 |

这张表专门抓两类常见错误：

1. 忘记把 `chunk_offset` 加回 `disk_lba`；
2. 在 LBA 3 -> 4、11 -> 12 这种 chunk 边界出现 off-by-one。

## 硬件边界：这是教学版映射，不是最终 datapath

这一关故意把公式直接写进组合逻辑：

```verilog
assign disk_index   = logical_chunk % DISK_COUNT;
assign stripe_index = logical_chunk / DISK_COUNT;
```

这样做的好处是读者能一眼对上 RAID0 数学公式；代价是综合器可能推导出较重的组合除法/取模电路。真实高性能 FPGA RAID datapath 通常会进一步约束或改写：

- 若 `DISK_COUNT` 是 2 的幂，用位切片/移位替代除法和取模；
- 若 `DISK_COUNT` 固定但不是 2 的幂，考虑 reciprocal multiply、查表、计数器或流水线；
- 若要接真实请求流，还需要 valid-ready、寄存器切分、时序约束和 backpressure。

所以 `DISK_COUNT=3/5` 的参数化测试不是在推荐真实硬件直接这样跑，而是专门用来抓“只在 2 的幂盘数下才看不出来”的边界错误。`disk_index [7:0]` 也是第一关的可读性取舍；更严谨的 SystemVerilog 版本可以用 `$clog2(DISK_COUNT)` 推导宽度。

## 怎么运行

从仓库根目录执行：

```bash
python rtl/lba_mapper/run_tests.py
```

runner 会做三件事：

1. 生成默认 `DISK_COUNT=4, CHUNK_SHIFT=0` 的可读 vector 文件；
2. 编译并运行固定 testbench；
3. 临时生成参数化 testbench，覆盖 `DISK_COUNT=3, CHUNK_SHIFT=2` 和 `DISK_COUNT=5, CHUNK_SHIFT=0`。

## 和 Python 模型的关系

第一版先对齐：

```python
RAID0.map_lba(lba)
```

后续再把 RAID5 的：

```python
RAID5.layout_row(row)
```

拆成 parity rotation 与 data slot 映射。

## 不做什么

第一版暂不做：

- RAID5 parity rotation；
- degraded read；
- 多请求合并；
- AXI/valid-ready 接口；
- 跨 clock domain；
- 接真实 SATA/NVMe/PCIe。

这些都留给后续关卡。现在先让一条 LBA 映射能被 testbench 抓住。
