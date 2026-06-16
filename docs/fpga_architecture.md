# FPGA Architecture - 从 Python 模型走到 RTL 小模块

## 核心结论

第一阶段不要直接做“完整 FPGA RAID 控制器”。

更稳的路线是：把已经在 Python golden model 里跑通的 RAID 行为，拆成几个能单独仿真、能和 Python 对拍的小 RTL 模块。

```text
Python golden model
    |
    |  产生映射表、数据块、parity 期望值
    v
RTL 小模块：xor_engine -> lba_mapper -> stripe_manager
    |
    |  testbench 对拍
    v
更大的 RAID read/write/rebuild 控制器
```

这页只定义第一批 RTL 边界，不承诺真实 SATA、NVMe、PCIe 或掉电恢复。

## 第一阶段边界

先做：

1. **算法小模块**：XOR、LBA 映射、stripe/chunk 拆分；
2. **控制小闭环**：valid/ready 或 start/done 级别的简单握手；
3. **仿真对拍**：用 Python 生成 test vector，RTL 输出必须和 Python 一致。

暂时不做：

- 真实磁盘协议：SATA / NVMe / PCIe；
- DMA、缓存一致性、主机驱动；
- 掉电保护、热插拔、复杂 metadata；
- 完整 RAID6 GF 运算。

这些不是不重要，而是太早做会把学习路线从“RAID 核心逻辑”拖进“接口工程泥潭”。

## 最小数据路径

```text
Host request
  lba + length + read/write
        |
        v
+----------------+       +------------------+
|  lba_mapper    | ----> |  stripe_manager  |
| logical ->     |       | split request    |
| disk/stripe    |       | into chunk ops   |
+----------------+       +------------------+
        |                         |
        |                         v
        |                +------------------+
        |                | xor/parity_engine|
        |                | data -> parity   |
        |                +------------------+
        |                         |
        v                         v
+------------------------------------------------+
| virtual disk ports / BRAM model / sim adapters |
+------------------------------------------------+
```

读者可以把它理解成：

- `lba_mapper` 决定“这个逻辑块该去哪个队员手里”；
- `stripe_manager` 决定“一次请求要拆成几张小纸条”；
- `xor/parity_engine` 决定“校验侦探怎么用 XOR 找回失踪队员”。

## Python 到 RTL 的映射表

| Python 锚点 | 已表达的行为 | 第一批 RTL 对应物 | 先验收什么 |
|---|---|---|---|
| `xor_blocks()` | 多个等长 block 逐字节 XOR | `rtl/xor_engine` | 输入 N 个 word，输出 XOR 结果 |
| `RAID0.map_lba()` | `disk = lba % disk_count`，`disk_lba = lba // disk_count` | `rtl/lba_mapper` RAID0 模式 | LBA 映射表逐项一致 |
| `RAID5.parity_disk()` | parity 随 stripe 轮转 | `rtl/lba_mapper` RAID5 模式 | stripe -> parity disk 一致 |
| `RAID5.map_lba()` | logical LBA -> data disk + stripe + parity disk | `rtl/lba_mapper` RAID5 模式 | LBA -> disk/stripe/parity 一致 |
| `RAID5.layout_row()` | 给文档和 demo 打印 stripe 布局 | test vector 生成脚本 | RTL 映射结果能还原同一张布局表 |
| `RAID5.write_full_stripe()` | data blocks 写入数据盘，XOR 写入 parity 盘 | `stripe_manager` + `xor_engine` | full-stripe write 的 chunk 操作顺序合理 |
| `RAID5.read()` 降级分支 | 数据盘失效时用其他盘 XOR 重构 | 后续 `reconstruct_engine` | 第二批再做，不抢第一批 |
| `RAID5.rebuild_disk()` | 遍历 stripe 重建整盘 | 后续 `rebuild_engine` FSM | 第二批再做，不抢第一批 |

重点是：第一批 RTL 不是凭空发明接口，而是把 Python 里已经验证过的函数硬件化。

## 推荐闯关顺序

### 1. `rtl/xor_engine`

为什么先做它：

- RAID5 的 parity 和 degraded read 都离不开 XOR；
- 输入输出简单，最适合第一条 RTL + testbench 闭环；
- 未来可以从组合逻辑升级成流水线，不影响上层概念。

最小接口可以先长这样：

```text
parameter DATA_WIDTH = 32
parameter INPUTS = 3

in_data[INPUTS][DATA_WIDTH] -> out_xor[DATA_WIDTH]
```

验收标准：

- Python 生成几组 data block；
- testbench 喂给 RTL；
- RTL 输出必须等于 `xor_blocks()` 的结果。

### 2. `rtl/lba_mapper`

第二步做地址映射，因为 RAID 的“多盘调度感”来自这里。

先支持 RAID0：

```text
logical_lba -> disk_index, disk_lba
```

再支持 RAID5：

```text
logical_lba -> data_disk, stripe, parity_disk
```

验收标准：

- 对照 `demo_layout.py` 的映射表；
- 至少覆盖 3、4、5 盘配置；
- 覆盖 stripe 边界，比如 LBA 2 -> LBA 3、LBA 3 -> LBA 4 这种跨行位置。

### 3. `rtl/stripe_manager`

第三步才拆请求。

它不急着碰真实 AXI 或磁盘协议，只负责把一个 logical request 拆成 chunk 操作：

```text
write LBA 0..5
  -> disk0 stripe0 data
  -> disk1 stripe0 data
  -> disk2 stripe0 parity
  -> disk1 stripe1 data
  ...
```

验收标准：

- full-stripe write 的 data/parity 操作完整；
- partial write 先只标记为 unsupported 或需要 RMW；
- 输出动作能和 Python demo 的布局解释对上。

### 4. `sim/` 对拍

最后补仿真说明和 test vector 约定。

建议目录结构：

```text
sim/
├── README.md
├── vectors/
│   ├── xor_engine_cases.txt
│   └── lba_mapper_cases.txt
└── run_*.sh / run_*.ps1
```

`sim/` 的目标不是炫工具，而是回答一句话：

> RTL 结果有没有和 Python golden model 一样？

## 第一批之后再做什么

等 `xor_engine`、`lba_mapper`、`stripe_manager` 都能对拍后，再考虑：

1. `reconstruct_engine`：单盘失效时 XOR 其他盘恢复一个 block；
2. `rebuild_engine`：遍历所有 stripe，把替换盘补回来；
3. `scrub_engine`：后台读全条带并检查 parity mismatch；
4. RAID6：引入 GF 运算和 P/Q parity；
5. 真实接口调研：SATA/NVMe/PCIe、DMA、缓存、驱动。

## 不要踩的坑

- 不要一开始写“完整 RAID 控制器顶层”，那会很快变成空壳；
- 不要把真实存储协议和 RAID 算法混在第一个实验里；
- 不要只写 RTL 不写 testbench，否则读者不知道它对不对；
- 不要让 RTL 接口脱离 Python 模型，否则 golden model 就失去价值。

## 下一步

下一关建议创建 `rtl/xor_engine/`：

1. 写最小 `README.md`，说明输入输出和对拍方式；
2. 写一个参数化 XOR RTL；
3. 用 Python 生成 3~5 个测试向量；
4. 写最小 testbench 或仿真说明。

这才是从“懂 RAID 行为”迈向“能在 FPGA 上验证一块 RAID 逻辑”的第一块砖。
