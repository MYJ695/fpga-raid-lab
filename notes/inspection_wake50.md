# Inspection - Wake 50

## 阶段

第 50 次唤醒：检验阶段。

本轮只检查第 49 轮新增的 `rtl/stripe_manager/README.md`，不新增 RTL。检验视角是：

- **RTL testbench 作者**：是否能从 README 直接写出最小 testbench；
- **挑剔初学者**：是否会误解当前已有 `stripe_manager.v`，或者误以为它已经是完整 RAID5 控制器；
- **Python golden model 对拍者**：README 的动作表是否和 `RAID5.parity_disk()` / `RAID5.data_disk_order()` 一致。

## 本轮做了什么

1. 阅读 `rtl/stripe_manager/README.md` 全文。
2. 对照 `notes/changelog_wake49.md` 中给出的第 50 轮检验清单。
3. 读取 Python 模型中 RAID5 的关键口径：
   - `RAID5.parity_disk(stripe)`；
   - `RAID5.data_disk_order(stripe)`；
   - `RAID5.layout_row(stripe)`。
4. 读取 `rtl/lba_mapper/README.md`，确认当前 RTL 映射仍是 RAID0，不应把 `stripe_manager` 直接包装成完整 RAID5 LBA mapper。
5. 用 Python 临时脚本生成 `DISK_COUNT=3/4/5`、`stripe=0..DISK_COUNT` 的 action 表，模拟未来 testbench golden vector。

## 修改了哪些文件

本轮是检验阶段，只新增检验报告：

- `notes/inspection_wake50.md`

没有修改交付物文档或代码。

## 如何验证

### 1. 文档口径验证

已读取并核对：

- `rtl/stripe_manager/README.md`
- `notes/changelog_wake49.md`
- `labs/level0_python_model/raid_model.py`
- `rtl/lba_mapper/README.md`

### 2. Python golden action 推导

运行临时脚本，按 Python 模型生成 per-disk action：

```python
sys.path.insert(0, 'labs/level0_python_model')
from raid_model import VirtualDisk, RAID5

for disk_count in (3, 4, 5):
    disks = [VirtualDisk(block_count=8, block_size=4) for _ in range(disk_count)]
    r = RAID5(disks)
    for stripe in range(disk_count + 1):
        parity = r.parity_disk(stripe)
        order = r.data_disk_order(stripe)
        actions = []
        for d in range(disk_count):
            if d == parity:
                actions.append('PARITY')
            else:
                actions.append(f'DATA({order.index(d)})')
```

结果确认：

- `DISK_COUNT=3` 时 stripe 0..3 覆盖 parity 回到 disk0；
- `DISK_COUNT=4` 时 README 中的示例和 Python 模型一致；
- `DISK_COUNT=5` 时 data slot 仍按“从 disk0 到 diskN-1 扫描，跳过 parity disk”的规则增长。

## 检验结论

`rtl/stripe_manager/README.md` 已经达到“能解释边界”的及格线，但还没达到“能无歧义导出 RTL/testbench”的优秀线。

它现在清楚说明了：

- 第一版只支持 RAID5 full-stripe write；
- parity 规则是 `stripe_index % DISK_COUNT`；
- data disk order 和 Python `RAID5.data_disk_order(stripe)` 一致；
- 不做 XOR、不做 AXI、不做 partial write、不做真实磁盘协议。

但如果下一轮直接写 `stripe_manager.v`，testbench 作者仍会遇到几个空白。

## 发现了什么问题

### P1：action 还没有数值编码，testbench 不能直接断言

README 现在写的是：

- `DATA(slot)`；
- `PARITY`；
- `UNSUPPORTED_RMW`；
- `IDLE`。

这对人读很清楚，但对 Verilog-2001 testbench 不够清楚。下一轮应补一个稳定编码，例如：

```text
ACTION_IDLE            = 0
ACTION_DATA            = 1
ACTION_PARITY          = 2
ACTION_UNSUPPORTED_RMW = 3
```

并说明：

- `action_code[disk] == ACTION_DATA` 时，`data_slot[disk]` 才有意义；
- 其他 action 下 `data_slot[disk]` 可以固定为 0，避免 X 值污染教学 testbench。

### P1：缺少最小 Verilog-2001 接口草案

README 目前有“第一版输入/输出”的概念表，但没有接近 RTL 的端口形状。testbench 作者仍需猜：

- 每块盘的 action 是压成 bus，还是拆成多个输出；
- `data_slot` 位宽如何定；
- `DISK_COUNT` 是否是 parameter；
- `write_valid=0` 时输出 IDLE 还是保持不变。

建议下一轮补接口草案，但仍不写 RTL：

```verilog
module stripe_manager #(
    parameter DISK_COUNT   = 4,
    parameter STRIPE_WIDTH = 32,
    parameter SLOT_WIDTH   = 8
)(
    input  [STRIPE_WIDTH-1:0] stripe_index,
    input  [7:0]              data_count,
    input                     write_valid,
    output [2*DISK_COUNT-1:0] action_code,
    output [SLOT_WIDTH*DISK_COUNT-1:0] data_slot,
    output                    unsupported
);
```

这里 `action_code` 用每盘 2 bit 足够表达四种 action；`data_slot` 用定宽 packed bus，符合 Verilog-2001 教学约束。

### P2：`DISK_COUNT=3` 的最小例子值得补

当前 README 只有 `DISK_COUNT=4` 示例。对 FPGA 初学者来说，3 盘 RAID5 是最小可行形态，最好补一张小表：

```text
stripe 0: disk0=PARITY, disk1=DATA(0), disk2=DATA(1)
stripe 1: disk0=DATA(0), disk1=PARITY, disk2=DATA(1)
stripe 2: disk0=DATA(0), disk1=DATA(1), disk2=PARITY
stripe 3: disk0=PARITY, disk1=DATA(0), disk2=DATA(1)
```

这张表能直观看到 parity 轮转回 disk0，比 4 盘表示例更适合作为第一个 testbench vector。

### P2：`UNSUPPORTED_RMW` 和 `unsupported` 标志的关系未定义

README 说 `data_count != DISK_COUNT - 1` 时输出 `UNSUPPORTED_RMW` 或错误标志。这里的“或”会让实现分叉。

建议收敛为一个规则：

- `write_valid=0`：所有 disk 输出 `IDLE`，`unsupported=0`；
- `write_valid=1 && data_count == DISK_COUNT - 1`：输出正常 `DATA/PARITY`，`unsupported=0`；
- `write_valid=1 && data_count != DISK_COUNT - 1`：所有 disk 输出 `UNSUPPORTED_RMW`，`unsupported=1`。

这比“某些盘 unsupported、某些盘 idle”更容易教学，也更容易 testbench 断言。

### P3：README 没有误导“已经有 RTL”，但标题可以更精确

当前标题是“动作拆分草案”，正文也明确“现在还不急着写 `stripe_manager.v`”。这一点不会明显误导。

不过如果下轮改进，可以把标题或第一段再强化为：

```text
本目录目前只有接口草案，还没有 RTL 实现。
```

这能避免读者从 `rtl/stripe_manager/` 目录名误判“这里已经有可仿真的模块”。

## 不够出色的点

当前 README 最大短板不是内容错误，而是“离可执行 testbench 还差半步”。

一个优秀的闯关式实验室文档，应该让读者读完后能自然写出：

1. Python vector generator；
2. Verilog-2001 module skeleton；
3. Icarus testbench 断言；
4. 失败场景：`data_count != DISK_COUNT - 1`。

现在第 1 点可以推导出来，第 2~4 点仍需设计者补充规则。

## 下轮建议做什么

第 51 轮进入改进阶段，建议不要写完整 RTL，只改 `rtl/stripe_manager/README.md`：

1. 增加“当前状态：只有接口草案，没有 RTL 实现”；
2. 增加 action 数值编码；
3. 增加最小 Verilog-2001 接口草案；
4. 增加 `write_valid` / `data_count` 三种输出规则；
5. 补 `DISK_COUNT=3` 最小 action 表；
6. 更新 `notes/changelog_wake51.md` 并跑基础回归。

这样第 52 轮检验时，就可以真正站在 testbench 作者视角，判断是否已经能动手写 `stripe_manager.v` 和 `run_tests.py`。
