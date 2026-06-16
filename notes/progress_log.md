# Progress Log

## 2026-06-16 - Wake 1 / Create

本轮小闭环：建立 Level 0 Python RAID 模型。

- 新增 `TODO.md`，把近期任务拆成 Now / Next / Later。
- 新增 `labs/level0_python_model/raid_model.py`：VirtualDisk、RAID0、RAID1、RAID5。
- 新增 `labs/level0_python_model/test_raid_model.py`：覆盖虚拟盘、XOR、RAID0、RAID1、RAID5 降级读和重建。
- 新增 `labs/level0_python_model/README.md`：说明如何运行与当前边界。
- 新增 `notes/decision_log.md`：记录本轮边界与待决策项。

## Wake 3 - Level 0 可读性与可维护性改进

- 新增 `.gitignore`，忽略 Python 缓存、pytest 缓存、虚拟环境和编辑器噪声。
- 固化 Wake 2 的 RAID5 边界探针，并补 RAID0 坏盘测试。
- 新增 `labs/level0_python_model/demo_layout.py`，用 ASCII 表展示 RAID0/1/5 布局。
- 更新 Level 0 README，补 demo 入口和 degraded write 边界。


## Wake 5 - RAID 基础桥接页

- 新增 `docs/raid_basics.md`，用容量、性能、可用性解释 RAID 的目标。
- 用表格对比 RAID0/1/5 的优点、代价和 Level 0 对应实验。
- 在主 README 增加 `docs/raid_basics.md` 和 demo/pytest 直接运行入口。
- 更新 TODO，标记 RAID basics 文档完成。


## Wake 7 - RAID0 映射页

- 新增 `docs/raid0_mapping.md`，把 `disk_index = lba % disk_count` 和 `disk_lba = lba // disk_count` 讲清楚。
- 补 3 盘 LBA 0~8 映射表、stripe/chunk/disk_lba 解释、坏 `disk1` 后不可读 LBA 表。
- 主 README 增加 RAID0 映射页入口，并把当前入口整理成闯关步骤。
- 更新 TODO，标记 RAID0 映射文档完成。


## Wake 9 - RAID1 镜像页

- 新增 `docs/raid1_mirror.md`，讲清 RAID1 的“复制数据”直觉。
- 补双盘 LBA 0~3 镜像表、写路径 fanout、读路径健康盘选择、容量代价。
- README 增加 RAID1 入口，并把当前通关路线扩展成 Step 0~5。
- 更新 TODO，标记 RAID1 镜像文档完成。


## Wake 11 - RAID5 parity 页

- 新增 `docs/raid5_parity.md`，把 RAID5 讲成“条带化 + XOR 校验”。
- 补 byte 级 XOR 手算例子、4 盘轮转 parity 表、LBA 映射表、degraded read 和 rebuild 直觉。
- README 增加 RAID5 parity 入口，并把当前通关路线扩展成 Step 0~6。
- 更新 TODO，标记 RAID5 parity 文档完成。


## Wake 13 - RAID5 write path 页

- 新增 `docs/raid5_write_path.md`，解释 full-stripe write、read-modify-write、reconstruct write。
- README 增加 write path 入口，并把通关路线扩展成 Step 0~7。
- TODO 标记 RAID5 write path 完成，新增 write hole / rebuild_and_scrub / degraded demo 后续任务。
- 新增 `notes/changelog_wake13.md`。


## Wake 51 / Budget Closeout - RTL stripe_manager 草案收口

本阶段目标：把仓库推进到“Python RAID 模型 + RAID5 知识文档 + 第一批 RTL 小实验”可持续迭代状态。

关键成果：

- Level 0 Python model 已成型：`VirtualDisk`、RAID0、RAID1、RAID5，覆盖 full-stripe write、degraded read、rebuild、scrub/write-hole 演示。
- 文档路线已成型：RAID basics、RAID0 mapping、RAID1 mirror、RAID5 parity、RAID5 write path、write hole、rebuild/scrub、FPGA architecture、references。
- RTL 小实验已启动：
  - `rtl/xor_engine/`：参数化 XOR 组合模块、vector、testbench、runner；
  - `rtl/lba_mapper/`：RAID0 LBA -> disk/chunk 组合模块、testbench、参数矩阵；
  - `rtl/stripe_manager/README.md`：RAID5 full-stripe per-disk action 接口草案，包含 action 编码、Verilog-2001 packed bus 接口、`write_valid`/`data_count` 输出规则、DISK_COUNT=3/4 示例。
- 进度记录已按 wake 保留：`notes/changelog_wake*.md` 与 `notes/inspection_wake*.md`。

最近验证结果：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest labs/level0_python_model/test_raid_model.py -q
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

通过摘要：

```text
12 passed
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
WAKE51 REGRESSION PASS
```

当前未完成的高优先事项：

1. 第 52 轮建议先检验 `rtl/stripe_manager/README.md`：确认 `action_code[2*d +: 2]` / `data_slot[SLOT_WIDTH*d +: SLOT_WIDTH]` 等写法在当前 Icarus Verilog 工具链中可接受。
2. 再实现 `rtl/stripe_manager/stripe_manager.v` + `run_tests.py` + testbench，只覆盖 full-stripe write、idle、unsupported RMW 三类最小规则。
3. 后续再扩展 `rtl/lba_mapper` 的 RAID5 parity rotation / data slot 映射，不要把它和完整 RAID5 控制器混在一起。
4. `rtl/xor_engine` 的流水线/valid-ready 版本仍未做。
5. `sim/` 仍需未来承接跨模块仿真和 Python golden model 对拍。
