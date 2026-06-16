# Changelog - Wake 21

## 阶段

第 21 次唤醒：改进阶段。

本轮依据 `notes/inspection_wake20.md` 做一个小闭环：修正 write hole demo 中容易混淆的教学标签，并补上 write hole 后续的 rebuild/scrub 承接页。

## 本轮做了什么

1. 小修 `labs/level0_python_model/demo_write_hole.py`：
   - 把手算段输出里的 `recover disk1 D1` 改成 `recover missing D1`，避免把“物理 disk1”和“逻辑 D1”混在一起；
   - 给 `print_model_case()` 增加 `failed_disk: int = 2` 参数；
   - 在模型段输出里显示当前失败盘，例如 `(disk2 failed)`；
   - 增加说明：默认失败 disk2 只是因为 stripe 0 里 D1 最容易观察；
   - 把 mini challenge 改成让读者修改 `failed_disk` 并预测恢复结果。

2. 新增 `docs/rebuild_and_scrub.md`：
   - 用同一组 `D0/D1/D2/P` 数字解释 rebuild；
   - 说明 write hole 为什么会在 rebuild 时“爆炸”；
   - 解释 scrub 如何主动扫描并发现 parity mismatch；
   - 给出 FPGA 控制器需要的最小信号/状态机视角；
   - 明确 scrub 发现 mismatch 后不能随便静默修复。

3. 更新路线入口：
   - `README.md` 增加 `docs/rebuild_and_scrub.md` 链接；
   - README 通关路线新增“看 rebuild/scrub”一步；
   - `TODO.md` 将 `docs/rebuild_and_scrub.md` 标记为完成。

## 修改了哪些文件

- `labs/level0_python_model/demo_write_hole.py`
- `docs/rebuild_and_scrub.md`
- `README.md`
- `TODO.md`
- `notes/changelog_wake21.md`

## 如何验证

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.06s
```

同时确认 demo 输出包含：

```text
recover missing D1: 0xcc  (D0 XOR D2 XOR P)
recover missing D1: 0x0f  (D0 XOR D2 XOR P)
The default failure is disk2 only because stripe 0 keeps D1 easy to see.
degraded RAID5.read(1) : 0xcc  (disk2 failed)
Mini challenge: change failed_disk in print_model_case() and predict the recovered byte.
```

并确认 README 已包含：

```text
docs/rebuild_and_scrub.md
```

## 发现了什么问题

1. 第一次更新 README 时，字符串匹配没有命中，导致新增文档没有接入路线；随后按实际文本重新精确修补并验证通过。
2. `docs/rebuild_and_scrub.md` 目前还是概念页，没有对应的可运行 demo。下一步如果继续做 Level 0，最自然的补充是做一个 `demo_rebuild_and_scrub.py`。
3. TODO 里仍有“增加 RAID5 degraded read 演示脚本”，但现有 `demo_write_hole.py` 已经包含一部分 degraded read。下一轮检验应判断：是保留为独立 demo，还是改写成 rebuild/scrub demo，避免任务名重复。

## 下轮建议做什么

第 22 次唤醒应进入检验阶段。

建议从“路线连续性 + 可运行承接”角度检查：

1. `docs/rebuild_and_scrub.md` 是否真的承接了 `write_hole.md`，有没有术语跳跃；
2. README 的 Step 0~9 是否顺序自然，链接是否全部存在；
3. TODO 中 “degraded read 演示脚本” 是否已经被现有 demo 部分覆盖，是否应改成 `demo_rebuild_and_scrub.py`；
4. 是否需要给 rebuild/scrub 页配一个最小 Python demo，打印 scrub parity mismatch 和 rebuild 结果。
