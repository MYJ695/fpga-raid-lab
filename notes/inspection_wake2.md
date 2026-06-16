# Inspection Report - Wake 2

## 阶段

第 2 次唤醒：检验阶段。

本轮不重写交付物，只从多个视角检查第 1 次唤醒产物，并记录下一轮改进目标。

## 检验视角

### 1. 测试工程师视角

已重新执行基础测试：

```bash
python -m pytest -q labs/level0_python_model
```

结果：

```text
7 passed
```

另外临时设计了未写入仓库的更难探针：

- RAID5 parity disk 故障后，正常数据盘读取仍应成功；
- RAID5 rebuild parity disk 后，校验块应恢复为原值；
- 5 盘 RAID5 的布局、降级读、重建应保持正确；
- full-stripe write 写到 failed disk 时应明确失败。

探针结果：全部通过。

### 2. 初学读者视角

及格点：

- `README.md` 已能看到当前可运行入口；
- `labs/level0_python_model/README.md` 说明了如何运行测试；
- 代码命名直接，`VirtualDisk` / `RAID0` / `RAID1` / `RAID5` 容易理解。

不够出色的点：

- Level 0 README 仍偏“说明书”，还没有直观展示 stripe / parity 布局；
- 没有一个 `demo_layout.py` 之类的脚本让读者直接看到 RAID0/1/5 的映射表；
- README 的通关地图说 Level 0 是“RAID 世界观”，但当前 `labs/level0_python_model` 实际已经包含 RAID0/1/5，分关卡叙事还可以更清楚。

### 3. 代码质量视角

及格点：

- 模型边界清楚：固定块大小、RAID5 full-stripe write、单盘故障；
- RAID5 轮转 parity、降级读、重建逻辑在基础和额外探针中均通过；
- `layout_row()` 对后续文档图解有复用价值。

不够出色的点：

- 测试文件没有覆盖 parity disk 故障和 5 盘阵列，虽然临时探针通过，但应固化为回归测试；
- `RAID0` 缺少明确测试：任意一盘故障后读对应块应失败，强调 RAID0 无冗余；
- `RAID1.write()` 当前如果某个镜像盘 failed，会整体抛错。作为教学模型可以接受，但 README 应说明“本模型不模拟 degraded write”。

### 4. 工程卫生视角

发现问题：

- 仓库没有 `.gitignore`；
- 运行 pytest 后产生了 `labs/level0_python_model/__pycache__/` 和 `.pyc` 文件；
- 没有 `requirements.txt` 或 `pyproject.toml`，读者需要从 README 中知道 pytest 依赖。

这不是算法正确性问题，但会影响项目可持续维护。

## 结论

第 1 轮产物达到及格线：可运行、测试通过、范围符合目标、没有发现 RAID5 核心逻辑错误。

但要变成“有趣、清晰、可持续扩展”的学习实验室，下一轮不应急着扩写大文档，而应做一个小而实的改进闭环：

1. 增加 `.gitignore` 并清理 Python 缓存；
2. 把本轮临时 RAID5 边界探针固化进 pytest；
3. 增加一个可视化/演示脚本，让读者直观看到 RAID0/1/5 布局；
4. 在 Level 0 README 中补充运行 demo 的方式和 degraded write 边界。

## 下一轮建议

第 3 次唤醒应进入改进阶段，建议只做一个小闭环：

> “提升 Level 0 的可维护性和可读性”：`.gitignore` + 更强测试 + ASCII 布局 demo + README 小幅说明。

不要在下一轮同时大规模补 `docs/raid_basics.md` 等文档，以免超过“小闭环”。
