# Changelog - Wake 13

## 阶段

第 13 次唤醒：改进阶段。

## 改进内容

1. 新增 `docs/raid5_write_path.md`，把 RAID5 写入拆成 full-stripe write、read-modify-write、reconstruct write 三条路径。
2. 用 4 盘 stripe 示例说明 partial write 不能只改数据块，必须同步修正 parity。
3. 增加 RMW 公式 `new_P = old_P XOR old_D XOR new_D` 的推导和 byte 级手算例子。
4. 增加 RMW 与 reconstruct write 的读旧块数量对比，给出教学级选择规则。
5. 明确引出 write hole：data 和 parity 分两处写，掉电/复位可能导致 stripe 不自洽。
6. 在 README 当前入口和 Step 路线中接入 `docs/raid5_write_path.md`。
7. 更新 `TODO.md`，标记 RAID5 write path 完成，并把下一组任务转向 write hole / rebuild / degraded demo。

## 下一步留给检验阶段的问题

- RMW 公式和 reconstruct write 读旧块数量是否经得起更复杂例子验证；
- 文档是否清楚地区分“当前 Python 模型已实现 full-stripe write”和“partial write 只是教学解释，尚未实现”；
- write hole 的风险描述是否足够准确，没有夸大为“每次 partial write 一定损坏”；
- README Step 0~7 是否仍然顺畅，还是应该补每关通关条件。
