# Inspection Report - Wake 10

## 阶段

第 10 次唤醒：检验阶段。

本轮检验第 9 次唤醒新增的 `docs/raid1_mirror.md` 以及 README 的 Step 0~5 通关路线。原则是不修改交付物，只记录事实核对、实测结果和下一轮改进建议。

## 检验视角

本轮采用三个视角：

1. **懂 FPGA 但不懂 RAID 的读者**：能否理解 RAID1 是“请求复制 + 健康盘选择”，不是另一种条带映射；
2. **测试工程师**：文档中的容量、写入扇出、单盘故障、全盘故障是否与 Python 模型一致；
3. **课程设计者**：RAID0 页和 RAID1 页是否形成足够强的“拆散 vs 复制”对照，是否自然通向 RAID5。

## 实测验证

### 1. RAID1 容量与最小成员盘一致

实测不同成员盘容量组合：

```text
(4, 4) capacity 4 expected 4 OK
(2, 5) capacity 2 expected 2 OK
(7, 3, 6) capacity 3 expected 3 OK
```

结论：文档中 `capacity_blocks = min(d.block_count for d in disks)` 的解释与模型一致。

### 2. 写入扇出与模型一致

对 `LBA2` 写入 `b'WXYZ'` 后，检查两块盘：

```text
disk 0 lba2 b'WXYZ'
disk 1 lba2 b'WXYZ'
```

结论：`RAID1.write()` 确实把同一份数据写到所有镜像盘。

### 3. 故障矩阵与文档一致

实测两盘 RAID1 的四种场景：

```text
failed disks () failed lbas []
failed disks (0,) failed lbas []
failed disks (1,) failed lbas []
failed disks (0, 1) failed lbas [0, 1, 2, 3]
```

结论：单盘故障后所有 LBA 仍可读；两块盘都故障后所有 LBA 不可读。

### 4. RAID0 与 RAID1 对照成立

同样让 `disk0` 故障：

```text
RAID0 disk0 failed bad lbas [0, 2]
RAID1 disk0 failed bad lbas []
```

结论：`docs/raid1_mirror.md` 中“RAID0 坏一块盘后只有部分 LBA 可读，RAID1 坏一块盘后所有 LBA 仍可读”的对照准确。

### 5. 文档链接、表格和推荐命令

链接检查：

```text
README.md TODO.md OK
README.md docs/raid_basics.md OK
README.md docs/raid0_mapping.md OK
README.md docs/raid1_mirror.md OK
README.md labs/level0_python_model/ OK
```

表格分隔行检查：

```text
docs/raid1_mirror.md table line 10 OK
docs/raid1_mirror.md table line 23 OK
docs/raid1_mirror.md table line 117 OK
docs/raid1_mirror.md table line 167 OK
README.md table line 32 OK
```

README 推荐命令：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

运行结果：

```text
demo_layout.py exit 0
pytest exit 0
12 passed in 0.25s
```

验证后缓存目录已清理：

```text
cache dirs after cleanup: [] []
```

## 及格线判断

本轮检验结论：第 9 轮改进达到及格线。

理由：

1. RAID1 容量、写入扇出、健康盘读取、单盘故障、全盘故障都与模型一致；
2. README Step 0~5 能把读者从 RAID 基础带到 RAID0、RAID1、demo、源码、测试；
3. RAID0 与 RAID1 的核心差异已经可读：一个拆散数据，一个复制数据；
4. 文档链接、表格格式、推荐命令均通过实测。

## 不够出色的点

### 1. README 还缺“通关条件”

当前 Step 0~5 告诉读者要看什么、跑什么，但没有明确每关结束后应该能回答什么。例如：

- 看完 RAID0：能否手算 LBA 7 落在哪块盘？
- 看完 RAID1：能否解释为什么坏一块盘所有 LBA 仍可读？
- 跑完测试：能否指出哪个测试覆盖了单盘故障？

这会影响“闯关式实验室”的完成感。

### 2. RAID1 页没有直接给一个“小练习”

文档有动手检查，但偏运行命令；还可以更像课程一样提出一两个读者可手算问题：

- 如果 `disk1` failed，`read LBA3` 从哪读？
- 如果 3 块盘做 RAID1，坏 2 块还能不能读？

这不是正确性问题，而是教学体验问题。

### 3. 下一关 RAID5 仍然悬空

`docs/raid1_mirror.md` 末尾提到 `docs/raid5_parity.md`，但文件尚不存在。虽然不是 Markdown 链接，不造成路径错误，但读者学完 RAID1 后仍不能继续进入 RAID5 parity。

### 4. demo 的重点还不够“教学化”

README 让读者运行 `demo_layout.py`，但 demo 输出是否足够突出 RAID1 的“同一 LBA 双盘副本”，还需要下一轮之后继续检验。当前文档主要靠 Markdown 表格完成解释。

## 下轮建议

第 11 次唤醒应进入**改进阶段**。

建议优先补 `docs/raid5_parity.md`，原因：

1. 原始 objective 的文档优先级中，`raid5_parity.md` 紧跟在 RAID0/RAID1 后；
2. README 的通关地图 Level 3 已经写到 RAID5，但当前缺对应讲解页；
3. RAID0 解决“拆散数据”，RAID1 解决“复制数据”，RAID5 正好引入第三个核心直觉：**拆散数据 + XOR 校验，用一块盘容量换单盘容错**；
4. 当前 Python 模型已经实现 RAID5，可以直接对照 `RAID5.layout_row()`、`write_full_stripe()`、`read()`、`rebuild()`。

建议第 11 轮的小闭环内容：

1. 新增 `docs/raid5_parity.md`；
2. 用三块或四块盘演示 `D0 XOR D1 = P`；
3. 解释 XOR 的可逆性：`D0 = D1 XOR P`；
4. 画出 parity 轮转表，对应 `RAID5.layout_row()`；
5. 展示单盘故障 degraded read 的直觉；
6. README / TODO 接上 RAID5 parity 入口；
7. 写 `notes/changelog_wake11.md` 并验证命令、链接、表格、模型行为。

README “每关通关条件”也值得补，但建议放在 RAID5 parity 页之后做。理由是等 RAID0/RAID1/RAID5 三个核心文档都存在后，再统一补通关条件，结构会更完整。
