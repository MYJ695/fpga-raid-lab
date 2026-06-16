# Changelog - Wake 35

## 阶段

第 35 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake34.md`，把 `rtl/lba_mapper` 从“只有下一步说明”推进为一个可运行的 RAID0 LBA 映射 RTL 小闭环。

## 本轮做了什么

1. 补齐 `rtl/lba_mapper/README.md`：
   - 明确第一版 RTL 只做 `RAID0 logical block address -> disk_index + disk_lba`；
   - 写出 module 参数、端口和输出含义；
   - 明确 `DISK_COUNT`、`CHUNK_SHIFT` 第一版都用 Verilog parameter 固定；
   - 增加 `DISK_COUNT=3, CHUNK_SHIFT=2` 的逐 LBA 边界表，专门抓 chunk 边界和 `disk_lba` offset 错误。
2. 新增可仿真的 RTL 小模块：
   - `rtl/lba_mapper/lba_mapper.v`：纯组合逻辑，无 clock/reset/handshake；
   - `rtl/lba_mapper/tb_lba_mapper.v`：读取默认 vector 并检查 `disk_index/stripe_index/disk_lba`；
   - `rtl/lba_mapper/run_tests.py`：生成默认 vector，调用 Icarus Verilog，并临时生成参数化 testbench。
3. 更新路线入口：
   - 根 `README.md` 增加运行 `lba_mapper` 的 Step；
   - `rtl/README.md` 更新 `lba_mapper` 状态；
   - `TODO.md` 勾选 `rtl/lba_mapper` 基础映射组合模块 + testbench。

## 修改了哪些文件

- `README.md`
- `TODO.md`
- `rtl/README.md`
- `rtl/lba_mapper/README.md`
- `rtl/lba_mapper/lba_mapper.v`
- `rtl/lba_mapper/tb_lba_mapper.v`
- `rtl/lba_mapper/run_tests.py`
- `rtl/lba_mapper/vectors.txt`
- `notes/changelog_wake35.md`

## 如何验证

已执行：

```bash
python rtl/lba_mapper/run_tests.py
python -m pytest labs/level0_python_model -q
```

结果：

```text
PASS lba_mapper regression: default + parameter matrix
12 passed in 0.05s
```

`run_tests.py` 覆盖：

- 默认固定 testbench：`DISK_COUNT=4, CHUNK_SHIFT=0`，20 个 case；
- 参数化临时 testbench：`DISK_COUNT=3, CHUNK_SHIFT=2`，21 个 case；
- 参数化临时 testbench：`DISK_COUNT=5, CHUNK_SHIFT=0`，19 个 case。

## 发现的问题

初版曾用 `CHUNK_MASK` localparam 计算 `chunk_offset`，在 `CHUNK_SHIFT=2` 的参数测试中暴露为 `chunk_offset` 恒为 0，导致 `disk_lba` 在 chunk 内偏移丢失。

已修正为：

```verilog
assign chunk_offset = lba - (logical_chunk << CHUNK_SHIFT);
```

这样既避开了 mask 位宽表达式的坑，也更直观地表达了“当前 LBA 减去 chunk 起点”。

## 不够出色的点

1. `lba_mapper` 现在仍使用 `%` 和 `/`，学习上清晰，但综合到真实硬件时会引入除法/取模代价；后续需要在文档里说明 power-of-two disk count 或查表/减法策略。
2. 当前只对拍到 Python runner 内置 golden，还没有直接调用 `labs/level0_python_model/raid_model.py` 的 `RAID0.map_lba()`，未来可减少双份公式漂移。
3. `sim/` 还没有统一入口，等 `lba_mapper` 稳定后可考虑 `sim/run_all.py` 汇总 RTL 回归。

## 下轮建议

第 36 轮进入检验阶段，建议从 **硬件综合/RTL 代码审查者** 视角检验：

1. `lba_mapper.v` 的 `/`、`%` 是否应该在 README 中标注“教学版，非最终高性能实现”；
2. `DISK_COUNT` 非 2 的幂时，端口宽度和综合代价是否讲清楚；
3. `run_tests.py` 是否应直接复用 Python 模型，避免公式复制；
4. 根 README 的闯关路线是否因为新增 Step 过长，需要重排 Level 1 小节。
