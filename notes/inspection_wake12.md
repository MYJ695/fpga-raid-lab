# Inspection Report - Wake 12

## 阶段

第 12 次唤醒：检验阶段。

本轮检验第 11 次唤醒新增的 `docs/raid5_parity.md` 以及 README Step 0~6 路线。原则是不修改交付物，只记录事实核对、实测结果和下一轮改进建议。

## 检验视角

本轮采用四个视角：

1. **懂 FPGA 但不懂 RAID 的读者**：能否把 RAID5 理解成“RAID0 条带化 + XOR 校验”，而不是神秘算法；
2. **测试工程师**：3/4/5 盘、容量不均、所有单盘故障、双盘故障是否与 Python 模型一致；
3. **硬件实现者**：文档能否自然映射到 XOR engine、LBA mapper、stripe manager、rebuild engine；
4. **课程设计者**：README Step 0~6 是否能承接 RAID0、RAID1，再进入 RAID5 write path。

## 实测验证

### 1. RAID5 容量公式

对不同盘数和不等容量成员盘做了容量检查：

```text
capacity (3, 4, 4) 6 expected 6 OK
capacity (4, 3, 5, 6) 9 expected 9 OK
capacity (5, 2, 2, 3, 4) 8 expected 8 OK
```

结论：当前模型使用：

```python
capacity_blocks = min(member_block_count) * (disk_count - 1)
```

这与 RAID5 “少 1 块盘容量，但受最小盘限制”的文档表达一致。

### 2. 3/4/5 盘 parity 轮转

本轮没有只测文档中的 4 盘例子，而是扩展到 3、4、5 盘。

3 盘：

```text
stripe 0 parity 0 ['P', 'D0', 'D1'] OK
stripe 1 parity 1 ['D2', 'P', 'D3'] OK
stripe 2 parity 2 ['D4', 'D5', 'P'] OK
stripe 3 parity 0 ['P', 'D6', 'D7'] OK
```

4 盘：

```text
stripe 0 parity 0 ['P', 'D0', 'D1', 'D2'] OK
stripe 1 parity 1 ['D3', 'P', 'D4', 'D5'] OK
stripe 2 parity 2 ['D6', 'D7', 'P', 'D8'] OK
stripe 3 parity 3 ['D9', 'D10', 'D11', 'P'] OK
```

5 盘：

```text
stripe 0 parity 0 ['P', 'D0', 'D1', 'D2', 'D3'] OK
stripe 1 parity 1 ['D4', 'P', 'D5', 'D6', 'D7'] OK
stripe 2 parity 2 ['D8', 'D9', 'P', 'D10', 'D11'] OK
stripe 3 parity 3 ['D12', 'D13', 'D14', 'P', 'D15'] OK
stripe 4 parity 4 ['D16', 'D17', 'D18', 'D19', 'P'] OK
```

结论：文档中的公式 `parity_disk = stripe % disk_count` 与 `RAID5.layout_row()` 一致。

### 3. LBA 映射一致性

对 3/4/5 盘阵列的前若干 LBA 做了映射检查：

```text
map_lba first range OK
```

检查规则：

- `stripe = lba // (disk_count - 1)`；
- `offset = lba % (disk_count - 1)`；
- `parity = stripe % disk_count`；
- data disk 必须避开 parity disk；
- `disk_lba == stripe`。

结论：文档中的 LBA 7 手算答案也与模型一致：4 盘时，LBA 7 在 `stripe 2`，parity 在 `disk2`，data order 为 `disk0,disk1,disk3`，所以落在 `disk1:block2`。

### 4. XOR 恢复性质

测试 2、3、4 个 data block 的 XOR 恢复：

```text
xor recover 2 data blocks OK
xor recover 3 data blocks OK
xor recover 4 data blocks OK
```

结论：文档中的 `D0 XOR D1 = P`、`D0 = D1 XOR P` 是 3 盘 RAID5 的最小例子；扩展到更多 data block 时仍然成立：缺一个块时，可以用 parity 和剩余数据块 XOR 回来。

### 5. 所有单盘故障矩阵

本轮对 3、4、5 盘阵列逐个 fail 每一块盘，并读取所有 logical LBA：

```text
degraded n 3 fail disk 0 bad []
degraded n 3 fail disk 1 bad []
degraded n 3 fail disk 2 bad []
degraded n 4 fail disk 0 bad []
degraded n 4 fail disk 1 bad []
degraded n 4 fail disk 2 bad []
degraded n 4 fail disk 3 bad []
degraded n 5 fail disk 0 bad []
degraded n 5 fail disk 1 bad []
degraded n 5 fail disk 2 bad []
degraded n 5 fail disk 3 bad []
degraded n 5 fail disk 4 bad []
```

结论：文档说“只坏一块可以 XOR 回来”成立，不依赖坏的是 parity disk 还是 data disk。

### 6. 双盘故障边界

双盘故障检查：

```text
two failed n 4 DiskFailedError True
two failed n 5 DiskFailedError True
```

结论：文档第 183~185 行的边界说明正确：RAID5 只有单个 XOR parity，同一 stripe 缺两个未知数时无法恢复。

### 7. 链接、表格、命令

Markdown 链接：

```text
missing markdown links: []
```

表格格式：

```text
table docs/raid5_parity.md line 9 cols 5 sep 5 OK
table docs/raid5_parity.md line 53 cols 4 sep 4 OK
table docs/raid5_parity.md line 85 cols 6 sep 6 OK
table docs/raid5_parity.md line 113 cols 6 sep 6 OK
table docs/raid5_parity.md line 191 cols 3 sep 3 OK
table README.md line 31 cols 5 sep 5 OK
```

README 推荐命令：

```text
python labs/level0_python_model/demo_layout.py exit 0
python -m pytest -q labs/level0_python_model exit 0
12 passed in 0.06s
```

验证后缓存已清理：

```text
cache dirs after cleanup: [] []
```

## 及格线结论

`docs/raid5_parity.md` 已通过本轮及格线：

1. XOR parity 的手算例子正确；
2. 4 盘 layout 表与当前 Python 模型一致；
3. RAID5 容量、轮转 parity、LBA 映射、单盘 degraded read、rebuild 边界都讲到了；
4. README Step 0~6 的路径可运行，链接无坏链，推荐命令通过；
5. 文档没有把 partial write 混进 full-stripe write，而是在开头和末尾都明确说后续单独拆。

## 不够出色的点

虽然本轮验证通过，但从“闯关式实验室”的目标看，还有几个明显短板。

### 1. README 缺每关通关条件

当前 README 告诉读者“看什么、跑什么”，但没有明确每一关结束时应该能回答什么。例如：

- Level 1 后能不能手算 RAID0 的 `lba -> disk/block`？
- Level 2 后能不能解释 RAID1 单盘故障为什么还能读？
- Level 3 后能不能手算一个 RAID5 degraded read？

这会让路线像目录，而不是“闯关”。

### 2. RAID5 缺独立 degraded read 演示脚本

`demo_layout.py` 能展示 layout，但不能展示“坏一块盘后怎么 XOR 回来”的过程。读者现在需要从文档和 pytest 间接理解 degraded read。

更好的交付物是增加一个小脚本，例如：

```text
labs/level0_python_model/demo_raid5_degraded.py
```

输出类似：

```text
D0 = A000
D1 = B111
D2 = C222
P  = D0 xor D1 xor D2
fail disk2
recover D1 = P xor D0 xor D2
```

这会比单纯 layout 更符合 objective 里“让读者直观看到校验、降级读取和恢复过程”的展示建议。

### 3. RAID5 write path 页应该优先补

当前 parity 页已经多次提醒：只讲 full-stripe write，partial write / write hole 后续拆。但如果下一页不及时出现，读者会停在“RAID5 只是 XOR 一下”的简化认知上。

下一轮改进建议优先补：

```text
docs/raid5_write_path.md
```

重点解释：

- full-stripe write：新数据直接 XOR 出新 parity；
- read-modify-write：读旧数据、旧 parity，算新 parity；
- reconstruct write：读 stripe 里其他未改数据，重新算 parity；
- 为什么 partial write 可能产生 write hole。

### 4. 文档还没明确区分“教学模型”和真实 RAID5 的差距

当前模型只做最小行为闭环，没有讲：

- metadata/superblock；
- disk timeout 与错误上报；
- write ordering / flush / cache；
- bitmap/journal/PPL 这类防 write hole 机制；
- 后台 scrub。

这不是本页必须补完的内容，但在后续 `write_hole.md`、`rebuild_and_scrub.md`、`fpga_architecture.md` 中应逐步说明，避免读者误以为模型等于完整控制器。

## 下轮建议

第 13 次唤醒应进入**改进阶段**。

建议小闭环优先级：

1. 新增 `docs/raid5_write_path.md`；
2. README / TODO 接入该页面；
3. 页面只讲三条写路径：full-stripe write、read-modify-write、reconstruct write；
4. 明确 partial write 为什么比 full-stripe write 麻烦，并自然引出下一页 `write_hole.md`；
5. 写 `notes/changelog_wake13.md`；
6. 验证链接、表格、README 推荐命令、pytest。

如果时间允许，再考虑增加 `demo_raid5_degraded.py`。但为了保持“一轮一个小闭环”，第 13 轮建议先只补 `docs/raid5_write_path.md`，演示脚本留给后续改进。
