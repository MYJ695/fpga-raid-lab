# Changelog - Wake 15

## 阶段

第 15 次唤醒：改进阶段。

## 改进内容

1. 新增 `docs/write_hole.md`，解释 RAID5 partial write 被打断后为什么会留下 data/parity 不一致风险。
2. 用固定 4 盘 stripe 和 byte 级数值例子演示：
   - data 已写新值、parity 仍是旧值；
   - parity 已写新值、data 仍是旧值；
   - 两种状态在正常读和 degraded read / rebuild 中会出现不同后果。
3. 明确 write hole 不是“每次 partial write 必坏”，而是 data/parity 不能原子提交时产生的一致性窗口。
4. 增加 FPGA 视角：write scheduler、completion tracker、dirty bitmap、recovery state machine、scrub/check engine。
5. 简要列出 battery-backed cache、journal、PPL、dirty bitmap、scrub 等缓解方向，只作为后续路标，不展开成完整可靠性设计。
6. 在 `README.md` 当前入口和 Step 路线中接入 `docs/write_hole.md`。
7. 在 `TODO.md` 标记 `docs/write_hole.md` 完成。
8. 顺手补强 `docs/raid5_write_path.md`：加入多块 partial write 的 generalized RMW 公式，并把下一关链接改成可点击链接。

## 下一步留给检验阶段的问题

- `docs/write_hole.md` 中两个中断状态的数值例子是否完全正确；
- 文档是否过度暗示“write hole 只发生在 partial write”，而忽略 full-stripe write 也需要掉电一致性保护；
- dirty bitmap / PPL / journal / scrub 的描述是否准确且没有过度承诺；
- README Step 0~8 是否仍然顺畅，是否该补“每关通关条件”；
- 是否应该在后续补一个可运行 write hole demo，让 parity mismatch 影响 degraded read 的过程可视化。
