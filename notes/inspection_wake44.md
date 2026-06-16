# Inspection - Wake 44

## 阶段

第 44 次唤醒：检验阶段。

本轮承接 `notes/changelog_wake43.md`，换成“严格新读者 / 文档一致性审查”视角，从根 `README.md` 顺着 RTL 入口走到 `rtl/README.md`、`rtl/xor_engine/README.md`、`rtl/lba_mapper/README.md`、`sim/README.md` 和 `TODO.md`。

检验重点不是再新增功能，而是检查读者照着文档跑时：

1. 是否能从根 README 找到当前真实入口；
2. 推荐命令是否可运行且不污染目录；
3. 手动命令如果会留下产物，是否在足够靠近命令的位置提醒；
4. `sim/` 预留策略和 TODO 下一步是否一致。

## 本轮检验了什么

### 1. 文档路线走读

读回并交叉检查：

- `README.md`
- `rtl/README.md`
- `rtl/xor_engine/README.md`
- `rtl/lba_mapper/README.md`
- `sim/README.md`
- `TODO.md`
- `.gitignore`
- `notes/changelog_wake43.md`

结论：主路线整体成立。根 README 已把 Python demo、Python pytest、`xor_engine` runner、`lba_mapper` runner 都列为当前可运行入口；`rtl/README.md` 已说明 runner 默认把 `.vvp` 放到系统临时目录；`.gitignore` 已忽略 `*.vvp` 和 `*.vcd`。

### 2. 推荐入口实跑

从仓库根目录模拟新读者执行推荐入口：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

实测结果：

```text
12 passed in 0.05s
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
residue after recommended: []
```

这说明推荐路径不仅能跑通，而且符合第 41/43 轮建立的“runner 不在模块目录留下 `.vvp/.vcd`”约定。

### 3. 手动 Icarus 命令复测

继续模拟根 README 里的手动 XOR 命令：

```bash
python rtl/xor_engine/gen_vectors.py
iverilog -o rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/xor_engine.v rtl/xor_engine/tb_xor_engine.v
vvp rtl/xor_engine/tb_xor_engine.vvp
```

实测结果：

```text
PASS xor_engine cases=5
residue after root manual: ['rtl/xor_engine/tb_xor_engine.vvp']
```

随后已清理该 `.vvp`，最终检查：

```text
residue after cleanup: []
```

## 发现的问题

### P1：根 README 的手动命令附近缺少产物提醒

第 43 轮已经在 `rtl/README.md` 和 `rtl/xor_engine/README.md` 补充了说明：手动 `iverilog -o rtl/<module>/xxx.vvp ...` 会留下 `.vvp`，这类文件可以删除且已被 `.gitignore` 忽略。

但根 `README.md` 仍在第 92-98 行直接给出手动 XOR 命令，没有紧跟一句提醒。严格新读者可能只读根 README，不进入 `rtl/xor_engine/README.md`，于是会看到 `rtl/xor_engine/tb_xor_engine.vvp` 留在目录里，并误以为这是必须保留的项目文件。

这不是功能失败，但会削弱“目录清爽”和“读者不困惑”的体验。它也是第 43 轮改进没有完全覆盖到的入口层一致性问题。

### P2：`sim/README.md` 的当前单模块入口只举了 XOR，略落后于现状

`sim/README.md` 当前提示：

```bash
python rtl/xor_engine/run_tests.py
```

但现在 `lba_mapper` 也已有独立 runner，根 README 和 `rtl/README.md` 都把两者作为当前 RTL 关卡。`sim/README.md` 没有错，因为它只是举例说明“当前读者要跑单模块先看 RTL 子目录”，但作为跨模块预留区说明，它应同步列出当前两个单模块入口，避免读者误以为只有 XOR 能跑。

### P3：TODO 的下一步方向仍正确，但应优先补文档一致性再推进 `stripe_manager`

`TODO.md` 中 RTL 下一步是：

- `rtl/lba_mapper`：扩展 RAID5 parity rotation / data slot 映射；
- `rtl/stripe_manager`：把请求切成 stripe/chunk 动作；
- `sim/`：记录 Icarus/Verilator 仿真命令，和 Python golden model 对拍。

从检验结果看，当前不需要马上做 `sim/run_all.py`。原因：推荐 runner 已能无残留跑通，且只有两个单模块实验；提前建统一入口会有过度工程化风险。

更合适的第 45 轮小闭环是先补齐入口文档一致性：

1. 根 README 的手动 XOR 命令后补一句 `.vvp` 产物提醒；
2. `sim/README.md` 当前单模块入口同步列出 `xor_engine` 和 `lba_mapper`；
3. 不新增 `sim/run_all.py`，继续保持预留策略。

## 不够出色的点

当前项目已经“能跑”，但作为闯关式实验室，入口层还可以更像游戏关卡：读者每跑一条命令，都应知道它会产生什么、是否需要清理、下一关在哪里。

现在的不足不是代码，而是信息出现的位置不够贴近用户动作：

- 在模块页能看到 `.vvp` 提醒；
- 但在根 README 直接复制手动命令时看不到；
- 在 `sim/README.md` 能知道 `sim/` 暂不做主入口；
- 但它只列 XOR，没有体现 LBA mapper 已经成为第二个可运行 RTL 关卡。

这类小摩擦会让新读者觉得“项目好像还没收口”，值得在下一轮用很小改动修掉。

## 下轮建议

第 45 轮进入改进阶段，建议只做一个文档一致性闭环：

1. 修改 `README.md`：在手动 XOR 命令块后增加一句：这会留下 `rtl/xor_engine/tb_xor_engine.vvp`，它是可删除的 Icarus 编译产物，已被 `.gitignore` 忽略；若想目录清爽优先使用 runner。
2. 修改 `sim/README.md`：把当前单模块入口从只列 `xor_engine` 改成同时列出：
   - `python rtl/xor_engine/run_tests.py`
   - `python rtl/lba_mapper/run_tests.py`
3. 不创建 `sim/run_all.py`；等至少出现跨模块 testbench 或第三个 RTL 模块后再考虑统一入口。
4. 验证方式：读回相关段落，执行两个 RTL runner，确认 `.vvp/.vcd` 仍无残留。
