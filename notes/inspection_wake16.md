# Inspection Report - Wake 16

## 阶段

第 16 次唤醒：检验阶段。

本轮检验第 15 次唤醒新增的 `docs/write_hole.md`，以及 README/TODO/`docs/raid5_write_path.md` 对该页面的接入。原则是不修改交付物，只记录事实核对、实测结果和下一轮改进建议。

## 检验视角

本轮采用五个视角：

1. **测试工程师**：复算 write hole 页面里的所有 XOR 数值，确认两个失败状态没有算错；
2. **可靠性工程师**：检查是否把 write hole 讲成“可能的一致性窗口”，而不是“partial write 必然损坏”；
3. **懂 FPGA 但不懂 RAID 的读者**：检查 completion tracking、metadata、scrub 等说法是否能建立正确直觉；
4. **课程设计者**：检查 README Step 0~8 是否仍像一条顺滑通关路线；
5. **项目维护者**：检查 TODO 是否把下一步拆成可运行、可验证的小闭环。

## 实测结果

### 1. XOR 数值复算

文档固定例子：

```text
D0     = 0xaa
old_D1 = 0xcc
D2     = 0x00
old_P  = 0x66
new_D1 = 0x0f
new_P  = 0xa5
```

复算结果：

```text
old parity 0x66 OK
new parity 0xa5 OK
RMW delta 0xa5 OK
case1 recover with stale parity 0xcc OK
case2 recover with new parity 0xf OK
```

结论：

- `old_P = 0xaa XOR 0xcc XOR 0x00 = 0x66` 正确；
- `new_P = 0xaa XOR 0x0f XOR 0x00 = 0xa5` 正确；
- `old_P XOR old_D1 XOR new_D1 = 0xa5` 正确；
- 坑 1 里 data 新、parity 旧，`disk1` 坏后恢复出旧值 `0xcc`，正确；
- 坑 2 里 parity 新、data 旧，正常读看到旧值 `0xcc`，恢复读算出新值 `0x0f`，正确。

该页最关键的教学算例没有发现事实错误。

### 2. write hole 风险边界

检查到的关键边界句：

```text
write hole 是 RAID5 partial write 的一致性窗口，不是每次 partial write 必然损坏。
```

同时页面也补了：

```text
为什么 full-stripe write 也要小心
```

结论：

- 页面没有把 write hole 误写成“XOR 算错”；
- 页面没有把 write hole 误写成“每次 partial write 必坏”；
- 页面明确区分了正常读、degraded read、rebuild 的风险暴露时机；
- 页面没有误导当前 Python 模型已经实现 write hole，结尾明确写了“当前 Python 模型还没有模拟 write hole”。

及格线通过。

不够出色的点：

- 现在仍然是手算解释，读者还不能亲手跑出“正常读没坏，但降级读错了”的反差；
- full-stripe write 的风险边界讲到了，但还偏概念，没有展示“多个 data/parity 写仍然可能部分落盘”的具体小例子；
- 页面提到 PPL、journal、dirty bitmap、scrub，但没有给参考资料入口。

### 3. FPGA 视角检查

页面把 write hole 映射到 FPGA/控制器模块：

```text
data/parity 必须成组提交 -> write scheduler + completion tracker
掉电后要知道哪些 stripe 可疑 -> metadata bitmap / dirty stripe table
恢复时要决定重放还是回滚 -> recovery state machine
不能无限缓存所有写 -> stripe buffer + backpressure
parity mismatch 要被发现 -> scrub / check engine
```

结论：这张表对入门者有效。它把问题从“XOR engine 怎么算”推进到“写什么时候算 committed”，符合本项目从 RAID 知识走向 FPGA 架构的目标。

不够出色的点：

- 还没有把这些模块和未来 `rtl/stripe_manager`、`rtl/lba_mapper`、`sim/` 关联起来；
- `flush / ordering / completion` 目前只是隐含在 completion tracker 里，没有作为独立概念出现；
- “metadata bitmap / dirty stripe table”只告诉读者要记可疑 stripe，没有解释它只能缩小检查范围、不能自动恢复数据。正文机制表里有这句话，但 FPGA 表里没有呼应。

建议下一轮不要急着写大架构页，先做一个小 demo，让这些抽象模块有可观察现象。

### 4. README 通关路线

抽取到的 Step：

```text
0 先看 RAID 基础
1 看 RAID0 映射
2 看 RAID1 镜像
3 看 RAID5 parity
4 看 RAID5 write path
5 看 write hole
6 跑可视化 demo
7 对照源码看映射、镜像和校验
8 跑测试
```

编号连续，顺序也合理：先理解 RAID5 parity，再理解 write path，最后看 write hole。

发现的问题：

1. README 顶部“通关地图”仍停在 Level 5 重建，没有显式把 write hole 作为 Level 4 和 Level 5 之间的可靠性关卡；
2. Step 6 的可视化 demo 仍只展示 RAID0/1/5 布局，不展示 write hole；
3. README 仍缺“每关通关条件”，例如 Step 5 结束后读者应该能回答：
   - 为什么正常读不一定发现 parity mismatch？
   - data 新 parity 旧时，坏掉 data disk 会恢复出什么？
   - dirty bitmap 为什么不等于自动修复？

结论：路线可用，但还不像真正的“闯关式实验室”。

### 5. 链接、表格和可运行检查

链接检查通过：

```text
README.md TODO.md OK
README.md docs/raid_basics.md OK
README.md docs/raid0_mapping.md OK
README.md docs/raid1_mirror.md OK
README.md docs/raid5_parity.md OK
README.md docs/raid5_write_path.md OK
README.md docs/write_hole.md OK
README.md labs/level0_python_model/ OK
docs/raid5_write_path.md write_hole.md OK
```

Markdown 表格列数检查通过，涉及：

```text
README.md
docs/write_hole.md
docs/raid5_write_path.md
```

可运行检查通过：

```text
python labs/level0_python_model/demo_layout.py exit 0
python -m pytest -q labs/level0_python_model exit 0
12 passed in 0.06s
```

缓存已清理：

```text
cache dirs after cleanup: [] []
```

## 本轮发现的问题

按优先级排序：

1. **缺少可运行 write hole demo**  
   当前页面讲得清楚，但仍是 Markdown 手算。对“闯关式实验室”来说，下一步最有价值的是让读者跑一个脚本，看到：正常读看似正确，degraded read/rebuild 依赖错误 parity 时会恢复出错误值。

2. **TODO 没有显式列出 write hole demo 任务**  
   TODO 里有 `rebuild_and_scrub.md` 和 degraded read 演示脚本，但没有把 `demo_write_hole.py` 作为独立小闭环。下一轮若要改进，应先把这个任务补进去并完成。

3. **README 顶层通关地图没有体现 write hole 关卡**  
   当前 Step 列表有 write hole，但上方 Level 表没有。读者扫第一张表时，会觉得 Level 4 是“小写问题”，Level 5 直接进入重建，中间的可靠性风险不够显眼。

4. **机制名缺参考入口**  
   PPL、journal、dirty bitmap、scrub 这些词已经出现，但目前没有 `docs/references.md` 或本页参考链接。对初学者足够，对后续深入不够。

5. **每关缺通关条件**  
   README 的 Step 0~8 是路线，不是关卡。后续要变成实验室，需要给每关补“过关后你应该能做到什么”。

## 下轮建议

第 17 次唤醒应进入**改进阶段**。

建议选择一个小闭环：**新增可运行 write hole demo**，优先级高于直接写 `rebuild_and_scrub.md`。

推荐交付物：

1. 新增 `labs/level0_python_model/demo_write_hole.py`：
   - 固定使用与 `docs/write_hole.md` 相同的 `0xaa / 0xcc / 0x00 / 0x66 / 0x0f / 0xa5`；
   - 打印 old stripe、intended new stripe；
   - 场景 A：data 新、parity 旧；
   - 场景 B：parity 新、data 旧；
   - 分别打印 normal read 与 degraded recovery 的结果；
   - 结尾用一句话解释“看起来没坏”和“恢复时才坏”。

2. 修改 README：
   - 在当前可运行入口中加入 `demo_write_hole.py`；
   - Step 6 从“跑可视化 demo”升级为“跑布局和 write hole demo”；
   - 顶层通关地图把 Level 4 产出补成 `RMW / reconstruct write + write hole demo`。

3. 修改 TODO：
   - 增加并勾选 `demo_write_hole.py`；
   - 保留 `rebuild_and_scrub.md` 作为下一轮候选。

4. 可选小改：
   - 在 `docs/write_hole.md` 的“动手检查”里加入：
     ```bash
     python labs/level0_python_model/demo_write_hole.py
     ```

验证标准：

```bash
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

并检查输出至少包含：

```text
data new, parity old
parity new, data old
normal read
recover disk1
0xcc
0x0f
```
