# RAID1 Mirror - 数据的影分身

## 核心结论

RAID1 的核心只有一句话：**同一份逻辑数据，写到每一块镜像盘**。

它和 RAID0 的性格刚好相反：

| 项目 | RAID0 | RAID1 |
|---|---|---|
| 数据放法 | 拆散到不同盘 | 复制到每块盘 |
| 容量 | 多块盘容量相加 | 只等于最小那块盘 |
| 坏一块盘 | 映射到坏盘的数据丢失 | 只要还有一块好盘就能读 |
| 教学重点 | LBA 映射 | 写入扇出 + 健康盘选择 |

如果把 RAID0 想成“多人分工搬砖”，RAID1 就是“重要文件复印两份”。它不追求容量效率，而是用空间换简单可靠。

## 双盘镜像的最小例子

假设有两块盘：`disk0` 和 `disk1`。host 看到的逻辑 LBA 仍然是 0、1、2、3，但每个 LBA 都同时存在于两块盘上。

| host LBA | disk0 | disk1 |
|---|---|---|
| 0 | block0 = data0 | block0 = data0 |
| 1 | block1 = data1 | block1 = data1 |
| 2 | block2 = data2 | block2 = data2 |
| 3 | block3 = data3 | block3 = data3 |

布局图：

```text
          LBA0    LBA1    LBA2    LBA3
disk0     data0   data1   data2   data3
disk1     data0   data1   data2   data3
```

这就是“镜像”：不是把 LBA0 放 disk0、LBA1 放 disk1，而是每个 LBA 都有副本。

## 写路径：一次 host write，变成多次 member write

host 写入一个 LBA 时，RAID1 必须把同一份数据写到所有镜像成员盘。

```text
host write LBA2 = data2
        |
        v
+-------------------+
| RAID1 write fanout|
+-------------------+
   |             |
   v             v
disk0:LBA2    disk1:LBA2
=data2        =data2
```

在当前 Python 模型里，对应代码是 `RAID1.write()`：

```python
def write(self, lba: int, data: bytes) -> None:
    self._check_lba(lba)
    for disk in self.disks:
        disk.write(lba, data)
```

关键点：

- RAID1 不需要像 RAID0 那样计算 `disk_index = lba % disk_count`；
- 它要做的是 **fanout**：把同一个写请求复制给所有成员盘；
- 写入是否算成功，在真实系统里还涉及错误处理、重试、状态机和一致性记录；Level 0 先只保留最核心动作。

## 读路径：找一块健康盘读

读的时候，RAID1 不需要每次都读所有盘。只要某块镜像盘健康，就可以从它读出数据。

```text
host read LBA2
        |
        v
+---------------------+
| choose healthy disk |
+---------------------+
        |
        v
disk0:LBA2 -> data2
```

如果 `disk0` 坏了：

```text
host read LBA2
        |
        v
skip disk0, choose disk1
        |
        v
disk1:LBA2 -> data2
```

当前 Python 模型对应 `RAID1.read()`：

```python
def read(self, lba: int) -> bytes:
    self._check_lba(lba)
    for disk in self.disks:
        if not disk.failed:
            return disk.read(lba)
    raise DiskFailedError("all RAID1 mirrors are failed")
```

这段代码表达了 RAID1 的最小生存规则：**只要至少一块镜像盘还活着，读就能继续**。

## 故障表：坏一块盘会发生什么？

仍然用 LBA 0~3 和两块盘演示。

| 场景 | LBA0 | LBA1 | LBA2 | LBA3 | 结论 |
|---|---|---|---|---|---|
| disk0/disk1 都健康 | yes | yes | yes | yes | 任意 LBA 可读 |
| disk0 failed | yes | yes | yes | yes | 从 disk1 读 |
| disk1 failed | yes | yes | yes | yes | 从 disk0 读 |
| disk0 + disk1 都 failed | no | no | no | no | 没有健康副本 |

和 RAID0 对比，这张表很重要：RAID0 坏一块盘后，只有映射到健康盘的 LBA 还能读；RAID1 坏一块盘后，所有 LBA 仍然可读。

## 容量代价：安全感不是免费的

RAID1 的容量不是成员盘容量相加，而是取决于最小成员盘。

```text
2 块 1 TB 盘做 RAID1：可用容量约 1 TB
3 块 1 TB 盘做 RAID1：可用容量仍约 1 TB，但副本更多
```

在当前模型里：

```python
self.capacity_blocks = min(d.block_count for d in disks)
```

这表示：只要有一块盘比较小，整个镜像组就不能暴露超过这块盘的逻辑容量，否则小盘没有位置保存副本。

## FPGA 视角：RAID1 会变成什么硬件逻辑？

最小 RAID1 控制逻辑可以拆成两条路径：

```text
write path:
  host_valid + host_lba + host_data
       -> duplicate request to every member disk
       -> wait/collect member write responses

read path:
  host_valid + host_lba
       -> choose one healthy member disk
       -> return member read data
```

它暂时不需要 XOR，也不需要复杂条带映射。对 FPGA 初学者来说，RAID1 是学习“请求复制、健康状态、故障切换”的好关卡。

## 和下一关 RAID5 的关系

RAID1 的可靠性来自“完整副本”，RAID5 的可靠性来自“数据 + XOR 校验”。

可以先记住这个对照：

| 方案 | 保护方式 | 容量效率 | 恢复直觉 |
|---|---|---|---|
| RAID1 | 完整复制 | 低 | 从另一份副本读 |
| RAID5 | XOR parity | 较高 | 用剩余数据和 parity 算回来 |

下一关建议看 `docs/raid5_parity.md`：它会解释为什么 `A XOR B XOR parity` 可以把坏掉的一块数据算回来。

## 动手检查

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

重点观察：

- demo 里的 RAID1 是否展示同一 LBA 在两块盘上都有副本；
- 测试里的 RAID1 单盘故障后是否仍能读回数据；
- `raid_model.py` 里的 `RAID1.write()` 和 `RAID1.read()` 是否正好对应“写入扇出、读取健康盘”。

---

## 继续阅读

👉 [下一篇：RAID5 校验](raid5_parity.md)
