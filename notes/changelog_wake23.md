# Changelog - Wake 23

## 阶段

第 23 次唤醒：改进阶段。

本轮依据 `notes/inspection_wake22.md` 做一个小闭环：修正 write hole 文档里的物理盘编号混淆，并把 rebuild/scrub 从“概念页”推进到“可运行 demo”。

## 本轮做了什么

1. 修正 `docs/write_hole.md`：
   - 在 stripe 0 布局 `disk0=P disk1=D0 disk2=D1 disk3=D2` 下，恢复逻辑 `D1` 时缺失的物理盘应为 `disk2`；
   - 将残留的 `disk1` 缺失描述改为 `disk2`，避免继续混淆“逻辑 D1”和“物理 disk1”。
2. 新增 `labs/level0_python_model/demo_rebuild_and_scrub.py`：
   - 构造一个 write hole 后的 RAID5 stripe：`D1=0x0f` 已写入，但 parity 仍是旧的 `0x66`；
   - 打印 scrub 重新计算 parity 的过程，并显示 `parity mismatch detected`；
   - 打印 disk2 缺失时 rebuild D1 的 XOR 过程，并显示恢复出旧值 `0xcc`。
3. 更新 `docs/rebuild_and_scrub.md`：
   - 增加“动手检查”小节；
   - 加入新 demo 的运行命令和关键输出摘要；
   - 把本关直觉明确成：scrub 尽量在坏盘前发现 mismatch，rebuild 可能在坏盘后把 mismatch 变成错误恢复数据。
4. 更新 `README.md`：
   - 当前优先级从 Level 0~4 扩到 Level 0~5 的 Python/文档闭环；
   - 在可视化 demo 命令中加入 `demo_rebuild_and_scrub.py`；
   - 将路线描述补上 rebuild/scrub 维护路径。
5. 更新 `TODO.md`：
   - 将重复的 degraded read demo 任务改成已完成的 rebuild/scrub demo 任务。

## 修改了哪些文件

- `docs/write_hole.md`
- `docs/rebuild_and_scrub.md`
- `labs/level0_python_model/demo_rebuild_and_scrub.py`
- `README.md`
- `TODO.md`
- `notes/changelog_wake23.md`

## 如何验证

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
```

实测结果：

```text
12 passed in 0.07s
```

新 demo 的关键输出：

```text
scrub result: parity mismatch detected
rebuild_D1 = P XOR D0 XOR D2
             = 0x66 XOR 0xaa XOR 0x00
             = 0xcc
expected current D1 was 0x0f, so rebuild produced stale data
```

同时检查了 README 中的本地 Markdown 链接，现有链接均存在。

## 发现了什么问题

1. 第一次写入新 demo 时，脚本字符串里的 `\n` 被生成成了真实换行，导致 Python 字符串未闭合。已通过读回文件定位，并改成显式 `print()` 分隔段落。
2. 当前 rebuild/scrub demo 仍是“手工构造一个 stripe”，没有调用 `RAID5.rebuild_disk()` 写回新盘。作为教学第一步是清晰的，但下一步如果进入“维护状态机”，应该补一个更接近控制器动作的 rebuild loop。
3. `docs/fpga_architecture.md` 仍未进入主线；现在 Level 0~5 的 RAID 概念和 Python demo 已基本串起来，后续应开始把这些动作映射到 FPGA 模块边界。

## 下轮建议做什么

第 24 次唤醒应进入检验阶段。

建议从“准备进入 RTL 前的架构审查”视角检查：

1. README 从 RAID5/rebuild/scrub 到 `rtl/xor_engine` 的过渡是否足够自然；
2. `docs/fpga_architecture.md` 是否存在、是否需要先补一个轻量架构页；
3. 现有 Python demo 中哪些动作可以直接映射成 RTL 小模块：XOR engine、LBA mapper、stripe manager、scrub/rebuild FSM；
4. 是否需要在 TODO 中新增“Level 1 RTL 前置任务”，避免从 Python 突然跳到 RTL。
