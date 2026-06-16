# Inspection Report - Wake 14

## 阶段

第 14 次唤醒：检验阶段。

本轮检验第 13 次唤醒新增的 `docs/raid5_write_path.md`，以及 README/TODO 对该页面的接入。原则是不修改交付物，只记录事实核对、实测结果和下一轮改进建议。

## 检验视角

本轮采用五个视角：

1. **测试工程师**：用比文档更难的 RMW / reconstruct 测例检查公式是否站得住；
2. **懂 FPGA 但不懂 RAID 的读者**：能否区分 full-stripe write、read-modify-write、reconstruct write；
3. **Python 模型维护者**：页面是否误导读者以为当前模型已经支持 partial write；
4. **可靠性工程师**：write hole 是否被描述为“可能的不一致窗口”，而不是“每次 partial write 必坏”；
5. **课程设计者**：README Step 0~7 是否仍然像一条通关路线。

## 实测结果

### 1. RMW 公式压力测试

文档给出的核心公式是：

```text
new_P = old_P XOR old_D1 XOR new_D1
```

本轮没有只复查 2 数据块例子，而是扩展到 2、3、4、5、7 个 data block，并且一次修改 1 个、2 个、3 个以及接近整条 stripe 的多个 data block。

检验规则：

```text
old_P = XOR(all old data)
new_P_by_RMW = old_P XOR every(old changed data) XOR every(new changed data)
new_P_by_full_recompute = XOR(all new data)
```

实测输出：

```text
RMW formula stress
n_data 2 OK
n_data 3 OK
n_data 4 OK
n_data 5 OK
n_data 7 OK
```

结论：RMW 的 XOR delta 性质正确。文档中的单块修改公式是成立的，并且可以推广到多块修改。

不过，文档对“多块修改”的推广讲得还不够显式。下一轮改进可以补一句：

```text
如果一次改多个 data block，就把每个被修改块的 old_D 和 new_D 都 XOR 进去。
```

这是本轮发现的主要可改进点。

### 2. RMW 与 reconstruct write 读旧块数量

文档讲的读旧块数量规则：

```text
RMW 需要读：W 个 old data + 1 个 old parity = W + 1
reconstruct 需要读：N - W 个未修改 data
```

其中：

- `N` = 一个 stripe 里的 data block 数；
- `W` = 本次 write 修改的 data block 数。

本轮枚举 `N=2..8`，`W=1..N-1`：

```text
n_data 2 [(1, 2, 1, 'reconstruct')]
n_data 3 [(1, 2, 2, 'tie'), (2, 3, 1, 'reconstruct')]
n_data 4 [(1, 2, 3, 'RMW'), (2, 3, 2, 'reconstruct'), (3, 4, 1, 'reconstruct')]
n_data 5 [(1, 2, 4, 'RMW'), (2, 3, 3, 'tie'), (3, 4, 2, 'reconstruct'), (4, 5, 1, 'reconstruct')]
n_data 6 [(1, 2, 5, 'RMW'), (2, 3, 4, 'RMW'), (3, 4, 3, 'reconstruct'), (4, 5, 2, 'reconstruct'), (5, 6, 1, 'reconstruct')]
n_data 7 [(1, 2, 6, 'RMW'), (2, 3, 5, 'RMW'), (3, 4, 4, 'tie'), (4, 5, 3, 'reconstruct'), (5, 6, 2, 'reconstruct'), (6, 7, 1, 'reconstruct')]
n_data 8 [(1, 2, 7, 'RMW'), (2, 3, 6, 'RMW'), (3, 4, 5, 'RMW'), (4, 5, 4, 'reconstruct'), (5, 6, 3, 'reconstruct'), (6, 7, 2, 'reconstruct'), (7, 8, 1, 'reconstruct')]
```

结论：文档的教学级选择规则正确：

- 改得少，RMW 通常读得少；
- 改得多，reconstruct 通常读得少；
- 中间存在 tie，真实系统还要考虑读写调度、缓存命中、盘忙闲、stripe buffer 等因素。

文档没有把该规则写死成绝对性能结论，这是正确的。

### 3. 是否误导 Python 模型已经支持 partial write

检查结果：

```text
states current model only full stripe OK
has full-stripe OK
has read-modify-write OK
has reconstruct write OK
has delta formula OK
has generalized changed block formula MISSING
```

关键句存在：

```text
当前 Python 模型只实现 `write_full_stripe()`，没有实现 partial write。
```

结论：页面没有误导读者以为 Python 模型已经实现了 RMW/reconstruct。它把当前可运行范围和教学解释范围分开了。

不足：如上所述，多块修改的 generalized RMW 公式还不够显式。

### 4. write hole 风险边界

检查结果：

```text
write hole says possible not certain OK
```

页面使用的是“可能”“掉电或复位中断”“data/parity 不一致”这类表述，没有写成“每次 partial write 一定损坏”。这点技术边界是准确的。

本轮认可当前写法：它适合作为 `write_hole.md` 的入口，但还不足以替代完整 write hole 页面。

下一页应该继续补清楚：

- data 新、parity 旧；
- data 旧、parity 新；
- 阵列表面健康但 parity 不可信；
- 后续遇到 degraded read/rebuild 时，错误才可能被放大；
- journal/bitmap/PPL/scrub 这类机制为什么存在。

### 5. README Step 0~7 通关路线

抽取到的步骤：

```text
[('0', '先看 RAID 基础'),
 ('1', '看 RAID0 映射'),
 ('2', '看 RAID1 镜像'),
 ('3', '看 RAID5 parity'),
 ('4', '看 RAID5 write path'),
 ('5', '跑可视化 demo'),
 ('6', '对照源码看映射、镜像和校验'),
 ('7', '跑测试')]
```

结论：Step 编号连续，路线顺序合理：

```text
RAID 基础 -> RAID0 -> RAID1 -> RAID5 parity -> RAID5 write path -> demo -> source -> tests
```

不足：README 仍然像“路线图”，还不像“闯关式实验室”。每关缺少通关条件，例如：

- Step 1 结束后能否手算 `LBA -> disk/chunk`？
- Step 3 结束后能否解释单盘坏了为什么能读？
- Step 4 结束后能否判断什么时候用 RMW，什么时候用 reconstruct？

这不是本轮必须修的错误，但已成为下一次 README 改进的高价值点。

## 格式与路径检查

### Markdown 链接

```text
README.md TODO.md OK
README.md docs/raid_basics.md OK
README.md docs/raid0_mapping.md OK
README.md docs/raid1_mirror.md OK
README.md docs/raid5_parity.md OK
README.md docs/raid5_write_path.md OK
README.md labs/level0_python_model/ OK
missing links: []
```

### Markdown 表格

```text
README.md line 31 cols 5 sep 5 OK
docs/raid5_write_path.md line 7 cols 5 sep 5 OK
docs/raid5_write_path.md line 21 cols 5 sep 5 OK
docs/raid5_write_path.md line 109 cols 3 sep 3 OK
docs/raid5_write_path.md line 159 cols 4 sep 4 OK
docs/raid5_write_path.md line 233 cols 3 sep 3 OK
```

### README 推荐命令

运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

结果：

```text
RUN ... demo_layout.py exit 0
RUN ... -m pytest -q labs/level0_python_model exit 0
12 passed in 0.06s
```

缓存清理后：

```text
cache dirs after cleanup: [] []
```

## 及格线判断

本轮认为第 13 轮交付物达到及格线：

1. 三条 write path 讲清楚了；
2. full-stripe write 与当前 Python 模型对应明确；
3. RMW 公式经多 data block 压力测试成立；
4. reconstruct 与 RMW 的读旧块数量规则正确；
5. write hole 风险边界没有夸大；
6. README/TODO 接入无坏链，推荐命令和 pytest 通过。

## 不够出色的点

1. **generalized RMW 公式不够显式**

   文档展示了单块 `D1` 的公式，也说了“改多个 block 时 RMW 要读更多 old data”，但没有用一段清晰公式写出：

   ```text
   new_P = old_P
           XOR old_Di XOR new_Di
           XOR old_Dj XOR new_Dj
           ...
   ```

   这会让认真读者知道结论，但不够“一眼会用”。

2. **README 仍缺通关检查点**

   当前 Step 0~7 是顺的，但“闯关感”还不够。建议后续给每个 Step 补一句“通关后你应该能回答”。

3. **write hole 入口够用，但下一页必须补全场景矩阵**

   现在只作为引子合理。下一页 `docs/write_hole.md` 应该画出 data/parity 写入被打断的几种状态，并说明错误何时暴露。

4. **缺可运行 partial write / write hole 演示**

   这不是第 13 轮的失败，因为第 13 轮刻意只做文档小闭环。但从项目“有趣、清晰、可运行”的目标看，后续最好补一个小 demo，让读者看到 parity mismatch 如何导致 degraded read 返回错误数据。

## 第 15 次唤醒建议

第 15 次唤醒应进入**改进阶段**。

建议做一个小闭环，不要扩散：

1. 优先新增 `docs/write_hole.md`；
2. README/TODO 接入该页面；
3. 页面只讲一个主题：partial write 被打断后 data/parity 不一致；
4. 至少包含两种状态矩阵：
   - data 新、parity 旧；
   - data 旧、parity 新；
5. 解释为什么正常读可能暂时没发现，直到 degraded read/rebuild 才爆雷；
6. 用一句话点到 journal/bitmap/PPL/scrub，但不要展开成完整可靠性设计；
7. 写 `notes/changelog_wake15.md`；
8. 验证链接、表格、README 推荐命令、pytest。

如果还有余力，可以顺手在 `docs/raid5_write_path.md` 里补 generalized RMW 公式。但为了保持“一轮一个小闭环”，第 15 轮主任务仍建议锁定 `docs/write_hole.md`。
