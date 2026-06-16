# RTL 小模块约定

## 核心结论

`rtl/` 不是“把 Verilog 都扔进来”的杂物间，而是 FPGA RAID Lab 的硬件闯关区。

每个子目录只回答一个小问题：

```text
一个清晰的 RAID/控制逻辑问题 -> 一个小 RTL 模块 -> 一个能失败的 testbench -> 一条可重复命令
```

当前路线：

```text
xor_engine -> lba_mapper -> stripe_manager
```

顺序不是随便排的：

1. `xor_engine`：先掌握 RAID5 parity 的最小硬件原语，也就是 XOR 可恢复性；
2. `lba_mapper`：再掌握 host LBA 如何落到具体 disk 和 disk_lba；
3. `stripe_manager`：最后才把多块请求切成可调度的 chunk/stripe 操作。

先让小模块能独立仿真，再考虑把多个模块接成更大的 datapath。

## 每个 RTL 小模块至少包含什么

推荐目录形状：

```text
rtl/<module_name>/
├── README.md          # 这关解决什么问题、接口是什么、怎么跑
├── <module_name>.v    # Verilog-2001 RTL，先保持接口小而明确
├── tb_<module_name>.v # Icarus Verilog testbench，失败必须非零退出
├── run_tests.py       # 可选：一键生成向量、编译、运行、参数矩阵
└── vectors.txt        # 可选：可读的 golden 输入/期望输出
```

最小要求不是“文件必须多”，而是读者能回答四件事：

1. 这个模块在 RAID 路线里负责哪一小块？
2. 输入、输出和参数分别代表什么？
3. 从仓库根目录执行哪条命令能验证它？
4. 如果结果错了，仿真是否会返回非零退出码？

## runner 约定

优先使用从仓库根目录运行的命令：

```bash
python rtl/<module_name>/run_tests.py
```

runner 应该做这些事：

- 生成或读取 Python golden vectors；
- 调用 `iverilog` 编译 testbench；
- 调用 `vvp` 运行仿真；
- 外部工具缺失时给出友好提示；
- 让错误传播为非零退出码，方便以后接 CI。

`xor_engine` 已经提供了第一版范式：

```bash
python rtl/xor_engine/run_tests.py
```

但不要盲目复制它的所有实现细节。小型参数矩阵可以临时生成 Verilog；更复杂的模块应优先使用固定 testbench + vector 文件，避免 Python 字符串拼出难读的大块 RTL。

## 生成产物约定

当前阶段允许保留少量可读 vector，例如：

```text
rtl/xor_engine/vectors.txt
```

它们是 golden 输入/期望输出，适合拿来对照 RTL 行为；不要把它们和仿真编译垃圾混在一起看。

一键 runner 的默认规则是：

- `*.vvp` 编译输出放进系统临时目录，正常运行后不会留在 `rtl/<module>/`；
- 临时参数化 testbench 也放进系统临时目录；
- `vectors.txt` 仍留在模块目录，因为它是可读教学材料。

手动拆开跑 `iverilog -o rtl/<module>/xxx.vvp ...` 时，会在模块目录留下 `.vvp`。这类文件可以直接删除，且已由 `.gitignore` 忽略：

```text
*.vvp
*.vcd
__pycache__/
```

后续如果多个模块都产生中间文件，优先收敛到临时目录或统一 ignored build 目录，而不是让每个模块随意堆产物。

## `sim/` 和 `rtl/` 怎么分工

当前阶段：

- `rtl/<module>/run_tests.py`：单模块就地回归，适合学习者打开目录直接跑；
- `sim/`：预留给跨模块 testbench、Python golden model 对拍、未来统一入口。

等至少两个 RTL 模块都能独立回归后，再考虑：

```text
sim/run_all.py
```

在那之前，不急着把简单问题复杂化。

## 当前关卡

| 模块 | 状态 | 下一步 |
|---|---|---|
| `xor_engine` | 已有组合 RTL、vector、testbench、一键 runner | 以后再升级 valid/ready 或流水线版本 |
| `lba_mapper` | 已有 RAID0 组合 RTL、vector、testbench、一键 runner | 后续扩展 RAID5 parity rotation / data slot 映射 |
| `stripe_manager` | 已有 README 接口草案 | 先实现 full-stripe write 的 per-disk DATA/PARITY action testbench |
