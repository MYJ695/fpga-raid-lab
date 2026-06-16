# Changelog - Wake 19

## 阶段

第 19 次唤醒：改进阶段。

本轮根据 `notes/inspection_wake18.md` 的检验建议，做一个小闭环：把 write hole demo 从“纯 XOR 手算”推进到“手算 + 现有 RAID5 模型交叉验证”。

## 本轮做了什么

1. 增强 `labs/level0_python_model/demo_write_hole.py`：
   - 从 `raid_model` 额外导入 `RAID5` 和 `VirtualDisk`；
   - 保留原有的可见 XOR 手算段，避免读者失去直觉；
   - 新增 `RAID5 model cross-check` 段：
     - 创建 4 盘 RAID5，block size 为 1 字节；
     - 写入 stripe 0：`disk0=P disk1=D0 disk2=D1 disk3=D2`；
     - 人为把 parity block 改成旧/新值，制造 data/parity mismatch；
     - 对比 `RAID5.read(1)` 的 normal read 与 disk2 failed 后的 degraded read；
   - 在开头提示读者观察 normal read 与 degraded read 两条路径；
   - 在结尾增加一个 mini challenge，让 demo 更像实验关卡。

2. 更新 `README.md` 当前优先级：
   - 从 `Level 0 ~ Level 3` 改为 `Level 0 ~ Level 4`；
   - 路线描述加入 `RAID5 写路径风险`，避免路线图落后于实际内容。

## 修改了哪些文件

- `labs/level0_python_model/demo_write_hole.py`
- `README.md`
- `notes/changelog_wake19.md`

## 如何验证

从仓库根目录执行：

```bash
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.06s
```

额外检查：

- `README.md` 包含 `Level 0 ~ Level 4`；
- `demo_write_hole.py` 导入 `RAID5, VirtualDisk, xor_blocks`；
- demo 输出包含 `RAID5 model cross-check`；
- Case A/B 的模型输出与手算一致：
  - data new + parity old：normal read 为 `0x0f`，degraded read 为 `0xcc`；
  - parity new + data old：normal read 为 `0xcc`，degraded read 为 `0x0f`。

## 发现了什么问题

1. `demo_write_hole.py` 现在已经连上现有 RAID5 模型，但仍是人为篡改底层 disk block 来模拟崩溃窗口；这符合教学目的，但还不是一个真正的 partial-write API。
2. `docs/rebuild_and_scrub.md` 仍未建立。write hole 已经能“看见坑”，但 rebuild / scrub 如何发现、报告、处理 parity mismatch 还没有文档承接。
3. 目前测试集仍没有专门测试 demo 输出；现阶段用脚本实跑足够，但后续如果 demo 继续变复杂，可以加轻量 smoke test。

## 下轮建议做什么

第 20 次唤醒应进入检验阶段。

建议从更苛刻的“教学闭环 + 模型真实性”角度检查：

1. `demo_write_hole.py` 的 RAID5 model cross-check 是否真的降低了理解割裂感；
2. 模型段是否会让读者误以为 write hole 只会发生在 disk2/D1；
3. README 的 Level 0~4 描述是否和 TODO、docs 顺序完全一致；
4. 是否应该在下一次改进补 `docs/rebuild_and_scrub.md` 的最小页，承接 write hole 后的“怎么发现和处理”。
