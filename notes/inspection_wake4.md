# Inspection Report - Wake 4

## 阶段

第 4 次唤醒：检验阶段。

本轮目标是检查第 3 次唤醒的改进是否真正提高了 Level 0 的可运行性、可读性和可维护性；不对交付物做实质改写。

## 检验方法

### 1. 新读者实测路径

按 README/Level 0 README 的入口做了两种运行：

```bash
python -m pytest -q labs/level0_python_model
cd labs/level0_python_model
python -m pytest -q
python demo_layout.py
```

结果：

```text
12 passed
12 passed
```

`demo_layout.py` 能成功输出 RAID0、RAID1、RAID5 的 ASCII 布局表。

结论：基础运行路径可用，新读者不会卡在路径或 import 问题上。

### 2. 测试工程师视角

第 3 轮把测试从 7 个扩到 12 个，新增覆盖点包括：

- RAID0 成员盘故障后，对应数据不可读；
- RAID5 parity disk 故障时，数据盘读取仍可工作；
- RAID5 parity disk 重建后，读回数据一致；
- 5 盘 RAID5 的轮转 parity、降级读、重建；
- full-stripe write 遇到 failed disk 时明确失败。

结论：Level 0 当前宣称的能力与测试基本对齐，核心边界比第 2 轮更稳。

### 3. 初学读者视角

优点：

- Level 0 README 先讲“映射、冗余、恢复”，入口清楚；
- demo 的 ASCII 表比纯 pytest 更像学习实验；
- README 明确说明了 RAID0/1/5 当前边界，避免读者误以为这是完整 RAID 实现。

不够出色：

- demo 目前只展示静态布局，没有演示“坏一块盘后，RAID5 如何用 XOR 把缺失块算回来”；
- `demo_layout.py` 的输出更像速查表，还不像“闯关式实验室”的引导；
- 主 README 只链接了 Level 0 目录，没有直接提示可以运行 `demo_layout.py`。

### 4. 工程卫生视角

`.gitignore` 已覆盖：

- `__pycache__/`；
- `*.py[cod]`；
- `.pytest_cache/`；
- 常见虚拟环境和编辑器噪声。

运行测试会临时生成 `__pycache__/`，本轮检验后已清理。当前没有发现缓存目录残留。

结论：够用且不过度。

### 5. 对照 objective 的主线检验

Objective 的优先顺序是：

1. TODO；
2. Level 0 Python 模型；
3. 补 docs/raid_basics.md、raid0_mapping.md、raid1_mirror.md、raid5_parity.md 等文档；
4. RTL 小实验；
5. references。

当前状态：

- TODO 已有；
- Level 0 Python 模型已有且 12 测通过；
- `docs/raid_basics.md`、`docs/raid0_mapping.md`、`docs/raid1_mirror.md`、`docs/raid5_parity.md` 等目标文档仍缺失。

结论：下一轮应该从 Level 0 继续自然过渡到文档层，优先补 `docs/raid_basics.md`，而不是继续堆测试。

## 及格线判断

通过。

- 无路径错误；
- pytest 通过；
- demo 可运行；
- 缓存已清理；
- 第 3 轮没有把进度报告混入交付物文档。

## 不够出色的点

1. **缺少 RAID5 降级读取的可视化演示**  
   读者能看到 parity 轮转，但还看不到 XOR 恢复过程。

2. **主 README 的运行入口还可以更主动**  
   当前只链接 Level 0 目录，没有直接告诉读者“先跑 demo，再跑 pytest”。

3. **文档层仍为空档**  
   Objective 明确列出的 `docs/raid_basics.md` 等还没开始，读者从 demo 到 RAID 概念之间缺一页解释。

4. **测试仍偏行为正确，少了教学型断言**  
   例如没有直接断言 RAID5 某个 stripe 的 parity 位置和 LBA 映射公式，虽然 demo 展示了布局。

## 下一轮建议

第 5 次唤醒应进入改进阶段。建议做一个小闭环，不要大规模补齐所有文档：

> 新增 `docs/raid_basics.md`，并让主 README / TODO 指向它。

建议内容：

1. 用一页金字塔结构解释 RAID 解决的问题：容量、性能、可用性；
2. 简述 RAID0/1/5 的核心 trade-off；
3. 放一张小表把 RAID0/1/5 和 Level 0 Python 模型对应起来；
4. 引导读者下一步运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

可选小改进：在主 README 的“当前可运行入口”补一行 demo 命令。

不建议下一轮做 RTL 或 RAID6，因为 Level 0 到文档解释之间的桥还没搭好。
