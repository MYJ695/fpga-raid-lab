# Changelog - Wake 9

## 阶段

第 9 次唤醒：改进阶段。

## 改进内容

1. 新增 `docs/raid1_mirror.md`，解释 RAID1 的镜像、写入扇出、健康盘读取和容量代价。
2. 用双盘 LBA 0~3 表格和 ASCII 图展示同一数据在多块盘上的副本关系。
3. 对应到 Python 模型中的 `RAID1.write()`、`RAID1.read()` 和 `capacity_blocks`。
4. 在主 README 中加入 RAID1 镜像页入口，并把闯关路线扩展到 Step 0~5。
5. 更新 `TODO.md`，标记 `docs/raid1_mirror.md` 完成。
6. 更新 `notes/progress_log.md`，记录本轮小闭环。

## 下一步留给检验阶段的问题

- `docs/raid1_mirror.md` 是否准确反映当前 Python 模型行为；
- “写入扇出”和“读取健康盘”是否对 FPGA 读者足够直观；
- README Step 0~5 是否仍然顺畅；
- 下一轮改进应补 `docs/raid5_parity.md`，还是先补 README 每关通关条件。
