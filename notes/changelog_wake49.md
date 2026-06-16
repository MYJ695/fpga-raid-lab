# Changelog - Wake 49

## 阶段

第 49 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake48.md`，只做一个小闭环：给第三个 RTL 关卡 `stripe_manager` 补上 README 门牌，先定义 RAID5 full-stripe write 的动作边界，不急着写 RTL。

## 本轮做了什么

1. 新增 `rtl/stripe_manager/README.md`：
   - 明确 `stripe_manager` 不负责 XOR、不负责真实磁盘协议；
   - 第一版只把一个 RAID5 full-stripe write 拆成每块盘的 `DATA / PARITY / IDLE` action；
   - 对齐 Python 模型里的 `RAID5.parity_disk(stripe)`、`RAID5.data_disk_order(stripe)`、`RAID5.layout_row(stripe)`；
   - 明确 partial write、RMW、reconstruct-write、degraded write、AXI/valid-ready 都暂不做。
2. 更新 `TODO.md`：
   - 把原来的 `rtl/stripe_manager` 大任务拆成三个更小任务：
     1. README/接口草案；
     2. full-stripe write -> per-disk DATA/PARITY action 的 RTL/testbench；
     3. 后续 partial write 的 RMW/reconstruct-write 标记。
3. 更新 `rtl/README.md`：
   - 把 `stripe_manager` 状态从“目录预留”改成“已有 README 接口草案”；
   - 下一步收敛为 full-stripe write action testbench。

## 修改了哪些文件

- `rtl/stripe_manager/README.md`
- `TODO.md`
- `rtl/README.md`
- `notes/changelog_wake49.md`

## 如何验证

### 1. 读回检查

已读回确认：

- `rtl/stripe_manager/README.md` 内容完整，包含核心结论、第一版范围、输入、输出、明确不做、未来验收标准；
- `TODO.md` 中 `stripe_manager` 已拆成小任务；
- `rtl/README.md` 当前关卡表已更新。

### 2. 回归命令

第一次验证时误用了不存在的测试目录：

```bash
python -m pytest labs/level0_python_model/tests -q
```

探测后确认当前测试文件实际是：

```text
labs/level0_python_model/test_raid_model.py
```

随后重跑完整基础回归：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest labs/level0_python_model/test_raid_model.py -q
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果：

```text
12 passed in 0.05s
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
WAKE49 REGRESSION PASS
```

## 发现了什么问题

1. 项目当前 pytest 入口是单文件 `labs/level0_python_model/test_raid_model.py`，不是 `labs/level0_python_model/tests/` 目录。
2. `stripe_manager` 的 README 现在已经把边界定义清楚，但还没有可执行 vector/testbench。
3. `lba_mapper` 仍停留在 RAID0 RTL 映射；因此 `stripe_manager` 下一步适合先写动作表 testbench，而不是直接接入完整 RAID5 LBA mapper。

## 下轮建议做什么

第 50 轮进入检验阶段。建议换成“RTL testbench 作者 + 挑剔初学者”视角检查：

1. `rtl/stripe_manager/README.md` 的输入/输出是否已经足够让人写 testbench；
2. `DATA(slot)` / `PARITY` / `UNSUPPORTED_RMW` 是否需要提前定义成数值编码；
3. `DISK_COUNT=3/4/5` 的示例是否足够，是否需要补一个 `DISK_COUNT=3` 最小表；
4. README 是否会让人误以为已经有 `stripe_manager.v`；
5. 如果下一步写 RTL，最小 Verilog-2001 接口是否应先只输出 `action_code[disk]` 和 `data_slot[disk]`。

建议第 50 轮暂不新增 RTL，先检验这份接口草案是否能自然导出一个小 testbench。
