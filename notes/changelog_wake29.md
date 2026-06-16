# Changelog - Wake 29

## 阶段

第 29 次唤醒：改进阶段。

本轮根据 `notes/inspection_wake28.md` 的 P0/P1 建议，只做一个小闭环：把第 28 轮临时验证过的 `xor_engine` 参数化测试沉淀成仓库内的一键回归脚本，并把 README 改成第一次接触 RTL 的读者也能按顺序跑通。

## 本轮做了什么

- 新增 `rtl/xor_engine/run_tests.py`：
  - 重新生成默认 `4 x 32-bit` vectors；
  - 编译并运行仓库内 `tb_xor_engine.v`；
  - 临时生成参数化 testbench，额外覆盖 `8x2`、`16x3`、`64x5`；
  - 任一步失败会直接返回非零退出码，适合作为后续 RTL 回归入口。
- 更新 `rtl/xor_engine/README.md`：
  - 增加推荐的一键回归命令；
  - 说明 `run_tests.py` 实际覆盖哪些默认/非默认参数组合；
  - 明确 `vectors.txt` 为纯机器可读 hex 数据，不写表头、不写注释行；
  - 补充 Python baseline 与 RTL 的粒度差异：Python 是 byte/block 视角，RTL 是 fixed-width word 视角。

## 修改了哪些文件

```text
rtl/xor_engine/run_tests.py
rtl/xor_engine/README.md
notes/changelog_wake29.md
```

## 如何验证

在仓库根目录执行：

```bash
python rtl/xor_engine/run_tests.py
python -m pytest -q labs/level0_python_model
```

实测结果：

```text
PASS xor_engine cases=5
PASS_PARAM ww=8 ic=2 cases=3
PASS_PARAM ww=16 ic=3 cases=2
PASS_PARAM ww=64 ic=5 cases=1
PASS xor_engine regression: default + parameter matrix
12 passed in 0.05s
```

这说明：

1. 默认 `32-bit x 4` 的已提交 testbench 仍能跑通；
2. `xor_engine.v` 的参数化不只是文档声明，至少在 `8x2`、`16x3`、`64x5` 上通过了真实 Icarus 编译与仿真；
3. Python Level 0 baseline 没有被 RTL 实验改动破坏。

## 发现了什么问题

- `run_tests.py` 现在仍是 `xor_engine` 专用脚本；当后续加入 `lba_mapper`、`stripe_manager` 后，可能需要再抽一层 `sim/run_all.py` 或 Makefile。
- `tb_xor_engine.v` 仍只支持固定 `4 x 32-bit` vector 文件；参数矩阵测试目前由 Python runner 临时生成 testbench 完成，尚未统一成可复用的 Verilog 参数化 testbench 模板。
- 坏 vector 的行为还没有系统化测试：README 已提示不写注释/表头，但 testbench 对短行/脏行的报错仍不够教学友好。

## 下轮建议做什么

第 30 次唤醒应进入检验阶段，建议换成 **新读者 + RTL 回归维护者** 视角审查：

1. 从根 README 是否能自然发现并运行 `rtl/xor_engine/run_tests.py`；
2. `run_tests.py` 的失败信息是否足够定位“缺 iverilog / 编译失败 / 仿真输出不匹配”；
3. 临时 testbench 生成方式是否会成为后续 `lba_mapper` 的坏先例；
4. 是否应该在开工 `lba_mapper` 前，先规划一个轻量 `sim/` 回归入口。
