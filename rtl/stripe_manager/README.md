# stripe_manager - RAID5 full-stripe 动作拆分接口草案

## 核心结论

`stripe_manager` 是第三关：它不负责 XOR 计算，也不负责真实磁盘协议，只把一个已经对齐的 RAID5 full-stripe write 拆成每块盘要做的 chunk action。

**当前状态：本目录目前只有接口草案，还没有 `stripe_manager.v` RTL 实现。**

第一版先做“排队表”，不做“搬运工”：

```text
stripe_index + data_count + write_valid
        |
        v
per-disk actions: IDLE / DATA / PARITY / UNSUPPORTED_RMW
```

## 为什么现在只写 README

前两关已经把基础积木拆开：

1. `xor_engine`：回答“多个 data block 怎样生成 parity”；
2. `lba_mapper`：回答“一个 logical LBA 落到哪块盘”；
3. `stripe_manager`：下一步才回答“一个 stripe 写入会触发哪些盘动作”。

现在还不急着写 `stripe_manager.v`，因为 `lba_mapper` 的 RTL 版本仍只覆盖 RAID0 映射，RAID5 的 parity rotation / data slot 映射尚未硬件化。先把接口草案写清楚，可以避免第三关一开始就变成完整控制器。

## 第一版范围

只支持 RAID5 full-stripe write。

假设：

- `DISK_COUNT >= 3`；
- 每个 stripe 有 `DISK_COUNT - 1` 个 data chunk；
- parity disk 使用当前 Python 模型的规则：

```text
parity_disk = stripe_index % DISK_COUNT
```

- data disk order 与 `RAID5.data_disk_order(stripe)` 一致：从 `disk0` 到 `diskN-1` 扫描，跳过 parity disk。

## 第一版输入

| 名称 | 含义 | 备注 |
|---|---|---|
| `stripe_index` | 要写入的 RAID5 stripe 编号 | 用来决定 parity disk |
| `data_count` | 本次写入包含多少个 data chunk | 第一版必须等于 `DISK_COUNT - 1` |
| `write_valid` | 请求是否有效 | `0` 表示本周期没有写请求 |

第一版不接收真实 data bytes。data bytes 会交给 `xor_engine` 计算 parity；`stripe_manager` 只决定“谁是 data，谁是 parity”。

## 第一版输出与 action 编码

对每个 disk 输出一个 action。为了让 Verilog-2001 testbench 可以直接断言，action 固定为 2 bit 编码：

| action | 编码 | 含义 |
|---|---:|---|
| `ACTION_IDLE` | `0` | 本次请求不触碰该 disk |
| `ACTION_DATA` | `1` | 该 disk 写入某个 data chunk |
| `ACTION_PARITY` | `2` | 该 disk 写入 parity chunk |
| `ACTION_UNSUPPORTED_RMW` | `3` | 不是 full-stripe write，需要 read-modify-write，第一版不做 |

配套规则：

- `action_code[disk] == ACTION_DATA` 时，`data_slot[disk]` 表示该 disk 写入第几个 data chunk；
- 其他 action 下，`data_slot[disk]` 固定为 `0`，避免教学 testbench 被 X 值干扰；
- full-stripe write 正常情况下不会出现 `IDLE`，但 `write_valid=0` 时所有 disk 都是 `IDLE`。

## 最小 Verilog-2001 接口草案

下一步若写 RTL，可以先使用 packed bus，避免 SystemVerilog 数组端口：

```verilog
module stripe_manager #(
    parameter DISK_COUNT   = 4,
    parameter STRIPE_WIDTH = 32,
    parameter SLOT_WIDTH   = 8
)(
    input  [STRIPE_WIDTH-1:0]       stripe_index,
    input  [7:0]                    data_count,
    input                           write_valid,
    output [2*DISK_COUNT-1:0]       action_code,
    output [SLOT_WIDTH*DISK_COUNT-1:0] data_slot,
    output                          unsupported
);
```

约定：

- disk `d` 的 action 位段是 `action_code[2*d +: 2]`；
- disk `d` 的 data slot 位段是 `data_slot[SLOT_WIDTH*d +: SLOT_WIDTH]`；
- `DISK_COUNT` 是 parameter，第一批 testbench 至少覆盖 `3/4/5`；
- 这是组合逻辑草案，不定义时钟、复位、AXI 或 valid-ready 握手。

## `write_valid` / `data_count` 输出规则

第一版把 unsupported 场景收敛成单一规则，方便读者写断言：

| 条件 | per-disk action | `unsupported` |
|---|---|---:|
| `write_valid == 0` | 全部 `ACTION_IDLE` | `0` |
| `write_valid == 1 && data_count == DISK_COUNT - 1` | 1 个 `ACTION_PARITY`，其余为 `ACTION_DATA` | `0` |
| `write_valid == 1 && data_count != DISK_COUNT - 1` | 全部 `ACTION_UNSUPPORTED_RMW` | `1` |

也就是说，第一版不尝试“部分 disk 先写、部分 disk 等 RMW”。只要不是 full-stripe write，就清楚地拒绝。

## 示例：最小 3 盘 RAID5

`DISK_COUNT=3` 是 RAID5 的最小教学形态，也适合作为第一个 testbench vector：

```text
stripe 0: disk0=PARITY, disk1=DATA(0), disk2=DATA(1)
stripe 1: disk0=DATA(0), disk1=PARITY, disk2=DATA(1)
stripe 2: disk0=DATA(0), disk1=DATA(1), disk2=PARITY
stripe 3: disk0=PARITY, disk1=DATA(0), disk2=DATA(1)
```

## 示例：4 盘 RAID5

```text
stripe 0: disk0=PARITY, disk1=DATA(0), disk2=DATA(1), disk3=DATA(2)
stripe 1: disk0=DATA(0), disk1=PARITY, disk2=DATA(1), disk3=DATA(2)
stripe 2: disk0=DATA(0), disk1=DATA(1), disk2=PARITY, disk3=DATA(2)
stripe 3: disk0=DATA(0), disk1=DATA(1), disk2=DATA(2), disk3=PARITY
```

这和 Python 模型里的：

```python
RAID5.parity_disk(stripe)
RAID5.data_disk_order(stripe)
RAID5.layout_row(stripe)
```

必须保持一致。

## 明确不做

第一版暂不做：

- partial write；
- read-modify-write；
- reconstruct-write；
- degraded write；
- 多请求调度；
- AXI、valid-ready、真实磁盘接口；
- parity 数据本身的 XOR 计算。

这些不是被忘了，而是后续关卡。当前关卡只让读者看清楚：RAID5 的一次 full-stripe write，为什么每块盘的角色会随着 stripe 轮转。

## 未来验收标准

等开始写 RTL/testbench 时，最小验收应覆盖：

1. `DISK_COUNT=3,4,5`；
2. 至少 `stripe_index=0..DISK_COUNT`，覆盖 parity 轮转回到 disk0；
3. `write_valid == 0` 时所有 disk 输出 `ACTION_IDLE`；
4. `data_count == DISK_COUNT - 1` 时输出完整 DATA/PARITY actions；
5. `data_count != DISK_COUNT - 1` 时所有 disk 输出 `ACTION_UNSUPPORTED_RMW` 且 `unsupported=1`；
6. 输出表能和 Python `RAID5.layout_row(stripe)` 对拍。
