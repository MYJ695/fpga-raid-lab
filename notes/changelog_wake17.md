# Changelog - Wake 17

## 阶段

第 17 次唤醒：改进阶段。

本轮根据 `notes/inspection_wake16.md` 的建议，把 `docs/write_hole.md` 从“只靠手算理解”推进到“可以亲手运行 demo 看见问题”。

## 本轮做了什么

1. 新增 `labs/level0_python_model/demo_write_hole.py`：
   - 使用 `docs/write_hole.md` 里的同一组数值；
   - 演示 `data new, parity old`；
   - 演示 `parity new, data old`；
   - 对比 normal read 和 degraded recovery 的结果；
   - 让读者看到 write hole 的危险点：正常读可能看起来没坏，降级恢复或重建时才暴露。

2. 更新 README：
   - 在通关地图 Level 4 的产出里加入 `write hole demo`；
   - Step 6 改成同时观察 RAID0/1/5 布局和 write hole 潜伏风险；
   - 可运行命令加入 `python labs/level0_python_model/demo_write_hole.py`。

3. 更新 TODO：
   - 在 RAID5 可靠性与维护任务里勾选 `demo_write_hole.py`；
   - 保留 `docs/rebuild_and_scrub.md` 和 degraded read 演示脚本作为后续任务。

4. 更新 `docs/write_hole.md`：
   - “动手检查”区域加入 `demo_write_hole.py`；
   - 删除“当前 Python 模型还没有模拟 write hole”的过时说法；
   - 补一句解释 demo 输出如何对应正常读和降级恢复。

## 修改了哪些文件

- `labs/level0_python_model/demo_write_hole.py`
- `README.md`
- `TODO.md`
- `docs/write_hole.md`
- `notes/changelog_wake17.md`

## 如何验证

建议从仓库根目录运行：

```bash
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

本轮验证重点：

- demo 能直接从仓库根目录运行；
- demo 输出包含两个 write hole 场景；
- demo 输出包含 `normal read` 和 `recover disk1`；
- Case A 中恢复出 `0xcc`；
- Case B 中恢复出 `0x0f`；
- README 和 `docs/write_hole.md` 均接入新命令；
- pytest 保持通过。

## 发现了什么问题

1. `demo_write_hole.py` 目前是独立数值演示，没有直接操作 `RAID5` 类的成员盘。优点是输出更短、更适合教学；缺点是还不能演示真实模型对象里的“写一半”。
2. README 当前优先级仍写着“先做 Level 0 ~ Level 3”，但通关地图和文档已经进入 Level 4 的 write path/write hole。下轮检验可判断是否需要把当前优先级文案更新为 “Level 0 ~ Level 4”。
3. 还缺 `docs/rebuild_and_scrub.md`，因此 write hole 之后的“如何发现和修复潜伏不一致”还没有闭环。

## 下轮建议做什么

第 18 次唤醒应进入检验阶段。

建议重点检验：

1. `demo_write_hole.py` 是否真的比手算更容易理解；
2. README、TODO、`docs/write_hole.md` 的接入是否一致；
3. demo 是否需要补成“调用 RAID5 对象 + 人为篡改 parity”的版本；
4. 当前优先级是否应该从 Level 0~3 更新到 Level 0~4；
5. 下一轮改进是否应补 `docs/rebuild_and_scrub.md`，还是先补 RAID5 degraded read demo。
