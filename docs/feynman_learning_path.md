# 费曼学习路径 - 把星载 NVMe RAID 固存讲给新人听

## 核心结论

先别背协议名。把系统想成一句话：

> 卫星载荷不断产生数据，FPGA 像仓库调度员，把数据分给多块 NVMe SSD；RAID 负责“放得快、坏一块还能找回来”；控制面负责“状态看得见、故障管得住”。

如果你能把这句话讲清楚，再去看 AXIS、AXI-Lite、NVMe 队列和 RAID5 写路径，就不会迷路。

## 第 0 关：为什么需要这个系统

### 用小学生也能懂的话说

一台相机一直拍照，数据来得太快，一块硬盘来不及写。

办法是找很多块硬盘一起干活：

```text
一块盘：一个人搬箱子，慢
多块盘：一队人分头搬，快
RAID：队长规定每个箱子放哪、坏一个人时怎么补救
```

星载固存样机就是这个“高速数据仓库”的工程版本。

### 对应工程词

- 载荷数据流：连续来的箱子；
- NVMe SSD：货架；
- FPGA：调度员；
- RAID0/1/5：不同分货和备份规则；
- 遥测：仓库状态看板；
- 重建：某个货架坏了以后，把丢失内容补到新货架。

## 第 1 关：先懂 RAID 三兄弟

| 模式 | 一句话 | 好处 | 代价 |
|---|---|---|---|
| RAID0 | 轮流把数据切到多块盘 | 快、容量利用高 | 坏一块就丢一部分 |
| RAID1 | 每份数据写两份 | 坏一块还能读 | 容量减半 |
| RAID5 | 数据分散放，再放 XOR 校验 | 容量和可靠性折中 | 写入和重建更复杂 |

先跑：

```bash
python labs/level0_python_model/demo_layout.py
```

你要观察的不是代码，而是：同一个 LBA 最后落在哪块盘。

## 第 2 关：为什么 RAID5 的 XOR 能救数据

费曼解释：

```text
A XOR B XOR C = P
如果 B 丢了：B = A XOR C XOR P
```

这就像三个人的账和总校验都记着，丢一个人的账，可以用其他账倒推回来。

先跑：

```bash
python labs/level0_python_model/demo_rebuild_and_scrub.py
```

你要观察：坏盘后，系统不是“找回原盘”，而是用幸存数据和 parity 重算缺失块。

## 第 3 关：为什么工程样机不只是 RAID

技术要求里最容易让新人低估的是：RAID 只是中间一层。

```text
8路输入AXIS
   -> 流量控制/缓存/仲裁
   -> RAID映射/校验/重建
   -> NVMe Host/PCIe
   -> SSD

AXI-Lite寄存器
   -> 配模式、读状态、清中断、做错误注入
```

所以要分四层理解：

1. **数据面**：数据怎么高速流动；
2. **控制面**：寄存器怎么配置和回读；
3. **设备面**：NVMe SSD 怎么初始化、读写、报健康；
4. **验证面**：怎么证明功能、性能、异常恢复都过关。

## 第 4 关：从教程到工程的距离

本仓库当前只覆盖最前面的学习闭环：

```text
RAID概念 -> Python模型 -> 小RTL模块 -> 架构地图
```

离工程样机还差：

- NVMe Host 协议栈（路线取舍见 `docs/nvme_host_options.md`）；
- PCIe Gen3 x4 接入；
- 8 路 AXIS 汇聚和背压；
- DDR/缓存/队列调度；
- AXI-Lite 寄存器表；
- 板级约束、时序、资源、热设计；
- 72 小时稳定性和异常恢复测试。

这不是失败，而是学习边界清楚：先把地图画对，再决定哪一块值得深入实现。

## 推荐学习顺序

```text
1. docs/requirements_alignment.md     # 先知道工程目标
2. docs/00_big_picture.md             # 看整体架构图
3. docs/raid_basics.md                # 补RAID基本概念
4. docs/raid5_parity.md               # 搞懂XOR恢复
5. docs/raid5_write_path.md           # 搞懂RAID5写为什么难
6. docs/axis_axi_lite_basics.md      # 搞懂数据传送带和控制台
7. docs/nvme_host_options.md          # 搞懂真实SSD接入路线和边界
8. docs/fpga_architecture.md          # 再看FPGA模块怎么拆
9. labs/level0_python_model/          # 跑demo看现象
10. rtl/xor_engine 和 rtl/lba_mapper  # 看最小硬件积木
```
