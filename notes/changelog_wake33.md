# Changelog - Wake 33

## 阶段

第 33 次唤醒：改进阶段。

本轮承接 `notes/inspection_wake32.md` 的结论：`xor_engine` 已经形成可运行范式，但 `rtl/lba_mapper/`、`rtl/stripe_manager/`、`sim/` 的入口感还不够清晰。目标不是马上写复杂 RTL，而是先把下一关的边界和目录约定讲清楚。

## 本轮做了什么

核心改进：建立 RTL 扩展约定，让后续模块维护者知道“下一块砖怎么加”。

具体包括：

1. 新增 `rtl/README.md`
   - 说明 `rtl/` 是硬件闯关区，不是 Verilog 杂物间；
   - 定义单模块目录建议形状；
   - 明确 runner 约定：从仓库根目录运行、调用 Icarus/VVP、错误非零退出；
   - 说明 `rtl/<module>/run_tests.py` 与未来 `sim/run_all.py` 的分工；
   - 标出当前路线：`xor_engine -> lba_mapper -> stripe_manager`。

2. 新增 `rtl/lba_mapper/README.md`
   - 把下一关限定为 RAID0 LBA 映射，而不是直接跳到 RAID5 全功能映射；
   - 给出第一版建议接口；
   - 写清 RAID0 映射公式；
   - 给出小样例测试点；
   - 说明后续再扩展 RAID5 parity rotation / data slot 映射。

3. 新增 `sim/README.md`
   - 解释 `sim/` 当前是跨模块仿真预留区；
   - 避免读者看到空目录误以为已有完整仿真平台；
   - 说明单模块 runner 仍放在 `rtl/<module>/`，未来多模块对拍再收敛到 `sim/`。

4. 更新 `README.md`
   - 在当前可运行入口中补充 `rtl/README.md`、`rtl/lba_mapper/README.md`、`sim/README.md`；
   - 让新读者能从根 README 找到 RTL 约定和下一关边界。

5. 更新 `TODO.md`
   - 将 `lba_mapper` 拆成两步：先 README/边界，再基础 RTL + testbench；
   - 单独列出未来 RAID5 parity rotation / data slot 映射；
   - 标记 `rtl/README.md` 与 `sim/README.md` 已完成。

## 修改了哪些文件

```text
README.md
TODO.md
rtl/README.md
rtl/lba_mapper/README.md
sim/README.md
notes/changelog_wake33.md
```

## 如何验证

### 1. Python golden model 回归

```bash
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.05s
```

### 2. RTL XOR 回归

```bash
python rtl/xor_engine/run_tests.py
```

结果：

```text
PASS xor_engine regression: default + parameter matrix
```

### 3. Markdown 可读性与本地链接检查

检查文件：

```text
README.md
TODO.md
rtl/README.md
rtl/lba_mapper/README.md
sim/README.md
```

结果：

```text
changed markdown files readable; local links exist
```

## 发现了什么问题

1. `lba_mapper` 的 README 已经给出建议接口，但还没有真正的 RTL/testbench；下一轮如果继续改进，最自然的小闭环就是实现 RAID0 组合映射模块。
2. `stripe_manager` 仍然只是目录预留；这符合当前路线，但下一次检验需要确认读者不会误以为它已经可运行。
3. `sim/` 已经有定位说明，但仍没有实际 runner；需要等至少两个 RTL 模块存在后再建立统一入口，避免过度工程化。

## 下轮建议

第 34 轮按交替规则应进入检验阶段。

建议视角：**RTL 初学者 + testbench 作者**。

重点检查：

1. `rtl/lba_mapper/README.md` 的接口是否足够让人无歧义地写 Verilog；
2. `disk_chunk`、`stripe_index`、`disk_lba` 的命名是否会误导；
3. `DISK_COUNT` 非 2 的幂时，Verilog 组合除法/取模是否会给读者留下“硬件成本被隐藏”的风险；
4. `rtl/README.md` 的 runner 约定是否真的能复制到 `lba_mapper`；
5. 根 README / TODO 是否能引导读者发现新文档。

如果检验通过，第 35 轮再做 `rtl/lba_mapper/lba_mapper.v`、`tb_lba_mapper.v` 和 `run_tests.py` 的最小实现。
