# TODO - FPGA RAID Lab 小任务板

> 原则：每次只推进一个可验证小闭环。先让读者跑起来，再逐步接近 RTL 和真实接口。

## Now：Level 0 Python 模型

- [x] 建立 `labs/level0_python_model/` 基础实验目录
- [x] 实现 `VirtualDisk`：固定块大小、按 LBA 读写、可模拟故障
- [x] 实现 RAID0：条带映射 + 跨盘读写
- [x] 实现 RAID1：双盘镜像 + 单盘降级读
- [x] 实现 RAID5：轮转校验、full-stripe 写、正常读、单盘降级读、重建
- [x] 增加 pytest 测试，覆盖基础读写、RAID0 坏盘、RAID5 坏盘恢复和 5 盘边界

## Next：把 Level 0 讲清楚

- [x] 补 `docs/raid_basics.md`：RAID0/1/5 先解决什么问题
- [x] 补 `docs/raid0_mapping.md`：LBA 到 disk/chunk 的映射图
- [x] 补 `docs/raid1_mirror.md`：镜像、故障切换、容量代价
- [x] 补 `docs/raid5_parity.md`：XOR 校验、轮转 parity、降级读
- [x] 补 `docs/raid5_write_path.md`：full-stripe write、RMW、reconstruct write
- [x] 给 Level 0 增加一个 ASCII 可视化脚本，打印 stripe 布局

## Next：RAID5 可靠性与维护

- [x] 补 `docs/write_hole.md`：partial write 被打断后为什么危险
- [x] 增加 `demo_write_hole.py`：跑出正常读隐藏错误、降级恢复暴露错误
- [x] 补 `docs/rebuild_and_scrub.md`：重建、巡检和 parity mismatch
- [x] 增加 `demo_rebuild_and_scrub.py`：打印 scrub mismatch 和 rebuild 写回风险

## Next：Level 1 RTL 前置架构

- [x] 补 `docs/fpga_architecture.md`：定义 Python golden model 到第一批 RTL 小模块的桥
- [x] 明确第一阶段不碰 SATA/NVMe/PCIe，只做算法/控制小闭环
- [x] 创建 `rtl/xor_engine/`：第一块可仿真、可对拍的 RTL 小实验

## Later：RTL 小实验

- [x] `rtl/README.md`：明确 RTL 小模块目录约定、runner 约定和 `sim/` 分工
- [x] `rtl/xor_engine`：参数化 XOR 组合版本 + Python vector + Icarus testbench
- [ ] `rtl/xor_engine`：流水线/valid-ready 版本
- [x] `rtl/lba_mapper/README.md`：先定义 RAID0 LBA -> disk/chunk 的最小边界
- [x] `rtl/lba_mapper`：实现 RAID0 基础映射组合模块 + testbench
- [ ] `rtl/lba_mapper`：扩展 RAID5 parity rotation / data slot 映射
- [x] `rtl/stripe_manager/README.md`：定义 RAID5 full-stripe write 的第一版动作边界
- [ ] `rtl/stripe_manager`：实现 full-stripe write -> per-disk DATA/PARITY action 的 RTL/testbench
- [ ] `rtl/stripe_manager`：后续扩展 partial write 的 RMW/reconstruct-write 标记
- [x] `sim/README.md`：说明当前为空目录的用途和未来跨模块仿真入口
- [ ] `sim/`：记录 Icarus/Verilator 仿真命令，和 Python golden model 对拍

## Questions / Decisions

- [ ] 块大小是否长期用 4 字节演示，还是切到 512B/4KiB 更接近真实盘？
- [x] RTL 第一阶段先用 Verilog-2001 + Icarus Verilog；SystemVerilog 留到接口复杂后再评估。
