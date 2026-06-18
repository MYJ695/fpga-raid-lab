# 学习计划 - 按时间和角色读懂 FPGA RAID Lab

## 先抓住这句话

这个仓库不是让你一口气写出 NVMe RAID 样机，而是先把工程地图看懂。

换成费曼式说法：
```text
先知道仓库、货架、调度员、监控台分别是谁，
再去讨论某一个货架螺丝怎么拧。
```

如果时间有限，按下面的路线读；不要从 RTL 目录开始硬啃。

## 按时间预算选择路线

### 20 分钟：只建立大图

适合：第一次听到“星载 NVMe RAID 固存”的读者、项目负责人快速扫盲。

| 顺序 | 读什么 | 目标 |
|---:|---|---|
| 1 | `README.md` 的“一句话目标”和“项目定位” | 知道这个仓库只做前期调研和补课 |
| 2 | `docs/requirements_alignment.md` 的核心结论 | 先看技术要求到底在问什么，哪些内容这个仓库只做路线图 |
| 3 | `docs/feynman_learning_path.md` 的核心结论和第 0 关 | 用人话讲出系统为什么存在 |
| 4 | `docs/00_big_picture.md` | 看到数据面、RAID 层、控制面、NVMe 边界 |
| 5 | `docs/working_modes.md` 的核心结论和“五种工作模式一览” | 知道自检、待机、记录、回放、边记边放分别在系统里干什么 |
| 6 | `docs/acceptance_checklist.md` 的核心结论 | 分清 demo、教程、工程验收三者差别 |

20 分钟后你应该能说：
```text
这是一个“高速输入数据 -> FPGA 调度和保护 -> 多块 NVMe SSD 存储 -> 可观测可验收”的系统。
```

### 60 分钟：能讲清 RAID 和接口边界

适合：准备参与讨论方案的人，或者要判断这个仓库是否对齐技术要求的人。

| 顺序 | 读什么 | 目标 |
|---:|---|---|
| 1 | 完成 20 分钟路线 | 先有整体地图 |
| 2 | `docs/requirements_alignment.md` | 把技术要求翻译成学习主题 |
| 3 | `docs/raid_basics.md` | 知道 RAID0/1/5 的基本取舍 |
| 4 | `docs/raid5_parity.md` | 理解 XOR parity 为什么能恢复单盘故障 |
| 5 | `docs/axis_axi_lite_basics.md` | 分清 AXIS 数据流和 AXI-Lite 控制台 |
| 6 | `docs/working_modes.md` | 把五种工作模式看成系统状态机，而不是零散功能点 |
| 7 | `docs/nvme_host_options.md` | 知道为什么第一阶段不直接实现完整 NVMe Host |

60 分钟后你应该能回答：
```text
哪些问题属于 RAID 算法？哪些属于 FPGA 数据流？哪些属于 NVMe/PCIe/IP 选型？哪些属于验收证据？
```

### 2 小时：跑完现象级 demo，具备继续调研入口

适合：要继续做方案拆解、验证计划或后续 RTL/IP 评估的人。

| 顺序 | 做什么 | 目标 |
|---:|---|---|
| 1 | 完成 60 分钟路线 | 已有概念地图 |
| 2 | 读 `docs/raid5_write_path.md`、`docs/write_hole.md` | 知道 RAID5 写入为什么危险 |
| 3 | 读 `docs/rebuild_and_scrub.md` | 知道重建和巡检为什么是验收关注点 |
| 4 | 读 `docs/control_plane_registers.md` | 知道软件如何看状态、注入错误、追踪重建 |
| 5 | 跑 `labs/level0_python_model` 里的 demo | 把映射、write hole、rebuild/scrub、控制面状态看见 |
| 6 | 只浏览 `rtl/xor_engine` 和 `rtl/lba_mapper` runner | 知道最小硬件积木如何被测试，不要求深入写 RTL |
| 7 | 读 `docs/fpga_architecture.md` | 回到系统模块划分 |

2 小时后你不需要会写完整代码，但应该能提出下一阶段的问题：板卡/IP 怎么选？真实吞吐怎么压测？异常注入怎么闭环？资料如何和 bitstream/测试报告绑定？

## 按角色选择路线

| 角色 | 优先阅读 | 可以先跳过 | 你要带走的问题 |
|---|---|---|---|
| 新手学习者 | `docs/feynman_learning_path.md`、`docs/00_big_picture.md`、`docs/raid_basics.md` | RTL 细节 | 我能不能把系统讲给别人听？ |
| 项目负责人 | `README.md`、`docs/requirements_alignment.md`、`docs/acceptance_checklist.md`、`docs/nvme_host_options.md` | 具体 Verilog | 现在仓库覆盖了哪些前期调研，哪些还不是工程交付？ |
| 测试/验收工程师 | `docs/acceptance_checklist.md`、`docs/rebuild_and_scrub.md`、`docs/control_plane_registers.md` | RAID0 组合逻辑细节 | 哪些证据能证明状态、故障、恢复和资料一致？ |
| 软件/驱动/控制面 | `docs/axis_axi_lite_basics.md`、`docs/control_plane_registers.md`、`labs/level0_python_model/demo_control_plane.py` | NVMe PHY/PCIe 细节 | 软件如何配置、观察、清中断、追踪 rebuild/scrub？ |
| FPGA RTL 学习者 | `docs/fpga_architecture.md`、`rtl/xor_engine`、`rtl/lba_mapper` | 完整 NVMe Host 实现 | 哪些小模块适合先硬件化，哪些应先保持抽象？ |

## 术语先别慌：一句人话速查

| 术语 | 一句话解释 | 在这个仓库哪里看 |
|---|---|---|
| AXIS | 高速数据传送带，valid/ready 决定这拍能不能交货 | `docs/axis_axi_lite_basics.md` |
| AXI-Lite | 慢速控制台，软件通过寄存器配置和查看硬件 | `docs/axis_axi_lite_basics.md`、`docs/control_plane_registers.md` |
| 工作模式 | 固存样机现在处在自检、待机、记录、回放还是边记边放；它决定数据面和控制面该做什么 | `docs/working_modes.md` |
| 边记边放 | 一边写入新载荷、一边回放旧数据，是最容易暴露缓存、仲裁、背压和死锁风险的模式 | `docs/working_modes.md` |
| NVMe Host | 会和真实 NVMe SSD 说话的主机侧协议/IP/软件栈 | `docs/nvme_host_options.md` |
| PCIe Gen3 x4 | NVMe SSD 常用高速通道规格之一，不等于已经有完整存储系统 | `docs/nvme_host_options.md` |
| RAID0 | 把数据分条写到多块盘，追求吞吐，但坏一块就丢对应数据 | `docs/raid0_mapping.md` |
| RAID1 | 把数据复制到镜像盘，容量换可靠性 | `docs/raid1_mirror.md` |
| RAID5 | 数据加 XOR parity 分布在多块盘，坏一块还能算回来 | `docs/raid5_parity.md` |
| stripe | 多块盘在同一轮共同组成的一组数据/校验块 | `docs/raid5_parity.md` |
| rebuild | 换盘后用幸存数据和 parity 把缺失内容补回新盘 | `docs/rebuild_and_scrub.md` |
| scrub | 主动巡检数据和 parity 是否一致 | `docs/rebuild_and_scrub.md` |
| write hole | 数据和 parity 写到一半断电，二者不再匹配的坑 | `docs/write_hole.md` |
| abstract disk port | 先把 SSD 抽象成读写块接口，避免一开始陷入 NVMe/PCIe 复杂度 | `docs/nvme_host_options.md` |
| IRQ/W1C | 中断状态用来通知事件；W1C 表示写 1 清除对应状态位 | `docs/control_plane_registers.md` |
| telemetry / 遥测与事件信息 | 工程运行时的状态、计数、进度、错误记录和关键事件，是验收时追踪“系统发生过什么”的证据 | `docs/control_plane_registers.md`、`docs/working_modes.md` |

## demo 和 RTL runner 到底看什么

| 位置 | 你应该看见什么 | 不要误解成什么 |
|---|---|---|
| `demo_layout.py` | LBA 到成员盘/stripe/parity 的布局 | 真实磁盘驱动 |
| `demo_write_hole.py` | RAID5 写一半失败为什么危险 | 完整断电保护方案 |
| `demo_rebuild_and_scrub.py` | 单盘故障后如何读、重建、巡检 | 真实后台任务调度器 |
| `demo_control_plane.py` | 软件可见寄存器状态如何随故障、IRQ、rebuild、scrub 变化 | AXI-Lite 从设备 RTL |
| `python -m pytest -q labs/level0_python_model` | Python 行为模型的边界行为被测试锁定 | 板级验收通过 |
| `rtl/xor_engine/run_tests.py` | XOR parity 最小硬件积木能仿真 | 完整 RAID5 引擎 |
| `rtl/lba_mapper/run_tests.py` | LBA 映射可以做成简单组合逻辑 | 完整多盘调度器 |

## 最后自测

读完你可以用 7 个问题自测：

1. 这个仓库为什么不直接写完整 NVMe Host？
2. RAID0、RAID1、RAID5 分别用什么换什么？
3. 自检、待机、记录、回放、边记边放分别解决什么系统运行问题？
4. 为什么边记边放最容易暴露缓存、仲裁、背压和死锁风险？
5. AXIS 和 AXI-Lite 在系统里各管什么？
6. rebuild、scrub、write hole 为什么会进入验收讨论？
7. Python demo、RTL runner、工程样机验收三者的证据边界分别是什么？

能答出来，就说明你已经完成这个仓库的第一阶段目标：不是会写所有代码，而是有资格提出正确的工程问题。

---

## 继续阅读

⬅️ [上一篇：费曼学习路线](feynman_learning_path.md)<br>
🏠 [回到课程目录](index.md)<br>
➡️ [下一篇：系统大图](00_big_picture.md)
