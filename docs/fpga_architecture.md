# FPGA Architecture - 从需求地图走到 RTL 小模块

## 核心结论

第一阶段不要直接做“完整星载固存 FPGA 工程”。

更稳的路线是：先把技术要求拆成四张图，再把其中最核心、最容易验证的 RAID 行为做成 Python golden model 和 RTL 小模块。

```text
技术要求
  -> 数据面 / RAID面 / 控制面 / 设备面
  -> Python golden model
  -> RTL 小模块：xor_engine -> lba_mapper -> stripe_manager
  -> 更大的 read/write/rebuild/scrub 控制器
```

这页只定义早期架构边界，不承诺真实 NVMe、PCIe、板级约束或 40 Gbps 性能。

继续拆模块前，建议先读 [`axis_axi_lite_basics.md`](axis_axi_lite_basics.md)：它把 AXIS 解释成“数据传送带”，把 AXI-Lite 解释成“控制台”，能避免把高速数据路径和管理寄存器混成一个大黑盒。

## 从技术要求拆出的四个面

### 1. 数据面：高速数据怎么走

文档里的关键词：8 路输入、AXIS、64-bit、valid/ready、帧边界、字节有效、错误反馈。

早期学习目标：

- 知道 AXIS 是“带握手的流水传送带”；
- 理解 valid/ready 如何表达背压；
- 理解 8 路输入最终需要仲裁、缓存和统计；
- 暂不实现真实 8 路高吞吐汇聚器。

### 2. RAID 面：多盘怎么组织

文档里的关键词：RAID0、RAID1、RAID5、条带大小、成员盘映射、故障隔离、重建、一致性检查。

早期学习目标：

- 用 Python 看懂 LBA -> disk/chunk/stripe；
- 用 XOR 看懂 RAID5 单盘恢复；
- 用 demo 看懂 write hole、scrub、rebuild；
- 用小 RTL 模块验证 XOR 和 LBA 映射。

### 3. 控制面：系统怎么被管理

文档里的关键词：AXI-Lite、阵列模式、成员盘状态、错误计数、重建进度、告警、错误注入。

早期学习目标：

- 把“控制寄存器”理解成系统仪表盘；
- 能列出模式配置、状态回读、错误注入、统计计数四类寄存器；
- 暂不设计完整寄存器表。

### 4. 设备面：怎么接真实 SSD

文档里的关键词：NVMe 1.2/1.3、PCIe Gen3 x4、namespace、admin command、I/O queue、健康监测。

早期学习目标：

- 知道 NVMe Host 是独立复杂模块；
- 知道 RAID 层最好先和“抽象磁盘端口”对接；
- 暂不自己实现完整 NVMe/PCIe 协议栈。

## 最小学习数据路径

```text
Host / Payload request
  stream_id + lba + length + data
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

- `lba_mapper` 决定“这个箱子该去哪个货架”；
- `stripe_manager` 决定“一次请求要拆成几张小纸条”；
- `xor/parity_engine` 决定“校验线索怎么生成和反推”；
- `virtual disk ports` 先假装是 SSD，以后才替换为 NVMe Host。

## 第一批 RTL 边界

### 1. `rtl/xor_engine`

第一步做 XOR，因为它是 RAID5 最小硬件原语。

验收标准：

- 输入多个 data word；
- 输出 XOR parity；
- Python vector 能算出同样的结果；
- 失败时 testbench 返回非零。

### 2. `rtl/lba_mapper`

第二步做地址映射，因为 RAID 的“多盘调度感”来自这里。

先支持 RAID0：

```text
logical_lba -> disk_index, disk_lba
```

再扩展 RAID5：

```text
logical_lba -> data_disk, stripe, parity_disk
```

验收标准：

- 对照 `demo_layout.py` 的映射表；
- 至少覆盖 3、4、5 盘配置；
- 覆盖 stripe 边界。

### 3. `rtl/stripe_manager`

第三步才拆请求。

它不急着碰真实 AXIS 或 NVMe，只负责把一个 logical request 拆成 chunk 操作：

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

## 控制寄存器学习清单

工程样机后续至少会需要这些寄存器类别：

| 类别 | 例子 | 学习意义 |
|---|---|---|
| 模式配置 | RAID mode、stripe size、start/stop/init | 系统怎么被软件控制 |
| 成员盘状态 | present、failed、masked、rebuilding | 掉盘和替换怎么表达 |
| 统计计数 | stream bytes、write commands、errors | 性能和问题定位 |
| 重建状态 | rebuild enable、progress、throttle | 重建可控可观测 |
| 错误注入 | force disk fail、timeout、parity mismatch | 验收和联调需要可复现故障 |
| 告警中断 | fatal error、degraded、rebuild done | 系统如何通知上层 |

本仓库暂时只讲清楚这些寄存器为什么存在，不急着冻结地址表。

## 第一批之后再做什么

等 `xor_engine`、`lba_mapper`、`stripe_manager` 都能对拍后，再考虑：

1. `reconstruct_engine`：单盘失效时 XOR 其他盘恢复一个 block；
2. `rebuild_engine`：遍历所有 stripe，把替换盘补回来；
3. `scrub_engine`：后台读全条带并检查 parity mismatch；
4. `axis_ingress_model`：简化 2~8 路 valid/ready 输入模型；
5. `register_model`：AXI-Lite 寄存器影子模型；
6. NVMe Host 调研：自研、开源参考、厂商 IP 或 CPU/SoC 管理方案。

## 不要踩的坑

- 不要一开始写“完整 RAID 控制器顶层”，那会很快变成空壳；
- 不要把 NVMe/PCIe 协议和 RAID 算法混在第一个实验里；
- 不要只写 RTL 不写 testbench，否则读者不知道它对不对；
- 不要用教程 demo 冒充工程样机性能；
- 不要忽略控制面，工程验收会关心状态、告警、错误注入和版本一致性。
