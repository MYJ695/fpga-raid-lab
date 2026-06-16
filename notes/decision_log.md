# Decision Log

## 2026-06-16 - Level 0 模型边界

- 决策：先把 Python golden model 做成最小可运行实验，而不是直接写 RTL。
- 原因：RAID 的映射、校验、降级读和重建关系需要先讲清楚；Python 更适合快速验证。
- 当前限制：RAID5 只做 full-stripe write，不做 partial write / write hole。
- 待确认：后续 RTL 使用 Verilog 还是 SystemVerilog；教学块大小继续用 4B 还是改成 512B/4KiB。
