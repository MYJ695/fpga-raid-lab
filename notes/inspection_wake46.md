# Inspection - Wake 46

## 阶段

第 46 次唤醒：检验阶段。

本轮按第 45 轮建议，换成“懂 FPGA 但不懂 RAID 的读者”视角，不再只检查命令能不能跑，而是检查文档是否能解释清楚这条学习路线：

```text
Python 模型负责行为直觉和 golden reference；
RTL 小模块负责把一个局部逻辑问题硬件化；
runner/testbench 负责把两者用 vector 对拍。
```

## 本轮做了什么

1. 走读根 `README.md`、`rtl/README.md`、`sim/README.md`。
2. 补读两个当前 RTL 关卡说明：
   - `rtl/xor_engine/README.md`
   - `rtl/lba_mapper/README.md`
3. 从读者视角检查是否存在“能跑但不知道为什么跑”的断点。
4. 实测 README 推荐的 Python 与 RTL 入口，确认路线不是只在文档中成立。

## 检验对象

- `README.md`
- `rtl/README.md`
- `sim/README.md`
- `rtl/xor_engine/README.md`
- `rtl/lba_mapper/README.md`

## 检验结果

### 1. 及格线：可运行入口仍然成立

已执行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

结果：

```text
12 passed in 0.05s
PASS xor_engine regression: default + parameter matrix
PASS lba_mapper regression: default + parameter matrix
```

说明当前 README 推荐的路线仍能实际跑通：先看 Python 行为，再跑 RTL 小模块对拍。

### 2. 根 README：路线存在，但“为什么从 Python 跳到 RTL”还不够醒目

优点：

- 根 README 的“当前优先级”已经给出主线：

```text
Python golden model → RAID0/1/5 行为跑通 → RAID5 写路径风险 → rebuild/scrub 维护路径 → FPGA 架构边界 → RTL XOR/lba_mapper → testbench 对拍
```

- “当前可运行入口”列出了 Python demo、pytest、两个 RTL runner。
- 手动 XOR/Icarus 命令后已补充 `.vvp` 残留说明，避免读者误以为产生了必须提交的文件。

不够出色的点：

- 对懂 FPGA 但不懂 RAID 的读者来说，根 README 仍偏“路线清单”，缺少一个非常短的桥接解释：
  - 为什么 `xor_engine` 是 RAID5 的第一块硬件砖；
  - 为什么 `lba_mapper` 先从 RAID0 而不是 RAID5 开始；
  - vector 对拍到底是在证明“RTL 与 Python 模型对同一规则给出同一答案”。

这不是功能错误，但会让第一次进入项目的读者知道“要跑什么”，却未必立刻知道“为什么先跑它”。

### 3. `rtl/README.md`：模块规范清楚，但关卡顺序解释偏薄

优点：

- `rtl/README.md` 明确了硬件闯关区的约束：

```text
一个清晰的 RAID/控制逻辑问题 -> 一个小 RTL 模块 -> 一个能失败的 testbench -> 一条可重复命令
```

- 对 runner 的职责写得清楚：生成/读取 golden vectors、调用 `iverilog`、调用 `vvp`、错误非零退出。
- `rtl/` 与 `sim/` 的分工也清楚：单模块先放 `rtl/<module>/run_tests.py`，跨模块以后放 `sim/`。

不够出色的点：

- 当前路线只写了：

```text
xor_engine -> lba_mapper -> stripe_manager
```

但没有在 `rtl/README.md` 中直接解释这三个名字为什么是这个顺序。虽然两个子模块 README 各自解释得不错，但总入口页应该用 3~5 行把顺序讲透：

1. `xor_engine`：先掌握 RAID5 parity 的 XOR 可恢复性；
2. `lba_mapper`：再掌握逻辑地址如何落到盘和盘内地址；
3. `stripe_manager`：最后才处理跨 chunk/stripe 的请求切分与调度。

否则读者会理解每个模块，却不一定理解闯关顺序。

### 4. `sim/README.md`：边界清楚，但缺少“何时升级到跨模块”的具体触发例子

优点：

- 已明确当前 `sim/` 不是主入口。
- 已列出两个当前单模块入口：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

- 已说明等 `stripe_manager` 或 `xor_engine + lba_mapper` 联合对拍出现后，再收敛到这里。

不够出色的点：

- 对读者来说，“联合对拍”仍有一点抽象。可以补一个未来例子：

```text
给定一组 host LBA + data blocks：
lba_mapper 决定它们落到哪些 disk/chunk；
xor_engine 计算同一 stripe 的 parity；
Python golden model 给出期望布局与 parity；
sim/ 比较整条路径。
```

这个例子会更清楚地解释 `sim/` 为什么不是空目录，而是未来系统级对拍的位置。

### 5. 子模块 README：局部解释强，是当前最稳的部分

`rtl/xor_engine/README.md` 已经很好地解释：

- 它是从 Python golden model 走向 RTL 的第一块砖；
- 对应 Python `xor_blocks([...])`；
- 第一版故意保持纯组合；
- 先验证 RAID5 parity 的核心事实：

```text
A ^ B ^ C = P
A ^ B ^ P = C
```

`rtl/lba_mapper/README.md` 也解释清楚：

- 第一关只做 RAID0 LBA 到 `disk_index + disk_lba`；
- 先 RAID0，再 RAID5，避免一次进入公式迷宫；
- 后续再拆 RAID5 `layout_row(row)` 的 parity rotation 与 data slot 映射；
- 明确这是教学版组合映射，不是最终 datapath。

结论：两个子模块说明质量高，问题主要在上层 README 没有把这些解释浓缩回主路线。

## 发现了什么问题

没有发现新的可运行性问题。

发现的主要问题是“上层路线桥接还不够强”：

1. 根 README 让读者知道命令顺序，但对 `Python golden model -> RTL vector 对拍` 的意义解释不够醒目；
2. `rtl/README.md` 列出 `xor_engine -> lba_mapper -> stripe_manager`，但缺少顺序理由；
3. `sim/README.md` 说明了现在不该放什么，但未来跨模块对拍的具体画面还可以更清楚。

## 不够出色的判断

当前文档已经及格：能跑、路径正确、没有明显误导。

但距离“闯关式实验室”还差一点导游感。读者如果直接从根 README 进入，可能会形成这样的体验：

```text
我知道下一条命令是什么，
但我还要自己拼出为什么 XOR、LBA mapper、sim/ 预留区会组成一条 RAID 硬件化路线。
```

这类问题不适合靠大重写解决，适合下轮做一个小而精准的桥接补丁。

## 下轮建议做什么

第 47 轮进入改进阶段，建议只做一个小闭环：补“路线桥接说明”，不要改代码。

优先改动：

1. 在根 `README.md` 的当前优先级或可运行入口附近，加一个短小段落，解释：

```text
Python demo 先展示 RAID 行为；
Python pytest 保证模型可作为 golden reference；
RTL runner 把同一规则转成 Verilog 并用 vector/testbench 对拍。
```

2. 在 `rtl/README.md` 的当前路线后补 3 行顺序理由：

```text
先 XOR：掌握 RAID5 parity 的最小硬件原语；
再 LBA mapper：掌握地址落盘；
再 stripe_manager：把多块请求切成可调度的 stripe 操作。
```

3. 在 `sim/README.md` 补一个未来跨模块对拍例子，解释何时 `xor_engine + lba_mapper` 才值得进入 `sim/`。

建议不改：

- 暂不创建 `sim/run_all.py`；
- 暂不动 Verilog；
- 暂不重写两个子模块 README。
