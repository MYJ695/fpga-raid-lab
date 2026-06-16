# Inspection - Wake 48

## 阶段

第 48 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake47.md`，用“测试工程师 + 初学读者”双重视角检查第 47 轮补强后的路线桥接是否真的成立。

## 本轮做了什么

1. 走读根 `README.md` 的 Step 0~13 和当前可运行入口。
2. 走读 `rtl/README.md`、`rtl/xor_engine/README.md`、`rtl/lba_mapper/README.md`，检查模块契约是否被实际子目录满足。
3. 走读 `sim/README.md`，检查它是否会误导读者以为已有跨模块仿真。
4. 结合 `docs/fpga_architecture.md` 与 Python/RTL 映射代码，判断下一步是否适合开始定义 `rtl/stripe_manager/README.md`。
5. 实跑 README 中的主要 Python demo、pytest 和 RTL runner，确认文档路线不是纸面路线。

## 检验对象

- `README.md`
- `TODO.md`
- `docs/fpga_architecture.md`
- `sim/README.md`
- `rtl/README.md`
- `rtl/xor_engine/README.md`
- `rtl/lba_mapper/README.md`
- `rtl/lba_mapper/lba_mapper.v`
- `labs/level0_python_model/raid_model.py`

## 如何验证

已从仓库根目录执行：

```bash
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果摘要：

```text
12 passed in 0.05s
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
ALL README COMMANDS PASS
residue []
```

说明：当前 README 推荐的 Python 行为入口、pytest golden reference、两个 RTL 单模块 runner 均可运行；运行后未留下 `.vvp/.vcd` 临时产物。

## 检验结果

### 1. 根 README：Step 7~13 与实际命令顺序一致

第 47 轮补上的三段分工有效：

```text
Python demo -> pytest golden reference -> RTL runner/testbench 对拍
```

从初学者视角看，当前路线已经能解释“为什么不是直接写完整 RAID 控制器”：先把 RAID 行为跑出来，再把局部规则硬件化。

本轮未发现命令路径错误。`demo_layout.py`、write hole demo、rebuild/scrub demo、pytest、`xor_engine` runner、`lba_mapper` runner 都能从仓库根目录执行。

### 2. `rtl/README.md` 的最小模块要求基本被满足

`rtl/README.md` 给出的标准是：

```text
一个清晰的 RAID/控制逻辑问题 -> 一个小 RTL 模块 -> 一个能失败的 testbench -> 一条可重复命令
```

对照结果：

| 模块 | 清晰问题 | RTL | testbench/vector | runner | 结论 |
|---|---|---|---|---|---|
| `xor_engine` | 多个 word XOR 成 parity word | 有 | 有 | 有 | 满足 |
| `lba_mapper` | RAID0 LBA -> disk_index + disk_lba | 有 | 有 | 有 | 满足 |
| `stripe_manager` | 请求切分 | 空目录 | 无 | 无 | 只适合作为下一关 |

`xor_engine` 和 `lba_mapper` 已达到“可运行小关卡”要求；`stripe_manager` 仍只是路线占位，不能在 README 中暗示它已可运行。当前 `rtl/README.md` 对此表达是准确的。

### 3. `sim/README.md` 没有误导读者已有跨模块仿真

`sim/README.md` 明确写出：

- `sim/` 现在不是主要入口；
- 当前要跑单模块，应使用：
  - `python rtl/xor_engine/run_tests.py`
  - `python rtl/lba_mapper/run_tests.py`
- 等 `stripe_manager` 或联合对拍出现后，再把总入口收敛到 `sim/`。

这不会误导读者以为已有 `sim/run_all.py` 或跨模块系统仿真。

### 4. 代码与文档的边界有一个重要落差：`lba_mapper` 还只有 RAID0

`docs/fpga_architecture.md` 的长期路线写到：

```text
RAID5.parity_disk() / RAID5.map_lba() -> rtl/lba_mapper RAID5 模式
RAID5.write_full_stripe() -> stripe_manager + xor_engine
```

但当前实际 RTL：

```verilog
assign disk_index   = logical_chunk % DISK_COUNT;
assign stripe_index = logical_chunk / DISK_COUNT;
assign disk_lba     = (stripe_index << CHUNK_SHIFT) + chunk_offset;
```

这仍是 RAID0 风格的条带映射，不包含 RAID5 的 parity rotation / data slot 映射。

因此，从测试工程师视角看：可以开始写 `stripe_manager` 的概念 README，但不建议立刻实现 RTL。原因是 `stripe_manager` 若要服务 RAID5 full-stripe write，需要稳定依赖 RAID5 的 `parity_disk` 与 `data_disk_order` 规则；这些目前还没有在 `rtl/lba_mapper` 中硬件化。

### 5. 不够出色的点

当前项目已经清楚、可跑，但还不够“闯关式”的地方是：

1. `stripe_manager` 目录存在但完全空，读者看到路线第三关时没有“门牌说明”。
2. 下一步在 `lba_mapper` 扩展 RAID5，还是先给 `stripe_manager` 写接口草案，TODO 里没有明确排序。
3. `docs/fpga_architecture.md` 已经定义了 `stripe_manager` 的职责，但 `rtl/stripe_manager/` 下没有 README 把这个职责落成可验收的第一关。

这些不是当前功能错误，但会影响持续扩展：下一位维护者可能直接写过大的 `stripe_manager`，把请求切分、parity rotation、full-stripe write 调度混在一起。

## 发现的问题

本轮没有发现会导致命令失败或文档明显误导的问题。

主要发现是一个“下一关切入点”问题：

> 现在最值得做的小闭环，不是马上写 `stripe_manager.v`，而是先补 `rtl/stripe_manager/README.md`，定义第一版只接受 full-stripe write、只输出 data/parity chunk actions、partial write 明确 unsupported/RMW TODO。

这样既不跳过 `lba_mapper` 的 RAID5 扩展，又能提前防止 `stripe_manager` 失控。

## 下轮建议做什么

第 49 轮进入改进阶段，建议只做一个小闭环：

1. 新增 `rtl/stripe_manager/README.md`，作为第三关门牌；
2. 明确第一版边界：
   - 输入：stripe index + full-stripe data block count；
   - 输出：每个 disk 的 chunk action，其中一个是 parity；
   - partial write 暂不实现，只标为 RMW/reconstruct-write 后续任务；
3. 在 `TODO.md` 中把 `rtl/stripe_manager` 拆成“先写 README/接口草案”和“后写 RTL/testbench”两个任务；
4. 不新增 `stripe_manager.v`，除非 README 已经把可测试输入/输出定义得足够小。

建议继续保持本项目的小闭环节奏：先定义可验收边界，再写可失败测试，最后才写 RTL。
