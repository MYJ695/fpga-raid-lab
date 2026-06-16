# Inspection Report - Wake 6

## 阶段

第 6 次唤醒：检验阶段。

本轮检验第 5 次唤醒新增的 `docs/raid_basics.md` 以及主 README 入口。原则是不改交付物，只记录问题和下一轮改进目标。

## 检验方法

### 1. 新读者路径实测

从仓库根目录执行 README 推荐命令：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
demo exit 0
12 passed
```

结论：主 README 的“先看布局，再跑测试”路径可用。

### 2. Markdown 链接与表格格式检查

检查对象：

- `README.md`
- `docs/raid_basics.md`

结果：

- `README.md` 中的 `TODO.md`、`docs/raid_basics.md`、`labs/level0_python_model/` 均存在；
- `docs/raid_basics.md` 中指向 Level 0 README、模型、测试的相对链接均存在；
- Markdown 表格列数一致，未发现明显渲染错位风险。

### 3. 概念准确性核对

对照当前 Python 模型检查了关键说法：

- RAID0 映射确实是 `disk = lba % disk_count`，`disk_lba = lba // disk_count`；
- RAID1 确实写入所有镜像盘，读取任一健康盘；
- RAID5 确实是每个 stripe 有 `N-1` 个数据块和 1 个 parity 块；
- 当前模型 parity disk 为 `stripe % disk_count`，与文档中的轮转 parity 示例一致；
- RAID5 degraded read 依靠 XOR 重构单个缺失块，与文档表述一致；
- 当前模型只支持 full-stripe write，不覆盖 partial write / write hole，与文档边界一致。

结论：没有发现明显事实错误。

## 及格线判断

第 5 次改进达到及格线：

1. 新读者能从主 README 找到当前入口；
2. `docs/raid_basics.md` 能解释 RAID0/1/5 的基本动机和取舍；
3. 文档没有把未实现能力伪装成已实现能力；
4. 命令可运行，测试通过；
5. 链接和表格格式可用。

## 不够出色的点

### 1. `raid_basics.md` 讲“是什么”，还没讲“怎么算”

目前文档足够作为世界观入口，但对懂 FPGA 的读者来说，下一步最自然的问题是：

```text
给我一个 LBA，我到底怎么算出 disk/chunk？
```

这正好对应 `docs/raid0_mapping.md`。如果缺少这一页，读者从概念跳到 Python 代码时仍需要自己反推映射公式。

### 2. RAID5 降级读取仍缺少可视化

`docs/raid_basics.md` 已经讲了 XOR parity 的性质，但 `demo_layout.py` 只展示静态布局。读者还看不到：

```text
disk2 坏了
D1 = P xor D0 xor D2
```

这会影响“闯关式实验室”的趣味性。

### 3. 主 README 的路线仍偏宏观

README 已经有可运行入口，但还没有形成明确闯关动作：

```text
Step 0: 看 RAID Basics
Step 1: 跑 demo
Step 2: 跑 pytest
Step 3: 打开 raid_model.py 看 map_lba
```

下一轮如果只补 `raid0_mapping.md`，最好顺手让 README/TODO 指向这条更明确的学习路线。

### 4. RAID0 的教学价值被低估了

RAID0 没有冗余，看似简单，但它是后续 RAID5 映射、stripe、chunk、并行访问的地基。现在仓库已经有代码和测试，但文档还没把这个地基讲透。

## 下一轮建议

第 7 次唤醒应进入改进阶段。建议做一个小闭环：

> 新增 `docs/raid0_mapping.md`，把 LBA 到 disk/chunk 的映射讲清楚，并在 README / TODO 中接上入口。

建议内容：

1. 用金字塔结构先给公式：

```text
disk_index = lba % disk_count
disk_lba   = lba // disk_count
```

2. 给 3 块盘、LBA 0~8 的表格；
3. 解释 stripe、chunk、disk_lba 的关系；
4. 对应到 `RAID0.map_lba()`；
5. 加一个“坏 disk1 后哪些 LBA 不可读”的小表，为后续 RAID5 degraded read 铺路。

不建议第 7 轮优先做 RAID5 降级 demo。原因：当前概念链条还缺 RAID0 映射页；先把条带化讲清楚，再做 RAID5 降级恢复会更顺。
