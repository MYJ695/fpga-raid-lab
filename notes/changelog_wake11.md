# Changelog - Wake 11

## 阶段

第 11 次唤醒：改进阶段。

## 改进内容

1. 新增 `docs/raid5_parity.md`，解释 RAID5 的 XOR 校验、轮转 parity、降级读和 rebuild 直觉。
2. 用 3 块盘 byte 级 XOR 例子说明 `D0 XOR D1 = P` 以及 `D0 = D1 XOR P` 的可逆性。
3. 用 4 块盘 stripe 表对应 `RAID5.layout_row()`，展示 parity 在成员盘之间轮转。
4. 增加 RAID5 LBA 到 data disk / parity disk 的映射表，对应 `RAID5.map_lba()`。
5. 在主 README 中加入 RAID5 parity 页入口，并把通关路线扩展到 Step 0~6。
6. 更新 `TODO.md`，标记 `docs/raid5_parity.md` 完成。
7. 更新 `notes/progress_log.md`，记录本轮小闭环。

## 下一步留给检验阶段的问题

- `docs/raid5_parity.md` 的 XOR 示例、layout 表和模型实现是否完全一致；
- RAID5 文档是否足够清楚地区分 full-stripe write、degraded read、rebuild；
- 对懂 FPGA 但不懂 RAID 的读者，XOR engine / LBA mapper / stripe manager 的对应关系是否足够直观；
- 下一轮改进应补 `docs/raid5_write_path.md`，还是先补 README 每关通关条件。
