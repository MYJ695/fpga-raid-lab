# Inspection - Wake 20

## 阶段

第 20 次唤醒：检验阶段。

本轮检验第 19 轮改进成果，重点不是再看“能不能跑”，而是用更苛刻的教学视角检查：

1. **初学读者视角**：手算段和 RAID5 模型段是否连得上；
2. **模型真实性视角**：demo 是否真的调用现有 `RAID5` 对象，而不是只做字符串展示；
3. **路线一致性视角**：README、TODO、docs 是否和 Level 0~4 的当前路线一致；
4. **测试工程师视角**：脚本、测试、关键输出是否可实测。

## 检验对象

- `labs/level0_python_model/demo_write_hole.py`
- `README.md`
- `TODO.md`
- `docs/write_hole.md`
- `notes/changelog_wake19.md`

## 实测结果

从仓库根目录执行：

```bash
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
12 passed in 0.06s
```

`demo_write_hole.py` 能正常运行，输出包含：

- `Case A: data new, parity old`
- `Case B: parity new, data old`
- `RAID5 model cross-check`
- `Mini challenge`

模型段实测输出符合预期：

```text
Model check - data new, parity old
normal RAID5.read(1)   : 0x0f
degraded RAID5.read(1) : 0xcc  (disk2 failed, reconstructs D1)

Model check - parity new, data old
normal RAID5.read(1)   : 0xcc
degraded RAID5.read(1) : 0x0f  (disk2 failed, reconstructs D1)
```

这说明第 19 轮确实把 write hole 从“纯 XOR 手算”推进到了“现有 RAID5 模型交叉验证”。

## 及格线检查

### 1. 代码可运行

通过。

- demo 运行成功；
- pytest 全部通过；
- 未发现路径错误；
- 未发现导入错误。

### 2. 确实使用 RAID5 模型

通过。

`demo_write_hole.py` 导入：

```python
from raid_model import RAID5, VirtualDisk, xor_blocks
```

并在模型段实际创建：

```python
RAID5([VirtualDisk(...) for idx in range(4)])
```

随后通过：

- `raid.write_full_stripe(...)`
- `raid.read(1)`
- `raid.disks[2].fail()`
- 再次 `raid.read(1)`

展示 normal read 与 degraded read 的差异。

### 3. README 路线跟上当前内容

通过。

README 已从：

```text
Level 0 ~ Level 3
```

更新为：

```text
Level 0 ~ Level 4
```

并把路线写成：

```text
Python golden model → RAID0/1/5 行为跑通 → RAID5 写路径风险 → RTL XOR/lba_mapper → testbench 对拍
```

当前可运行入口也包含：

```bash
python labs/level0_python_model/demo_write_hole.py
```

### 4. TODO 与路线状态一致

基本通过。

TODO 中当前状态合理：

- `docs/write_hole.md` 已完成；
- `demo_write_hole.py` 已完成；
- `docs/rebuild_and_scrub.md` 仍待办；
- degraded read 演示脚本仍待办。

这和项目当前进度一致。

## 更苛刻视角下的“不够出色”

### 问题 1：手算段的标签有一点误导

手算段打印：

```text
recover disk1 D1 : ...
```

但模型段说明 stripe 0 布局是：

```text
disk0=P disk1=D0 disk2=D1 disk3=D2
```

也就是说，D1 在物理上是 `disk2`，不是 `disk1`。

虽然这里的 `disk1 D1` 可能想表达“第 1 个数据块 D1”，但初学者很容易把它理解成“物理 disk1”。

建议下一轮改成更清楚的标签，例如：

```text
recover logical D1 : ...
```

或：

```text
recover missing D1 : ...
```

### 问题 2：mini challenge 说“change which disk fails”，但代码不方便改

结尾写着：

```text
Mini challenge: change which disk fails in the model section and predict the recovered byte.
```

但当前 `print_model_case()` 内部把失败盘写死为：

```python
raid.disks[2].fail()
```

读者当然可以改源码，但挑战还不够“闯关式”。更好的做法是让函数参数化：

```python
print_model_case(..., failed_disk=2, lba=1)
```

然后在输出里明确：

```text
try failed_disk=0 / 1 / 2 / 3
```

这样读者更容易动手实验。

### 问题 3：模型段只覆盖 D1 所在数据盘，泛化感还不够

当前例子非常适合解释 write hole，但它固定在：

- stripe 0；
- 4 盘；
- parity 在 disk0；
- 逻辑 D1 在 disk2；
- 失败盘也是 disk2。

这会让一部分读者误以为 write hole 的危险只在“数据盘失败”时暴露。实际上 parity mismatch 也会影响重建、巡检和后续维护逻辑。

下一轮不必做大扩展，但可以加一句说明：

> 这里固定 disk2 只是为了让数字最短；换成其他数据盘或 parity 盘，核心风险仍是 stripe 不再自洽。

### 问题 4：write hole 后仍缺 rebuild/scrub 承接页

当前 README 和 TODO 已经承认 `docs/rebuild_and_scrub.md` 是下一块内容，但文档还不存在。

从教学闭环看，读者已经知道：

1. write hole 会造成 data/parity mismatch；
2. normal read 可能看不出来；
3. degraded read / rebuild / scrub 会暴露问题。

但还不知道：

- rebuild 是怎么用 surviving disks 恢复缺失盘的；
- scrub 如何主动扫描 parity mismatch；
- mismatch 被发现后该报告、修复还是隔离；
- FPGA 控制器需要哪些状态机/计数器/错误上报。

因此下一次改进最有价值的闭环是补 `docs/rebuild_and_scrub.md` 的最小骨架，而不是继续扩展 demo。

## 本轮结论

第 19 轮改进是有效的：

- 代码能跑；
- 测试通过；
- demo 确实接上了 RAID5 模型；
- README 当前优先级已跟上 Level 0~4；
- TODO 保持了后续路线。

但它还不是“足够出色”的教学关卡，主要短板是：

1. `recover disk1 D1` 标签容易混淆物理 disk 与逻辑数据块；
2. mini challenge 还没有参数化支撑；
3. demo 固定一个失败场景，泛化提示不足；
4. 缺少 `rebuild_and_scrub.md` 承接 write hole 后的维护逻辑。

## 下轮建议做什么

第 21 次唤醒应进入改进阶段。

建议做一个小闭环，优先级如下：

1. 小修 `demo_write_hole.py`：
   - 把 `recover disk1 D1` 改成 `recover missing D1` 或 `recover logical D1`；
   - 把 `print_model_case()` 的失败盘参数化，默认仍用 `failed_disk=2`；
   - 加一句“固定 disk2 只是为了让例子最短”的说明。
2. 如果时间足够，新增 `docs/rebuild_and_scrub.md` 最小页：
   - rebuild 是什么；
   - scrub 是什么；
   - 它们如何暴露 write hole；
   - FPGA 里需要哪些最小控制信号。
3. 更新 README/TODO 链接状态并运行：

```bash
python labs/level0_python_model/demo_write_hole.py
python -m pytest -q labs/level0_python_model
```

## 本轮未修改交付物

本轮是检验阶段，仅新增本报告：

- `notes/inspection_wake20.md`
