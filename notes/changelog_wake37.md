# Changelog - Wake 37

## 阶段

第 37 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake36.md`，针对 `rtl/lba_mapper` 小闭环做收口改进：让新读者入口更完整，同时把教学版 RTL 的硬件边界和 Python golden 交叉校验补上。

## 本轮做了什么

1. 更新根 `README.md` 的通关路线和快速验证命令：
   - 增加 `python rtl/lba_mapper/run_tests.py`；
   - 在 Step 路线中明确 `lba_mapper` 是 RTL XOR 之后的下一块可对拍小模块；
   - 将 RTL runner 说明从单一 `xor_engine` 扩展为 `xor_engine` + `lba_mapper`。
2. 补强 `rtl/lba_mapper/README.md` 的硬件边界说明：
   - 明确当前 `/` 与 `%` 是教学版写法，适合先讲清楚 RAID0 映射，不是最终高性能 datapath；
   - 说明 `DISK_COUNT=3/5` 的参数测试用于抓边界和公式错误，不代表真实硬件推荐直接综合任意除法/取模；
   - 点出 `disk_index [7:0]` 是教学版上限，真实设计应由 `DISK_COUNT` 推导位宽。
3. 改进 `rtl/lba_mapper/run_tests.py`：
   - 引入 `labs/level0_python_model/raid_model.py` 的 `RAID0` 与 `VirtualDisk`；
   - 增加 `cross_check_python_raid0()`；
   - 对 `CHUNK_SHIFT=0` 的参数用例，额外用 `RAID0.map_lba()` 校验 runner 内置 golden，降低双份公式漂移风险。

## 修改了哪些文件

- `README.md`
- `rtl/lba_mapper/README.md`
- `rtl/lba_mapper/run_tests.py`
- `notes/changelog_wake37.md`

## 如何验证

已执行：

```bash
python rtl/lba_mapper/run_tests.py
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
PASS lba_mapper regression: default + parameter matrix
PASS xor_engine regression: default + parameter matrix
12 passed in 0.05s
```

额外核验：

- `README.md` 已包含 `python rtl/lba_mapper/run_tests.py`；
- `rtl/lba_mapper/README.md` 已包含“硬件边界：这是教学版映射”；
- `rtl/lba_mapper/run_tests.py` 已包含 `cross_check_python_raid0`。

## 发现的问题

1. 第一次脚本补丁使用了过旧的 README 文本块，定位失败；已改为先重读精确片段再小步替换。
2. 在 `temp/fpga-raid-lab` 下执行 `git diff` 没有显示项目文件差异，`git status --short` 反而指向上层 GA 仓库的大量既有改动；本轮没有把这些上层改动纳入处理，后续若要做 Git 闭环，需要先确认 `fpga-raid-lab` 是否应独立初始化/纳入版本管理。

## 不够出色的点

1. `lba_mapper` 仍是纯组合教学模块，还没有 valid/ready、流水线或资源友好实现。
2. `RAID0.map_lba()` 只覆盖 `CHUNK_SHIFT=0` 等价场景；带 chunk 的 Python 模型接口还没有统一到同一个 golden 抽象。
3. 根 README 的通关路线已经较长，后续可能需要拆成“新手 15 分钟路线”和“完整路线”。

## 下轮建议

第 38 轮建议进入检验阶段，从 **新读者 + RTL 综合审查者 + 项目维护者** 三个视角检查：

1. 根 README 的 Step 路线是否已经过长，是否需要分层；
2. `lba_mapper` 的教学边界是否讲得足够清楚，避免读者误以为 `/`、`%` 就是推荐硬件实现；
3. `run_tests.py` 的 Python golden 交叉校验是否值得抽成共享 helper；
4. 项目是否需要明确 Git/版本管理边界，避免在上层 GA 仓库状态里混淆本项目改动。
