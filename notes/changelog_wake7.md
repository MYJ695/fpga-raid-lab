# Changelog - Wake 7

## 阶段

第 7 次唤醒：改进阶段。

## 改进内容

1. 新增 `docs/raid0_mapping.md`，解释 RAID0 的 LBA 到 disk/chunk 映射公式。
2. 用 3 块盘、LBA 0~8 的表格和 ASCII 布局图展示条带化。
3. 增加 `disk1` 故障后哪些 LBA 不可读的小表，为 RAID5 degraded read 铺路。
4. 在主 README 中加入 RAID0 映射页入口，并把当前路线改成更明确的闯关步骤。
5. 更新 `TODO.md`，标记 `docs/raid0_mapping.md` 已完成。
6. 更新 `notes/progress_log.md`，记录本轮小闭环。

## 下一步留给检验阶段的问题

- `docs/raid0_mapping.md` 的公式、表格和模型实现是否完全一致；
- 对懂 FPGA 但不懂 RAID 的读者，chunk/stripe/disk_lba 的解释是否足够清楚；
- README 的闯关路线是否比之前更顺；
- 下一轮改进应补 `docs/raid1_mirror.md`，还是先增强 `demo_layout.py` 的故障可视化。
