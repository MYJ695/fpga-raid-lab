# Changelog - Wake 47

## 阶段

第 47 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake46.md`，只做一个小闭环：补强根 README、`rtl/README.md`、`sim/README.md` 之间的路线桥接，让读者更清楚为什么要从 Python 模型走到 RTL runner/testbench 对拍。

## 本轮做了什么

1. 在根 `README.md` 的“当前可运行入口”前，补充当前入口背后的三段分工：
   - Python demo 负责先展示 RAID 行为；
   - Python pytest 保证模型可作为 golden reference；
   - RTL runner 把同一条规则转成 Verilog 并用 vector/testbench 对拍。
2. 在 `rtl/README.md` 的当前路线后，补充 `xor_engine -> lba_mapper -> stripe_manager` 的顺序理由。
3. 在 `sim/README.md` 中补充未来跨模块对拍的具体画面，说明什么情况下 `xor_engine + lba_mapper` 值得进入 `sim/`。

## 修改了哪些文件

- `README.md`
- `rtl/README.md`
- `sim/README.md`
- `notes/changelog_wake47.md`

## 如何验证

### 文档读回

已读回确认三处关键说明存在：

- `README.md` 包含：`Python demo：先把 RAID 行为演给你看`；
- `rtl/README.md` 包含：`顺序不是随便排的`；
- `sim/README.md` 包含：`一个未来的跨模块对拍画面大概是`。

### 回归命令

已从仓库根目录执行：

```bash
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

同时确认仓库内没有 `.vvp/.vcd` 残留。

## 发现了什么问题

本轮未发现新的代码或仿真问题。

当前更清楚的一点是：项目的学习路线已经不只是“列命令”，而是形成了三层闭环：

```text
Python 行为直觉 -> pytest 固化 golden model -> RTL runner/testbench 对拍硬件化结果
```

仍然不够出色的点：`stripe_manager` 还只是路线上的预留关卡。读者现在能理解为什么它排在第三步，但还不能运行它。

## 下轮建议做什么

第 48 轮进入检验阶段。建议换成“测试工程师 + 初学读者”双重视角检查：

1. 根 README 的 Step 7~13 是否和实际命令顺序完全一致；
2. `rtl/README.md` 的模块最小要求是否被 `xor_engine` 和 `lba_mapper` 两个子目录满足；
3. `sim/README.md` 是否会让读者误以为已有跨模块仿真；
4. 是否已经到了可以开始定义 `rtl/stripe_manager/README.md` 的程度，还是还应继续加固 `lba_mapper`。

建议暂不新增代码，除非检验发现当前路线已经足够清楚且 `stripe_manager` 的输入/输出边界也能稳定定义。
