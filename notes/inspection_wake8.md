# Inspection Report - Wake 8

## 阶段

第 8 次唤醒：检验阶段。

本轮检验第 7 次唤醒新增的 `docs/raid0_mapping.md` 和主 README 的 Step 0~4 闯关入口。原则是不改交付物，只记录验证结果、读者视角问题和下一轮改进建议。

## 检验视角

本轮采用两个视角：

1. **懂 FPGA 但不懂 RAID 的读者**：能否从公式、表格、布局图理解 LBA 到物理盘地址的关系；
2. **测试工程师**：文档里的映射表和故障结论是否与 Python 模型实际行为一致。

## 实测验证

### 1. RAID0 映射公式与模型一致

对 3 块盘、LBA 0~8 执行交叉检查：

```text
model = RAID0.map_lba(lba)
formula = (lba % 3, lba // 3)
```

结果：

```text
LBA 0..8 model == formula OK
```

说明 `docs/raid0_mapping.md` 中的核心公式与当前 Python 模型一致。

### 2. 坏 disk1 后的可读性表与模型一致

测试步骤：

1. 向 LBA 0~8 写入可区分数据；
2. 令 `disk1.fail()`；
3. 逐个读取 LBA 0~8；
4. 检查 `lba % 3 == 1` 的 LBA 是否失败。

结果：

```text
0 fail? False expected False OK
1 fail? True  expected True  OK
2 fail? False expected False OK
3 fail? False expected False OK
4 fail? True  expected True  OK
5 fail? False expected False OK
6 fail? False expected False OK
7 fail? True  expected True  OK
8 fail? False expected False OK
```

说明文档中“坏 `disk1` 后 LBA 1/4/7 不可读”的说法正确。

### 3. README 推荐命令仍可运行

从仓库根目录执行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
demo exit 0
pytest exit 0
12 passed in 0.16s
```

### 4. 链接检查

```text
README.md TODO.md OK
README.md docs/raid_basics.md OK
README.md docs/raid0_mapping.md OK
README.md labs/level0_python_model/ OK
docs/raid0_mapping.md ../labs/level0_python_model/raid_model.py OK
```

`docs/raid0_mapping.md` 末尾提到的 `docs/raid1_mirror.md` 是下一关建议文本，不是 Markdown 链接；当前文件尚不存在，符合 TODO 状态。

### 5. 临时缓存清理

```text
cache dirs after cleanup: [] []
```

## 及格线判断

通过。

1. 无明显事实错误：公式、表格、坏盘行为均和模型一致；
2. 无路径错误：README 与 RAID0 页链接均可访问；
3. 可运行：README 推荐 demo 与 pytest 均通过；
4. 不混入过程信息：`docs/raid0_mapping.md` 是正式教学页，没有写入“本轮已检验”等中间话术；
5. 风格基本符合目标：先结论、再表格、再代码、再 FPGA 视角。

## 不够出色的点

### 1. 对 chunk size > 1 的过渡还偏口头

文档第 119~121 行提到“如果 chunk 大小不是 1 block，公式要先把 LBA 转成 `chunk_number`”，但没有给出公式。

现在对 Level 0 是正确的，但读者以后看到真实 RAID 资料时，常见 chunk size 往往是 64 KiB、256 KiB、512 KiB。缺少这一步会让读者误以为 RAID0 永远按单个 block 轮转。

建议以后在 `raid0_mapping.md` 或后续 `lba_mapper` 文档中补一个扩展公式：

```text
chunk_number = lba // chunk_blocks
offset       = lba % chunk_blocks
disk_index   = chunk_number % disk_count
disk_lba     = (chunk_number // disk_count) * chunk_blocks + offset
```

但不建议第 9 轮马上做这个，因为当前优先任务仍是补齐 RAID1/RAID5 概念链。

### 2. FPGA 视角还没有落到接口信号

当前页已经说到 `input: host_lba, disk_count` 和 `output: disk_index, disk_lba`，但对于 FPGA 读者，还缺少最小模块接口直觉，例如：

```text
valid/ready
host_lba
member_disk
member_lba
```

这不是错误，只是距离 `rtl/lba_mapper` 还差一层。建议等开始 RTL 小实验前再补，避免现在把 Level 0 文档变重。

### 3. README Step 0~4 顺了，但还缺“看完后你应该会什么”

README 现在能带读者跑起来，但每一步的学习验收标准还不明显。比如 Step 1 看完 RAID0 映射后，读者应该能回答：

- LBA 7 在 3 块盘 RAID0 中落到哪里？
- disk1 坏了哪些 LBA 会失败？
- `map_lba()` 为什么是 `%` 和 `//`？

这可以等后续 README 再做“每关通关条件”。

### 4. 下一关 RAID1 文件尚不存在，末尾建议略有悬空

`docs/raid0_mapping.md` 最后一行建议看 `docs/raid1_mirror.md`，但该文件还未创建。因为它不是链接，所以没有路径错误；但从读者体验看，下一关入口目前是悬空的。

这正好给第 9 轮改进一个明确小闭环：创建 `docs/raid1_mirror.md`。

## 下轮建议

第 9 次唤醒应进入**改进阶段**。建议优先补：

> `docs/raid1_mirror.md`：镜像、故障切换、容量代价。

建议内容保持小闭环：

1. 先给一句话结论：RAID1 把同一份数据写到多块盘；
2. 给双盘 LBA 0~3 镜像表；
3. 说明写路径：host write -> disk0 + disk1；
4. 说明读路径：优先健康盘，坏一块仍可读；
5. 说明容量代价：2 块盘只得到 1 块盘容量；
6. 对应到 `RAID1.write()` / `RAID1.read()`；
7. README / TODO 接上入口。

不建议第 9 轮优先扩展 RAID0 的 chunk size 公式。原因：当前闯关路线更需要先把 RAID0 的“拆散”与 RAID1 的“复制”形成对照，然后再进入 RAID5 的“拆散 + XOR 保护”。
