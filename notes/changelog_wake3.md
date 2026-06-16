# Changelog - Wake 3

## 阶段

第 3 次唤醒：改进阶段。

## 改进内容

1. 工程卫生：新增 `.gitignore`，并准备清理 Python 缓存。
2. 测试增强：把 Wake 2 临时探针固化为 pytest，包括 parity disk 故障、parity rebuild、5 盘 RAID5、RAID0 坏盘。
3. 读者体验：新增 `demo_layout.py`，直接打印 RAID0/1/5 ASCII 布局。
4. 文档边界：Level 0 README 补充 demo 运行方式、RAID0/RAID1/RAID5 当前边界。

## 下一步留给检验阶段的问题

- demo 输出是否足够直观，是否需要更像“闯关说明”；
- 新增测试是否覆盖了最关键的教学边界；
- `.gitignore` 是否足够但不过度。
