# TODO - FPGA RAID Lab 小任务板

> 原则：每次只推进一个可验证小闭环。先让读者跑起来，再逐步接近工程样机需求。

## Now：对齐《固存样机技术要求》

- [x] 抽取并阅读 `D:\work\2601s\raid\固存样机技术要求.docx`
- [x] 新增 `docs/requirements_alignment.md`：把工程指标翻译成学习地图
- [x] 新增 `docs/feynman_learning_path.md`：用费曼法讲清星载 NVMe RAID 固存
- [x] 更新 `README.md`：把仓库定位从普通 FPGA RAID 教程升级为固存样机前期补课
- [x] 更新 `docs/00_big_picture.md`：加入 8 路输入、AXIS、AXI-Lite、NVMe Host、遥测/重建
- [x] 更新 `docs/fpga_architecture.md`：按数据面/RAID面/控制面/设备面拆分
- [x] 更新 `notes/glossary.md`：补 NVMe、PCIe、AXIS、AXI-Lite、遥测、错误注入等术语

## Done：Level 0 Python 模型

- [x] 建立 `labs/level0_python_model/` 基础实验目录
- [x] 实现 `VirtualDisk`：固定块大小、按 LBA 读写、可模拟故障
- [x] 实现 RAID0：条带映射 + 跨盘读写
- [x] 实现 RAID1：双盘镜像 + 单盘降级读
- [x] 实现 RAID5：轮转校验、full-stripe 写、正常读、单盘降级读、重建
- [x] 增加 pytest 测试，覆盖基础读写、RAID0 坏盘、RAID5 坏盘恢复和 5 盘边界

## Done：RAID 基础文档

- [x] 补 `docs/raid_basics.md`：RAID0/1/5 先解决什么问题
- [x] 补 `docs/raid0_mapping.md`：LBA 到 disk/chunk 的映射图
- [x] 补 `docs/raid1_mirror.md`：镜像、故障切换、容量代价
- [x] 补 `docs/raid5_parity.md`：XOR 校验、轮转 parity、降级读
- [x] 补 `docs/raid5_write_path.md`：full-stripe write、RMW、reconstruct write
- [x] 补 `docs/write_hole.md`：partial write 被打断后为什么危险
- [x] 补 `docs/rebuild_and_scrub.md`：重建、巡检和 parity mismatch

## Done：Level 1 RTL 前置架构

- [x] 补 `docs/fpga_architecture.md`：定义 Python golden model 到第一批 RTL 小模块的桥
- [x] 明确第一阶段不碰完整 NVMe/PCIe，只做算法/控制小闭环
- [x] 创建 `rtl/xor_engine/`：第一块可仿真、可对拍的 RTL 小实验
- [x] 创建 `rtl/lba_mapper/`：RAID0 LBA 映射组合模块 + testbench
- [x] `rtl/README.md`：明确 RTL 小模块目录约定、runner 约定和 `sim/` 分工
- [x] `sim/README.md`：说明当前为空目录的用途和未来跨模块仿真入口

## Next：让工程需求更“可见”

- [x] 补 `docs/axis_axi_lite_basics.md`：解释 AXIS/AXI-Lite 在样机里的角色
- [x] 补 `docs/nvme_host_options.md`：调研 NVMe Host 的实现路线和风险
- [x] 补 `docs/acceptance_checklist.md`：把验收项翻译成教程自测和后续工程证据
- [ ] 补 `docs/control_plane_registers.md`：列出模式、成员盘、错误注入、重建进度寄存器草案
- [ ] 扩展 `rtl/lba_mapper`：加入 RAID5 parity rotation / data slot 映射
- [ ] 实现 `rtl/stripe_manager`：full-stripe write -> per-disk DATA/PARITY action
- [ ] 增加一个简化 2 路 AXIS valid/ready 教学 demo
- [ ] 增加一个 Python `register_model` 教学 demo：模拟 RAID_MODE、ERROR_INJECT 和 IRQ_STATUS

## Questions / Decisions

- [ ] 块大小是否长期用 4 字节演示，还是切到 512B/4KiB 更接近真实盘？
- [x] RTL 第一阶段先用 Verilog-2001 + Icarus Verilog；SystemVerilog 留到接口复杂后再评估。
- [x] 真实 NVMe 接入倾向自研、厂商 IP、开源参考，还是 SoC/CPU 协同？先完成路线对比，工程选型待板卡/IP/预算确认。
- [x] 工程样机教程是否需要单独建立“验收清单”文档？已新增 `docs/acceptance_checklist.md`。
