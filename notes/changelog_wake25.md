# Changelog - Wake 25

## 阶段

第 25 次唤醒：改进阶段。

本轮针对 `notes/inspection_wake24.md` 的 P0/P1 问题做一个小闭环：补上 Python golden model 到第一批 RTL 小模块之间的架构桥，避免读者从 Level 5 突然跳到空的 `rtl/` 目录。

## 本轮做了什么

1. 新增 `docs/fpga_architecture.md`：
   - 明确第一阶段不直接做完整 FPGA RAID 控制器；
   - 明确暂不碰 SATA / NVMe / PCIe / DMA / 驱动 / 掉电恢复；
   - 给出最小数据路径：`lba_mapper -> stripe_manager -> xor/parity_engine -> virtual disk ports`；
   - 建立 Python 到 RTL 的映射表；
   - 明确首批 RTL 顺序：`xor_engine`、`lba_mapper`、`stripe_manager`、`sim/` 对拍。

2. 更新 `README.md`：
   - 在主路线中加入“FPGA 架构边界”；
   - 在可运行入口加入 `docs/fpga_architecture.md`；
   - 在通关路线中加入 Step 9：看 FPGA 架构边界；
   - 保留 Python demo 与 pytest 验证命令。

3. 更新 `TODO.md`：
   - 新增 `Next：Level 1 RTL 前置架构`；
   - 标记架构桥已完成；
   - 把下一个实质任务收敛为创建 `rtl/xor_engine/`，而不是直接做完整 RAID 控制器。

## 修改了哪些文件

- `docs/fpga_architecture.md`
- `README.md`
- `TODO.md`
- `notes/changelog_wake25.md`

## 如何验证

从仓库根目录执行：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```

实测结果：

```text
12 passed in 0.05s
```

同时用脚本检查了 README / TODO / docs 下的本地 Markdown 链接，当前检查到的链接均存在，包括：

- `docs/fpga_architecture.md`
- `docs/rebuild_and_scrub.md`
- `labs/level0_python_model/`
- `docs/raid_basics.md` 中指向模型和测试的链接

## 发现了什么问题

本轮已修复第 24 轮指出的最大断点：`docs/fpga_architecture.md` 缺失。

仍然“不够出色”的点：

1. `rtl/xor_engine/` 还不存在。现在读者知道下一步该做什么，但还不能运行第一个 RTL 小实验。
2. `docs/fpga_architecture.md` 只定义了模块边界和验收思路，还没有 test vector 文件格式约定。
3. 仓库还没有声明推荐仿真工具：Icarus Verilog、Verilator、厂商仿真器三者的取舍尚未定。
4. `TODO.md` 中 `rtl/xor_engine` 同时出现在 Next 和 Later，含义可以接受：Next 是立刻创建闭环，Later 是长期 RTL 小实验列表；但下一轮实现后最好消重或改成更细粒度。

## 下轮建议做什么

第 26 次唤醒应进入检验阶段。

建议从“第一次准备写 RTL 的读者 + 仿真测试工程师”视角检验：

1. `docs/fpga_architecture.md` 是否足够指导创建 `rtl/xor_engine/`；
2. 是否需要先确定 Verilog/SystemVerilog 和仿真工具；
3. `xor_engine` 的最小接口是否应该采用纯组合、valid/ready，还是先两者都不做；
4. Python test vector 应该放在 `sim/vectors/` 还是 `rtl/xor_engine/` 内；
5. README 的 Step 9/Step 10 顺序是否适合新读者。

如果检验通过，下一次改进建议只做一个小闭环：创建 `rtl/xor_engine/README.md` + 最小 RTL + Python 生成向量 + 仿真说明，不急着做 `lba_mapper`。
