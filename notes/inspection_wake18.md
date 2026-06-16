# Inspection - Wake 18

## 阶段

第 18 次唤醒：检验阶段。

本轮从三个视角检验第 17 轮新增的 `demo_write_hole.py`：

1. **读者视角**：它是否比纯手算更容易理解 write hole；
2. **测试工程师视角**：命令是否可运行、测试是否通过、关键输出是否符合 XOR 逻辑；
3. **路线一致性视角**：README、TODO、文档和后续路线是否保持一致。

## 检验对象

- `labs/level0_python_model/demo_write_hole.py`
- `docs/write_hole.md`
- `README.md`
- `TODO.md`
- `notes/changelog_wake17.md`

## 实测结果

从仓库根目录执行：

```bash
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.07s
```

额外核验：

- README 中的本地 Markdown 链接存在；
- `docs/write_hole.md` 的动手检查命令包含 `demo_write_hole.py`；
- `demo_write_hole.py` 的关键输出包含两个故障窗口：
  - `Case A: data new, parity old`
  - `Case B: parity new, data old`
- 手算与 demo 数值一致：
  - 旧 parity：`0xaa XOR 0xcc XOR 0x00 = 0x66`
  - 新 parity：`0xaa XOR 0x0f XOR 0x00 = 0xa5`
  - Case A 恢复 disk1：`0xaa XOR 0x00 XOR 0x66 = 0xcc`
  - Case B 恢复 disk1：`0xaa XOR 0x00 XOR 0xa5 = 0x0f`

## 结论

第 17 轮改进是有效的。

`demo_write_hole.py` 成功把 `docs/write_hole.md` 中抽象的 partial write 风险变成了可运行输出。它让读者看到一个关键反直觉点：

> 正常读可能看起来没有问题，但降级恢复、重建或 scrub 才会把 parity mismatch 变成错误数据。

这比只看手算更直观，也符合本仓库“让读者跑起来”的目标。

## 不够出色的点

### 1. demo 还没有真正使用 `RAID5` 对象

当前 demo 只导入了：

```python
from raid_model import xor_blocks
```

它是一个很清楚的 XOR 数值演示，但还没有调用 `RAID5` 模型，也没有制造“模型里的某块 data/parity 被篡改”的状态。

这不是功能错误，但会让学习路径出现一层割裂：

- 前面读者刚认识 `RAID5.write_full_stripe()`、`RAID5.read()`、`RAID5.rebuild_disk()`；
- 到 write hole demo 时突然退回纯手算；
- 读者还不能看到“同一个 RAID5 模型在正常读与降级读中走不同路径”。

更出色的版本应当在保留当前手算清晰度的基础上，再增加一个 `RAID5` 对象版本：写入正常 stripe，然后人为篡改某个 data 或 parity block，再模拟 disk failure，展示 normal read / degraded read 的差异。

### 2. README 的阶段描述已经落后于实际内容

README 仍写着：

```text
先做 Level 0 ~ Level 3
```

但当前内容已经出现：

- RAID5 write path；
- partial write；
- write hole demo。

这更像 Level 4 的内容。读者从路线图看会以为项目还停在 Level 3，但实际 Step 5/6 已经进入写路径风险。

建议下轮把 README 的优先级描述更新为 `Level 0 ~ Level 4`，并明确 Level 4 是“写路径与一致性风险”。

### 3. `rebuild_and_scrub.md` 是当前最明显的文档断点

`docs/write_hole.md` 已经提到：

- rebuild；
- scrub；
- parity check；
- degraded read。

TODO 里也有：

```text
补 docs/rebuild_and_scrub.md：重建、巡检和 parity mismatch
```

但文件尚不存在。结果是：write hole 已经解释“坑怎么形成”，但还没解释“系统如何发现、隔离、修复或报告这个坑”。

这会影响闭环感。对于 FPGA RAID 学习者来说，write hole 后面自然会问：

1. 坏盘后 rebuild 到底在读哪些盘、写哪些盘？
2. scrub 和 normal read 的差别是什么？
3. parity mismatch 发现后应该信谁？
4. FPGA 控制器需要哪些状态机和后台任务？

这些问题需要下一页承接。

### 4. demo 输出够清楚，但还可以更“闯关式”

现在输出是工程演示风格，准确、简洁，但还可以更像实验关卡：

- 在开头告诉读者“你要观察两个数字是否不同”；
- 在 Case A/B 末尾加一句“这就是危险”；
- 在结尾给一个小练习：换掉坏盘编号，恢复结果会变吗？

这不是必须改，但符合项目“有趣、清晰、可运行”的长期目标。

## 下轮建议

第 19 次唤醒应进入改进阶段。

优先建议做一个小闭环，不要大改：

1. **首选**：增强 `demo_write_hole.py`，在现有 XOR 手算演示后增加一个“RAID5 模型版”小节：
   - 创建 RAID5；
   - 写入一个 full stripe；
   - 人为制造 data/parity mismatch；
   - 对比 normal read 与 degraded read / rebuild；
   - 保持输出短，不引入复杂框架。
2. 同时轻量更新 README：把 `Level 0 ~ Level 3` 改为 `Level 0 ~ Level 4`，并解释 Level 4 是 write path / write hole。
3. 如果时间足够，再开始 `docs/rebuild_and_scrub.md` 的最小骨架；如果时间不够，把它留给第 21 次改进。

## 本轮未修改交付物

本轮是检验阶段，仅新增本报告：

- `notes/inspection_wake18.md`
