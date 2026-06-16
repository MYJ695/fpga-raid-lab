# Inspection - Wake 32

## 阶段

第 32 次唤醒：检验阶段。

本轮换成 **第二个 RTL 模块维护者** 视角：假设下一轮要开始做 `rtl/lba_mapper`，检查第 31 轮收敛后的 `xor_engine` 回归范式是否足够容易复制，是否会误导后续模块，以及仓库当前状态是否仍符合“闯关式实验室”的目标。

## 检验范围

读取并检查：

- `README.md`
- `TODO.md`
- `docs/fpga_architecture.md`
- `notes/changelog_wake31.md`
- `notes/inspection_wake30.md`
- `rtl/xor_engine/README.md`
- `rtl/xor_engine/run_tests.py`
- `rtl/xor_engine/xor_engine.v`

实际执行：

```bash
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```

并额外查看：

```bash
rtl/lba_mapper/
rtl/stripe_manager/
sim/
sim/golden_model/
sim/testbenches/
git status --short -- .
git ls-files rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/__pycache__/run_tests.cpython-313.pyc rtl/xor_engine/vectors.txt
```

## 结论

第 31 轮已经把第 30 轮的 P0/P1 问题基本闭环：根 README 能发现 RTL runner，缺工具提示更友好，testbench 失败路径有非零退出语义，基础回归真实通过。

但从“第二个 RTL 模块要开工”的角度看，当前仓库仍有三个不够出色的点：

1. `rtl/lba_mapper/` 与 `rtl/stripe_manager/` 已经存在但为空，读者会误以为已有内容或进入死胡同；
2. `sim/` 目录也存在但为空，和 README 中“仿真和 golden model”的描述仍有落差；
3. `xor_engine` 的 runner 范式可用，但还没有被提炼成“下一块 RTL 模块应该照着做什么、不该照着复制什么”的目录级约定。

这些不是阻塞性 bug，但会影响项目从“一块能跑的 RTL”走向“可持续扩展的 RTL 实验室”。

## 实测结果

### 基础回归仍然通过

```text
$ python rtl/xor_engine/run_tests.py
PASS xor_engine regression: default + parameter matrix

$ python -m pytest -q labs/level0_python_model
12 passed in 0.05s
```

说明第 31 轮的 runner 与 testbench 改动没有破坏现有可运行性。

### 仓库子树状态干净

限定在 `temp/fpga-raid-lab` 子树查看：

```text
$ git status --short -- .
<empty>
```

注意：从更上层仓库看有大量 GA 自身文件变化，但本任务限制在 `temp/fpga-raid-lab` 内，本轮没有触碰那些文件。

### 生成产物未被 git 跟踪

```text
$ git ls-files rtl/xor_engine/tb_xor_engine.vvp rtl/xor_engine/__pycache__/run_tests.cpython-313.pyc rtl/xor_engine/vectors.txt
<empty>
```

这说明 `tb_xor_engine.vvp`、`__pycache__`、`vectors.txt` 目前不是已跟踪源码。它们会在本地运行后出现，但不会直接污染版本库。

## 发现的问题

### P1 - 空 RTL 目录会制造“下一关已经有入口”的错觉

当前目录存在：

```text
rtl/lba_mapper/
rtl/stripe_manager/
```

但二者均为空。

这对维护者和读者都有一点危险：

- 维护者不知道下一轮是否应该直接填代码，还是先补 README / 接口草案；
- 读者看到根 README 的路线后进入目录，只会看到空目录；
- “闯关式实验室”的节奏被打断：上一关 `xor_engine` 很完整，下一关却没有关卡说明。

下一轮最小改进不一定要直接实现完整 `lba_mapper`，更适合先给 `rtl/lba_mapper/README.md` 建立关卡边界：输入是什么、输出是什么、先支持 RAID0 还是 RAID5、暂不处理什么。

### P1 - `sim/` 目录仍缺少占位说明，和路线图不完全对齐

当前目录存在：

```text
sim/golden_model/
sim/testbenches/
```

但两个子目录为空。

第 31 轮在根 README 中解释了“第二个 RTL 模块出现后再考虑 `sim/run_all.py`”，这个策略合理；但 `sim/` 本身没有 README，导致从文件系统进入的读者仍会困惑：

> 这里是现在应该使用的仿真入口，还是未来预留？

最小改进可以是新增 `sim/README.md`，明确：

- 当前唯一可运行 RTL 回归仍在 `rtl/xor_engine/run_tests.py`；
- `sim/` 暂时承接未来跨模块 testbench / golden model 对拍；
- 何时升级到统一 runner：至少两个 RTL 模块都能独立回归后。

### P1 - `xor_engine` runner 范式仍未提炼成目录级约定

`rtl/xor_engine/run_tests.py` 现在工程上可用，但后续 `lba_mapper` 不应该盲目复制其中所有做法。

值得保留的模式：

- 一条 Python 命令从仓库根目录运行；
- 先生成或读取 golden vectors；
- 调用 Icarus Verilog 编译/运行；
- 失败时给出清晰错误；
- testbench 自己负责非零失败语义。

不宜直接复制的模式：

- 大量 Python 字符串拼临时 Verilog；
- 每个模块各自发明输出格式；
- 每个模块各自决定生成产物放在哪里；
- 没有说明 vector 文件是源码、缓存还是运行产物。

下一轮可以新增 `rtl/README.md`，用很短的“RTL 小模块约定”固定这些规则。这样后续做 `lba_mapper` 时，不需要重新讨论 runner 结构。

### P2 - 运行产物位置对新手仍有轻微干扰

运行 `python rtl/xor_engine/run_tests.py` 后，本地会出现：

```text
rtl/xor_engine/vectors.txt
rtl/xor_engine/tb_xor_engine.vvp
rtl/xor_engine/__pycache__/
```

这些当前未被 git 跟踪，不是版本污染。但从学习体验看，源码目录里混入 `.vvp` 和缓存，会让新手分不清哪些文件应该阅读、哪些可以删除。

这不是下一轮最高优先级；但当开始做第二个 RTL 模块时，建议顺手规定：

- 可读输入向量可以保留在模块目录；
- 编译产物优先放临时目录或统一 ignored build 目录；
- README 里标注哪些文件是运行生成的。

## 对第 31 轮改进的评价

第 31 轮没有过度重构，这是对的。它修掉了入口、缺工具提示和失败退出码三个实用问题，并保持了单模块 runner 的轻量。

真正需要升级的是“目录级可扩展性”，不是 `xor_engine` 本身。也就是说，下一轮不应再继续打磨 XOR 细节，而应把项目从单点样例推进到第二块 RTL 模块的准备状态。

## 下轮建议

第 33 轮改进阶段建议做一个小闭环：**建立 RTL 扩展约定，而不是马上写复杂 RTL。**

推荐改动：

1. 新增 `rtl/README.md`：说明每个 RTL 小模块至少包含 `README.md`、`.v`、`tb_*.v` 或 runner、可运行命令、失败语义；
2. 新增 `rtl/lba_mapper/README.md`：定义下一关最小边界，建议先做 RAID0 LBA → disk/chunk 映射，再扩到 RAID5 parity rotation；
3. 新增 `sim/README.md`：说明当前 `sim/` 是未来跨模块对拍区，避免空目录困惑；
4. 更新 `TODO.md`：把 `lba_mapper` 拆成“README/接口草案”和“最小 RTL + testbench”两个任务。

验证方式：

```bash
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
```

并检查新增 README 链接从根 README / TODO 能被发现。
