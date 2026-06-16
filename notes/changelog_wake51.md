# Changelog - Wake 51

## 阶段

第 51 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake50.md`，只做一个小闭环：继续打磨 `rtl/stripe_manager/README.md`，把第 50 轮指出的“能读懂但还不能直接写 testbench”的缺口收敛成可断言的接口草案。

## 本轮做了什么

1. 更新 `rtl/stripe_manager/README.md`：
   - 明确当前状态：本目录只有接口草案，还没有 `stripe_manager.v` RTL 实现；
   - 增加固定 2 bit action 编码：`IDLE=0`、`DATA=1`、`PARITY=2`、`UNSUPPORTED_RMW=3`；
   - 增加最小 Verilog-2001 接口草案，使用 packed bus 输出 `action_code` / `data_slot`，避免一开始引入 SystemVerilog 数组端口；
   - 明确 `write_valid` / `data_count` 三种输出规则；
   - 把 unsupported 场景收敛为单一规则：非 full-stripe write 时所有 disk 输出 `ACTION_UNSUPPORTED_RMW` 且 `unsupported=1`；
   - 补充 `DISK_COUNT=3` 最小 RAID5 action 表；
   - 保留 `DISK_COUNT=4` 示例，并继续要求和 Python `RAID5.layout_row(stripe)` 对拍。

## 修改了哪些文件

- `rtl/stripe_manager/README.md`
- `notes/changelog_wake51.md`

## 如何验证

### 1. 读回检查

已读回确认 `rtl/stripe_manager/README.md` 包含：

- 当前无 RTL 实现的状态说明；
- action 数值编码表；
- packed bus 风格的 Verilog-2001 接口草案；
- `write_valid == 0`、full-stripe write、unsupported RMW 三类规则；
- `DISK_COUNT=3` 与 `DISK_COUNT=4` 示例；
- 未来 testbench 验收标准。

### 2. 基础回归

运行命令：

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
WAKE51 REGRESSION PASS
```

## 发现了什么问题

1. `stripe_manager` 的接口草案已经比第 49 轮更接近可实现状态，但仍然没有真正的 RTL/testbench。
2. README 当前写了 `action_code[2*d +: 2]` 这种 Verilog-2001 常用 part-select 写法；第 52 轮应从工具兼容性视角确认项目当前 `iverilog` 是否接受这种写法。
3. `data_slot` 在非 DATA action 下固定为 `0` 是为了降低教学 testbench 难度；后续若支持多请求调度，可能需要再定义更完整的 valid 语义。
4. `lba_mapper` 仍是 RAID0 映射，不能把 `stripe_manager` 直接接成完整 RAID5 写路径。

## 下轮建议做什么

第 52 轮进入检验阶段，建议换成“RTL 实现者 + Icarus Verilog 工具链”视角检查：

1. `rtl/stripe_manager/README.md` 的接口草案是否能直接导出一个组合逻辑 `stripe_manager.v`；
2. `action_code[2*d +: 2]` / `data_slot[SLOT_WIDTH*d +: SLOT_WIDTH]` 是否符合当前 iverilog 可接受的 Verilog 写法；
3. `DISK_COUNT=3/4/5`、`write_valid=0`、unsupported RMW 的最小 testbench vector 是否已经无歧义；
4. 是否需要在写 RTL 前先补 `rtl/stripe_manager/run_tests.py` 的 vector 生成思路；
5. 继续警惕不要把本模块扩张成完整 RAID5 控制器。
