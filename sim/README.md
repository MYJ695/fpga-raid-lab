# sim - 跨模块仿真预留区

## 核心结论

`sim/` 现在不是主要入口，而是给后续“多个 RTL 模块一起对拍”预留的位置。

当前读者要跑单模块，请先看：

```bash
python rtl/xor_engine/run_tests.py
python rtl/lba_mapper/run_tests.py
```

等 `stripe_manager` 也有独立回归，或者出现 `xor_engine + lba_mapper` 联合对拍后，再把跨模块总入口收敛到这里。

一个未来的跨模块对拍画面大概是：

```text
给定一组 host LBA + data blocks：
lba_mapper 决定它们落到哪些 disk/chunk；
xor_engine 计算同一 stripe 的 parity；
Python golden model 给出期望布局与 parity；
sim/ 比较整条路径是否一致。
```

## 目录分工

```text
sim/
├── golden_model/   # 未来放跨模块 Python golden model 或导出的测试向量
└── testbenches/    # 未来放跨模块/系统级 testbench
```

当前这两个目录可以为空。它们表示路线图，不表示已有完整仿真平台。

## 什么时候把东西放进 sim/

适合放进 `sim/` 的内容：

- `xor_engine + lba_mapper` 联合对拍；
- 多模块共享的 vector 格式；
- 未来 `sim/run_all.py`；
- Verilator/Icarus 的系统级仿真脚本；
- Python golden model 与 RTL 输出的统一比较器。

不急着放进 `sim/` 的内容：

- 只有一个模块使用的简单 testbench；
- 某个模块自己的 README；
- 单模块局部 runner。

## 当前策略

```text
单模块学习入口：rtl/<module>/run_tests.py
跨模块回归入口：sim/ 以后再建立
```

这样做的好处是：

1. 新手打开 `rtl/xor_engine/` 就能跑，不需要先理解全局仿真框架；
2. 后续模块增多时，又有地方承接统一回归；
3. 项目不会在第一块 RTL 还很小时，就被过度工程化。
