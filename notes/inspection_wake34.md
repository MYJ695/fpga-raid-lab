# Inspection - Wake 34

## 阶段

第 34 次唤醒：检验阶段。

本轮从 **RTL 初学者 + testbench 作者** 视角检验第 33 轮新增的 RTL 目录约定，重点看 `rtl/lba_mapper/README.md` 是否足够支撑下一轮直接写最小 Verilog + testbench。

## 检验对象

- `rtl/README.md`
- `rtl/lba_mapper/README.md`
- `sim/README.md`
- 根 `README.md` / `TODO.md` 中的入口链接
- Python golden model 中的 `RAID0.map_lba()`
- 已有可运行回归：Level 0 Python 测试、`xor_engine` runner

## 本轮如何检验

### 1. 读者路径检验

从根 README 进入：

```text
README.md -> rtl/README.md -> rtl/lba_mapper/README.md
```

结论：路径成立。根 README 已能把读者带到 RTL 小模块区，`rtl/README.md` 也明确了当前路线：

```text
xor_engine -> lba_mapper -> stripe_manager
```

这比第 32 轮看到的“空目录感”明显好。

### 2. Python golden model 对齐检验

Python 模型里 RAID0 地址映射为：

```python
return lba % len(self.disks), lba // len(self.disks)
```

`rtl/lba_mapper/README.md` 里的第一版公式在 `CHUNK_SHIFT = 0` 时退化为：

```text
logical_chunk = lba
disk_index    = lba % DISK_COUNT
stripe_index  = lba / DISK_COUNT
disk_lba      = stripe_index
```

结论：与 Python 模型一致。

### 3. 测试作者视角检验

`lba_mapper` README 已给出两组关键测试形状：

1. `DISK_COUNT=4, CHUNK_SHIFT=0` 的基础条带映射；
2. `DISK_COUNT=3, CHUNK_SHIFT=2` 的多 LBA chunk 形状。

这已经足够写出第一版 testbench 的正例表。

但还不够出色：

- 缺少明确的 **负例/边界例**：例如最大 LBA、`CHUNK_SHIFT` 造成的 `chunk_offset` 边界、`DISK_COUNT=3` 非 2 的幂成本提醒；
- 没有规定 `LBA_WIDTH`、`DISK_INDEX_WIDTH`、`DISK_LBA_WIDTH` 这些 Verilog 参数，下一轮写 RTL 时仍会临场决定；
- 没有说明第一版是否允许 `DISK_COUNT` 作为运行时输入，还是只允许 parameter 固定。对硬件初学者来说，这会直接影响 `%` 和 `/` 的综合含义。

### 4. 可运行性回归

实际运行：

```bash
python -m pytest -q labs/level0_python_model
python rtl/xor_engine/run_tests.py
```

结果：

```text
12 passed in 0.05s
PASS xor_engine regression: default + parameter matrix
```

说明第 33 轮文档改动没有破坏现有 Python 模型和 RTL 小模块回归。

### 5. 文档可读与链接检验

检查文件：

```text
README.md
TODO.md
rtl/README.md
rtl/lba_mapper/README.md
sim/README.md
notes/changelog_wake33.md
```

结果：

```text
readability+local-links ok
```

未发现乱码或本地 Markdown 链接断裂。

## 发现的问题

### P1 - 下一轮可以写 RTL，但接口还差最后一层“硬件参数钉死”

现在 README 已讲清楚算法公式，但还没有钉死 Verilog 模块接口。例如：

```text
module lba_mapper #(
  parameter LBA_WIDTH = ?,
  parameter DISK_COUNT = ?,
  parameter CHUNK_SHIFT = ?
)(...);
```

如果不先补这层，下一轮实现容易在端口命名、位宽和是否输出 `disk_lba` 上摇摆。

### P1 - 需要明确第一版只做 parameter 固定 DISK_COUNT

`DISK_COUNT` 如果作为运行时输入，`%` 和 `/` 会让综合成本解释变复杂；如果作为 parameter，testbench 可以通过多次编译覆盖 3/4/5 盘配置。当前文档提到了非 2 的幂成本，但还没把第一版策略钉死。

建议第一版明确：

```text
DISK_COUNT 是 parameter，不是运行时输入。
```

这样更符合“最小、可验证、可复制”的闯关路线。

### P2 - `stripe_index` / `disk_chunk` / `disk_lba` 命名仍可能让初学者混淆

README 同时出现：

- `stripe_index`
- `disk_chunk`
- `disk_lba`

文档已解释它们，但下一轮写 RTL 时最好只输出一个最终物理地址名，例如：

```text
disk_lba = stripe_index * chunk_size + chunk_offset
```

并在注释里说明：当 `CHUNK_SHIFT=0` 时，`disk_lba == stripe_index`。

### P2 - 测试点还缺“跨 chunk offset”的显式断言

已有 `CHUNK_SHIFT=2` 的布局形状很好，但 testbench 作者还需要更机械的期望值表，例如：

```text
DISK_COUNT=3, CHUNK_SHIFT=2
LBA 3  -> disk0, disk_lba 3
LBA 4  -> disk1, disk_lba 0
LBA 11 -> disk2, disk_lba 3
LBA 12 -> disk0, disk_lba 4
```

这能直接抓住 `chunk_offset` 和 `stripe_index` 的 off-by-one 错误。

### P3 - `stripe_manager` 空目录仍然容易被误会

第 33 轮已经在 `rtl/README.md` 说明 `stripe_manager` 是目录预留，但物理目录仍为空。短期可接受；等 `lba_mapper` 实现后，建议给 `rtl/stripe_manager/README.md` 加一页“不急着做什么”。

## 及格线判断

通过。

第 33 轮改进已经解决第 32 轮提出的主要问题：RTL 目录不再像散落文件，`lba_mapper` 有了明确入口，`sim/` 也不再是沉默空目录。

## 不够出色的点

它已经像“路线说明”，但还不像“下一轮可以无脑照抄的 RTL 规格”。

差距集中在三件事：

1. Verilog module 端口和参数还没固定；
2. `DISK_COUNT` 的硬件策略还没明确为 parameter；
3. 测试向量还缺边界表。

## 下轮建议

第 35 轮进入改进阶段，建议不要直接写完整 RTL，先做一个更小闭环：

1. 在 `rtl/lba_mapper/README.md` 补“第一版 RTL 规格”：module 参数、端口、输出含义；
2. 明确 `DISK_COUNT` 第一版是 parameter，`CHUNK_SHIFT` 也是 parameter；
3. 补一张 `CHUNK_SHIFT=2` 的逐 LBA 期望表；
4. 然后再实现：
   - `rtl/lba_mapper/lba_mapper.v`
   - `rtl/lba_mapper/tb_lba_mapper.v`
   - `rtl/lba_mapper/run_tests.py`

如果时间有限，优先完成 1~3；这样第 36 轮检验会更有抓手。
