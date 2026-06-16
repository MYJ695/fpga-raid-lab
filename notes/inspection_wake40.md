# Inspection - Wake 40

## 阶段

第 40 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake39.md`，从 **独立发布维护者 + 新读者克隆项目** 的视角检查：第 39 轮补齐 `.gitignore` 后，项目是否仍然清晰、可运行、可维护。

## 本轮检验了什么

1. 复读入口与维护说明：
   - `README.md`
   - `TODO.md`
   - `rtl/README.md`
   - `sim/README.md`
   - `.gitignore`
   - `notes/changelog_wake39.md`
2. 实际执行根 README 中的新读者路线：
   - `python labs/level0_python_model/demo_layout.py`
   - `python labs/level0_python_model/demo_write_hole.py`
   - `python labs/level0_python_model/demo_rebuild_and_scrub.py`
   - `python -m pytest -q labs/level0_python_model`
   - `python rtl/xor_engine/run_tests.py`
   - `python rtl/lba_mapper/run_tests.py`
3. 模拟项目被单独拷出后初始化独立 Git 仓库：
   - 复制 `temp/fpga-raid-lab` 到临时目录；
   - 在临时目录执行 `git init`；
   - 检查 `git status --short --ignored` 中源码与仿真产物的边界。
4. 检查当前 runner 是否继续把 `.vvp` 产物留在模块目录。

## 及格线结果

通过。

根 README 当前列出的主要可运行入口均能实际执行：

```text
python labs/level0_python_model/demo_layout.py
python labs/level0_python_model/demo_write_hole.py
python labs/level0_python_model/demo_rebuild_and_scrub.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果摘要：

```text
12 passed
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
```

第 39 轮的 `.gitignore` 补丁有效。把项目单独拷出并 `git init` 后，状态显示：

```text
?? .gitignore
?? README.md
?? TODO.md
?? docs/
?? labs/
?? notes/
?? roadmap/
?? rtl/
?? sim/
!! rtl/lba_mapper/tb_lba_mapper.vvp
!! rtl/xor_engine/tb_xor_engine.vvp
```

这说明：

- 教学源码会作为未跟踪内容出现，符合新仓库初始化预期；
- `.vvp` 仿真产物会被忽略，不会误进入首轮提交；
- 第 39 轮解决的是“误提交风险”，不是“目录视觉噪声”。

## 质量判断

当前项目已经达到“新读者按 README 跑起来”的及格线，并且维护边界比第 38 轮更清楚。

比较好的点：

1. **发布边界更稳**  
   即使从上层 GA 仓库中单独拷出，`.gitignore` 也能正确屏蔽 Icarus Verilog 编译产物。

2. **入口命令真实可跑**  
   README 中 Python demo、pytest、两个 RTL runner 都经过实际执行，不只是文档列举。

3. **`sim/` 没有过早工程化**  
   `sim/README.md` 明确说明当前单模块入口仍在 `rtl/<module>/run_tests.py`，这对学习型仓库是合理的：先让读者在模块目录里理解局部问题，再把跨模块仿真收敛到 `sim/`。

## 发现的问题

### P1：runner 仍会把 `.vvp` 留在源码目录，视觉上不像干净发布包

当前实际存在：

```text
rtl/lba_mapper/tb_lba_mapper.vvp
rtl/xor_engine/tb_xor_engine.vvp
```

`.gitignore` 已经防止误提交，但新读者跑完 RTL 后，源码目录里仍会多出二进制/编译产物。对“闯关式实验室”来说，这不是致命问题，但会降低目录的清爽度：

- 读者打开 `rtl/xor_engine/` 时会看到 `tb_xor_engine.vvp`，但它不是学习材料；
- 读者可能误以为 `.vvp` 是必须理解的源文件；
- 后续模块变多后，产物散落会让 `rtl/` 看起来像构建目录。

建议第 41 轮做实质改进：把 `rtl/xor_engine/run_tests.py` 和 `rtl/lba_mapper/run_tests.py` 的默认 `.vvp` 输出改到临时目录，或者统一到一个 ignored 的 `sim_build/`。考虑当前目标是教学清晰，推荐先用 `tempfile.TemporaryDirectory()`，因为它不引入新目录概念，改动半径最小。

### P2：`sim/README.md` 已说明未来方向，但缺一个“未来统一入口”的命令草图

`sim/README.md` 当前的判断是正确的：现在不要把单模块 testbench 都搬进 `sim/`。

但从维护者视角看，它还可以更出色：给出一个未来命令草图，例如：

```bash
python sim/run_all.py --rtl --golden
```

并说明它未来会做三件事：

1. 运行 Python golden model；
2. 运行各 RTL 单模块 runner；
3. 汇总跨模块对拍结果。

这不需要现在实现 `sim/run_all.py`，只要让读者知道 `sim/` 将来如何接住复杂度。

### P2：README 快速路线开始变长，下一次新增 RTL 模块前应拆成两层

根 README 当前仍可接受，但新读者路线已经包含多个 demo、pytest、RTL runner。等 `stripe_manager` 出现后，建议拆成：

- **15 分钟跑通路线**：只跑一个布局 demo、pytest、两个或三个 RTL runner；
- **完整学习路线**：按 docs 页面逐步读 RAID0/1/5、write hole、rebuild/scrub、FPGA architecture。

当前不建议立刻拆，因为还没有出现第三个 RTL 模块；但这是下一阶段可预期的结构压力。

## 不够出色的点

第 39 轮把“别误提交产物”解决了，但还没有解决“产物为什么会出现在源码目录里”。

对一个学习型仓库来说，`.gitignore` 是底线，干净的学习目录才是更好的体验。读者不应该在第一次跑 RTL 后，就需要判断哪些文件是教材、哪些文件是工具产物。

## 下轮建议

第 41 轮进入改进阶段，建议只做一个小闭环：

**把两个 RTL runner 的默认 Icarus 输出移出模块源码目录。**

优先方案：

1. `rtl/xor_engine/run_tests.py`：默认 testbench 编译输出放入 `tempfile.TemporaryDirectory()`；
2. `rtl/lba_mapper/run_tests.py`：同样处理默认 testbench 的 `.vvp`；
3. 保持参数化矩阵现有临时目录策略；
4. 回归验证：
   - 删除或忽略现有 `.vvp` 后运行两个 runner；
   - 确认 `rtl/*/*.vvp` 不再新增；
   - 跑 Python pytest，确认无牵连。

暂不建议本轮实现 `sim/run_all.py`，因为那会把“清理 runner 输出”和“建立统一仿真入口”混成两个闭环。
