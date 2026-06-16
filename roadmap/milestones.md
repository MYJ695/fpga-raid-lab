# Milestones - 里程碑

## Milestone 0：对齐工程需求

目标：把《固存样机技术要求》翻译成学习地图。

产出：

- `docs/requirements_alignment.md`
- `docs/feynman_learning_path.md`
- 更新后的 README 和 big picture

验收：

- 能说清 8 路输入、NVMe SSD 阵列、RAID0/1/5、AXIS/AXI-Lite、验收交付之间的关系；
- 明确本仓库只做前期调研和基础补课，不冒充工程样机交付。

状态：已建立第一版。

## Milestone 1：RAID 世界观

目标：不用 FPGA，先把 RAID0/1/5 的行为讲清楚。

产出：

- RAID 基础文档；
- LBA 映射、镜像、RAID5 parity、写路径说明；
- Python 虚拟磁盘模型。

验收：

- 能解释容量、性能、可靠性三者取舍；
- 能画出 RAID0/1/5 的基本数据布局。

状态：已完成基础版。

## Milestone 2：Python RAID 小队

目标：用可运行 demo 把 RAID 行为看见。

产出：

- `VirtualDisk`
- RAID0 mapping
- RAID1 mirror
- RAID5 full-stripe write
- degraded read
- rebuild/scrub/write-hole demo

验收：

- pytest 基础用例通过；
- 模拟坏一块盘后 RAID5 能恢复读；
- demo 能展示 write hole 和 scrub mismatch。

状态：已完成基础版。

## Milestone 3：RTL 基础模块

目标：把最核心的硬件模块单独做出来。

产出：

- `xor_engine`
- `lba_mapper`
- 后续 `stripe_manager`
- testbench / runner / vector

验收：

- RTL 输出与 Python golden model 对齐；
- runner 可从仓库根目录一键执行；
- 缺少外部仿真工具时有清晰提示。

状态：`xor_engine`、RAID0 `lba_mapper` 已有基础版。

## Milestone 4：控制面和可观测性入门

目标：把工程验收关心的“看得见、控得住”纳入教程。

候选产出：

- `docs/axis_axi_lite_basics.md` 中的 AXI-Lite 寄存器概念；
- 成员盘状态机草图；
- 错误注入和统计计数器清单；
- 重建进度、告警、中断的最小模型。

验收：

- 新人能解释为什么工程样机不仅要能写数据，还要能回读状态、注入故障、定位问题。

状态：已通过 `docs/axis_axi_lite_basics.md` 完成入门展开；成员盘状态机和中断模型仍留作后续。

## Milestone 5：数据面接口入门

目标：理解 8 路 AXIS 输入和 RAID 数据通路之间的关系。

候选产出：

- `docs/axis_axi_lite_basics.md` 中的 AXIS valid/ready 费曼解释；
- 2 路简化 stream ingress Python/RTL 小实验；
- 背压、帧边界、字节有效和错误反馈说明。

验收：

- 能解释为什么“8 路输入”不是简单 for 循环，而涉及仲裁、缓存、限速和统计。

状态：AXIS/背压概念已完成；2 路简化 stream ingress 小实验待做。

## Milestone 6：真实接口调研

目标：决定接真实 NVMe SSD 的工程路线。入口文档：`docs/nvme_host_options.md`。

候选路线：

- 厂商 NVMe/PCIe IP；
- 开源 NVMe Host 参考；
- SoC/CPU 管 NVMe，FPGA 只做 RAID/数据面；
- PCIe DMA + 主机模拟盘；
- DDR/BRAM 继续做算法验证。

验收：

- 给出方案取舍：开发量、风险、性能、可验证性、授权/成本；
- 给出进入真实 NVMe 前的评审清单，明确何时继续停留在抽象 disk port。

状态：已完成入门路线对比和真实 NVMe 前评审清单；真实 IP/板级方案仍需结合器件、预算和验收环境继续评估。


## Milestone 7：验收视角和证据链

目标：把《固存样机技术要求》里的验收压力翻译成教程自测、调研问题和后续工程证据链。

产出：

- `docs/acceptance_checklist.md`
- README 中的“读完你应该能回答什么”
- TODO 中的验收清单任务闭环

验收：

- 能区分“教程小实验能证明什么”和“工程样机验收还要补什么”；
- 能把 RAID 功能、20/40Gbps 性能、72 小时稳定性、错误注入、资料追踪映射到后续测试证据；
- 不把 Python/RTL 小 demo 误称为板级验收通过。

状态：已完成第一版验收清单；后续可继续细化为测试用例模板。


## Milestone 8：控制面寄存器草案

目标：把技术要求里的 AXI-Lite、状态回读、故障注入、重建进度、告警和遥测刷新周期，翻译成学习阶段能理解的寄存器地图。

产出：

- `docs/control_plane_registers.md`
- README 和费曼学习路径中的控制面入口
- TODO 中的后续 `register_model` 教学 demo 任务

验收：

- 能说清 AXIS 数据面和 AXI-Lite 控制面的分工；
- 能列出最小寄存器组：版本、全局控制、阵列模式、成员盘、错误注入、IRQ、rebuild、scrub、遥测；
- 能解释为什么成员盘状态不能只有 good/bad；
- 能解释 rebuild 和 scrub 的区别；
- 明确当前只是前期调研和寄存器草案，不冒充完整 AXI-Lite 从设备或板级验收。

状态：已完成第一版控制面寄存器草案；后续可做 Python register shadow model。
