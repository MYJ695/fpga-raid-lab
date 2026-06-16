# Changelog - Wake 31

## 阶段

第 31 次唤醒：改进阶段。

本轮根据 `notes/inspection_wake30.md` 的检验结论，收敛 `rtl/xor_engine/run_tests.py` 作为第一块 RTL 小模块的一键回归入口，让它更适合作为后续 `lba_mapper`、`stripe_manager` 的维护范式。

## 改动

1. 更新根 `README.md` 的通关命令：
   - 把 `python -m pytest -q labs/level0_python_model` 和 `python rtl/xor_engine/run_tests.py` 明确列为当前快速验证关卡；
   - 保留手动 `gen_vectors.py` / `iverilog` / `vvp` 命令，但降级为“想拆开看时再跑”；
   - 说明当前策略：单模块 runner 暂放模块目录，第二个 RTL 模块出现后再考虑 `sim/run_all.py`。
2. 更新 `rtl/xor_engine/run_tests.py`：
   - 捕获外部工具缺失时的 `FileNotFoundError`；
   - 对缺少 `iverilog` / `vvp` 一类问题输出项目级提示：安装 Icarus Verilog，并确认工具在 `PATH`。
3. 更新 `rtl/xor_engine/tb_xor_engine.v`：
   - 当 vector 为空或结果 mismatch 时，除了打印 `FAIL`，还调用 `$finish_and_return(1)`；
   - 避免只看 `vvp` 退出码时误把失败仿真当成成功。

## 验证

已执行：

```bash
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
```

结果：

```text
12 passed
PASS xor_engine regression: default + parameter matrix
```

额外做了两个失败路径验证：

1. 临时注入错误版 `xor_engine.v`，确认 testbench mismatch 时 `vvp` 返回非零；
2. 直接调用 runner 的 `run()` 函数模拟缺失外部工具，确认提示包含：
   - `missing external tool: ...`
   - `Install Icarus Verilog and make sure both iverilog and vvp are on PATH.`
   - `Then rerun: python rtl/xor_engine/run_tests.py`

## 结论

第 30 轮提出的四个小缺口已闭环：

- 根 README 现在能发现一键 RTL 回归入口；
- 缺工具时不再只暴露 Python traceback；
- testbench 失败路径具备非零退出语义；
- `sim/` 统一入口暂缓策略已在 README 中说明。

下一轮建议切回检验阶段，用“第二个 RTL 模块的维护者”视角检查：当前 runner 范式是否足以复制到 `lba_mapper`，以及是否需要在 `rtl/README.md` 或 `sim/README.md` 建立更早的目录级约定。
