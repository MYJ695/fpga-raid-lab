# Inspection - Wake 22

## 阶段

第 22 次唤醒：检验阶段。

本轮不改交付物，重点从“懂 FPGA 但不懂 RAID 的读者 + 测试工程师”视角检查第 21 轮新增内容：`docs/rebuild_and_scrub.md` 是否承接 `write_hole.md`，README 路线是否连贯，TODO 是否仍然准确，现有脚本是否足以支撑下一关。

## 检验范围

- `README.md`
- `TODO.md`
- `docs/write_hole.md`
- `docs/rebuild_and_scrub.md`
- `labs/level0_python_model/demo_write_hole.py`
- `labs/level0_python_model/raid_model.py`
- `notes/changelog_wake21.md`

## 实测验证

从仓库根目录执行了：

```bash
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.07s
```

同时用脚本检查 README 和 `docs/rebuild_and_scrub.md` 中的本地 Markdown 链接。README 中以下链接均存在：

- `TODO.md`
- `docs/raid_basics.md`
- `docs/raid0_mapping.md`
- `docs/raid1_mirror.md`
- `docs/raid5_parity.md`
- `docs/raid5_write_path.md`
- `docs/write_hole.md`
- `docs/rebuild_and_scrub.md`
- `labs/level0_python_model/`

## 及格线结论

当前第 21 轮交付物总体及格：

1. 新增 `docs/rebuild_and_scrub.md` 能承接 write hole，把“潜伏 mismatch”推进到 rebuild/scrub 两条维护路径；
2. README 已接入新文档，通关路线从 RAID 基础到 write hole 再到 rebuild/scrub 是顺的；
3. 现有 demo 和 pytest 可运行，基础行为没有坏；
4. `docs/rebuild_and_scrub.md` 没有明显乱码、路径错误或公式错误。

## 发现的问题

### P0：`docs/write_hole.md` 仍有 disk 编号错误，会误导读者

`docs/write_hole.md` 的 stripe 表写的是：

```text
disk0=P  disk1=D0  disk2=D1  disk3=D2
```

因此如果讨论“D1 缺失/恢复”，坏盘应是 `disk2`。

但 `docs/write_hole.md` 中至少两处仍写成了 `disk1`：

- 约第 83 行：`但如果之后 disk1 坏了，系统要用 D0 XOR D2 XOR P 恢复 D1`
- 第 226 行：`一旦 disk1 缺失...`

这和第 21 轮刚修正的 `demo_write_hole.py` 输出不一致。demo 已经明确：

```text
stripe 0 layout : disk0=P disk1=D0 disk2=D1 disk3=D2
degraded RAID5.read(1) : ... (disk2 failed)
```

影响：读者可能把“逻辑 D1”和“物理 disk1”再次混在一起。这个问题应优先修，因为它正好是第 20/21 轮想消除的教学歧义。

### P1：TODO 中 “增加 RAID5 degraded read 演示脚本” 已与现有 demo 重叠

`TODO.md` 仍有：

```text
- [ ] 增加 RAID5 degraded read 演示脚本，打印 XOR 恢复过程
```

但现有 `demo_write_hole.py` 已经能打印：

- 正常读直接返回数据盘内容；
- degraded read 通过 XOR 恢复；
- write hole 下恢复结果与正常读不一致；
- 用真实 `RAID5` 对象交叉验证。

因此这个 TODO 如果继续保持原样，下一轮容易做出重复 demo。更好的任务名应改成：

```text
增加 demo_rebuild_and_scrub.py：打印 scrub mismatch 和 rebuild 写回过程
```

这样能接上新文档第 170 行的“下一步可以做一个很小的 Python demo”。

### P1：`docs/rebuild_and_scrub.md` 是概念页，但缺少可运行锚点

该文档已经讲清楚：

- rebuild 用幸存块 XOR 出缺失块；
- scrub 重新计算 parity 并比较 stored parity；
- mismatch 后早期策略应 report only；
- FPGA 侧可以映射成最小状态机和信号。

但它还没有像 `write_hole.md` 那样给出“从仓库根目录运行”的命令。对闯关式实验室来说，Level 5 的入口还不够有趣，也不够可验证。

下一轮最有价值的小闭环不是继续扩文档，而是补一个很小的脚本：

```bash
python labs/level0_python_model/demo_rebuild_and_scrub.py
```

脚本目标：

1. 固定同一组 `D0=0xaa, D1=0x0f, D2=0x00, P=0x66` 的 write-hole 状态；
2. 打印 scrub：`expected_P=0xa5, stored_P=0x66, mismatch=True`；
3. 打印 rebuild：`disk2 failed -> rebuild D1 = 0xcc`；
4. 说明 report-only 不会静默修盘。

### P2：README 的 Level 表已经出现 Level 5，但当前优先级仍写 Level 0~4

README Level 表中已有：

```text
Level 5 | 重建 | 坏盘换新盘怎么补数据？ | rebuild engine 模型
```

但“当前优先级”仍写：

```text
先做 Level 0 ~ Level 4
```

第 21 轮实际上已经开始铺 Level 5 的 rebuild/scrub 概念页。严格说这不是错误，因为当前仍以 Level 0 Python 模型为主；但从路线表达看，下一轮如果补 `demo_rebuild_and_scrub.py`，README 的当前优先级应改成类似：

```text
先做 Level 0 ~ Level 5 的 Python/文档闭环，再进入 RTL XOR/lba_mapper
```

否则读者会疑惑：为什么 Level 5 文档已经进路线，但优先级仍说只做 Level 0~4。

## 不够出色的地方

从“有趣、清晰、可运行”的目标看，现在的 rebuild/scrub 页还停留在“读懂”层面，没有达到“看见”的层面。

它已经能解释概念，但还不能让读者一条命令看到：

```text
scrub: parity mismatch detected
rebuild: missing D1 reconstructed as stale 0xcc
```

这会让 Level 5 比前面的 write hole demo 少一点闯关感。下轮应该把这个缺口补上。

## 建议第 23 轮怎么改

第 23 次唤醒应进入改进阶段，建议只做一个小闭环：**把 rebuild/scrub 变成可运行 demo，并同步修正路线文字**。

优先修改：

1. 修 `docs/write_hole.md`：把 D1 缺失相关的 `disk1` 改成 `disk2`，避免物理盘号/逻辑数据号混淆；
2. 新增 `labs/level0_python_model/demo_rebuild_and_scrub.py`：打印 scrub mismatch 与 rebuild 结果；
3. 更新 `docs/rebuild_and_scrub.md`：增加“动手检查”命令和 demo 输出摘要；
4. 更新 `README.md`：在命令列表加入新 demo，并视情况把当前优先级扩到 Level 5 Python/文档闭环；
5. 更新 `TODO.md`：把重复的 degraded read demo 任务改成或标记为 rebuild/scrub demo。

验证建议：

```bash
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```
