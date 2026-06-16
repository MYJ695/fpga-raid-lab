# RAID0 Mapping - LBA 怎么落到硬盘小队？

## 核心结论

RAID0 的核心只有一句话：**把连续的逻辑块轮流发给多块盘**。

如果有 `disk_count` 块盘，并且每个 chunk 在本实验里等于 1 个 block，那么映射公式就是：

```text
disk_index = lba % disk_count
disk_lba   = lba // disk_count
```

这不是数学炫技，而是 FPGA RAID 控制器将来必须硬件化的第一类逻辑：给定一个 host LBA，马上算出该访问哪块盘、盘内哪个地址。

## 三块盘的最小例子

假设有 3 块虚拟盘：`disk0`、`disk1`、`disk2`。

| host LBA | disk_index = lba % 3 | disk_lba = lba // 3 | 实际位置 |
|---:|---:|---:|---|
| 0 | 0 | 0 | disk0:block0 |
| 1 | 1 | 0 | disk1:block0 |
| 2 | 2 | 0 | disk2:block0 |
| 3 | 0 | 1 | disk0:block1 |
| 4 | 1 | 1 | disk1:block1 |
| 5 | 2 | 1 | disk2:block1 |
| 6 | 0 | 2 | disk0:block2 |
| 7 | 1 | 2 | disk1:block2 |
| 8 | 2 | 2 | disk2:block2 |

换成布局图就是：

```text
          stripe0   stripe1   stripe2
disk0       LBA0      LBA3      LBA6
disk1       LBA1      LBA4      LBA7
disk2       LBA2      LBA5      LBA8
```

## stripe、chunk、disk_lba 是什么关系？

先用本实验的最小定义：

- **chunk**：一次放到某块盘上的连续数据片段；Level 0 里先设成 1 个 block；
- **stripe**：跨所有成员盘的一排 chunk；3 块盘时，`LBA0~2` 组成 stripe0，`LBA3~5` 组成 stripe1；
- **disk_lba**：某块物理盘内部的 block 号。

所以，RAID0 不是把文件“复制”到多块盘，而是把逻辑地址拆散：

```text
host sees:  LBA0  LBA1  LBA2  LBA3  LBA4  LBA5
            |     |     |     |     |     |
            v     v     v     v     v     v
physical:  d0:0  d1:0  d2:0  d0:1  d1:1  d2:1
```

## 对应到 Python 模型

当前实现位于 [`../labs/level0_python_model/raid_model.py`](../labs/level0_python_model/raid_model.py)：

```python
def map_lba(self, lba: int) -> tuple[int, int]:
    self._check_lba(lba)
    return lba % len(self.disks), lba // len(self.disks)
```

读写路径都先调用 `map_lba()`：

```text
write(host_lba, data)
  -> map_lba(host_lba)
  -> disks[disk_index].write(disk_lba, data)

read(host_lba)
  -> map_lba(host_lba)
  -> disks[disk_index].read(disk_lba)
```

这就是后续 `rtl/lba_mapper` 的雏形。

## 坏一块盘会怎样？

RAID0 没有冗余。坏掉的不是“某个文件”，而是所有映射到坏盘的 LBA。

如果 `disk1` 故障：

| host LBA | 实际位置 | 还能读吗？ | 原因 |
|---:|---|---|---|
| 0 | disk0:block0 | yes | disk0 还活着 |
| 1 | disk1:block0 | no | 数据只在 disk1 |
| 2 | disk2:block0 | yes | disk2 还活着 |
| 3 | disk0:block1 | yes | disk0 还活着 |
| 4 | disk1:block1 | no | 数据只在 disk1 |
| 5 | disk2:block1 | yes | disk2 还活着 |
| 6 | disk0:block2 | yes | disk0 还活着 |
| 7 | disk1:block2 | no | 数据只在 disk1 |
| 8 | disk2:block2 | yes | disk2 还活着 |

这张表要记住：RAID5 的降级读，本质上就是在 RAID0 条带映射的基础上，再加一个 parity chunk，让“no”有机会被 XOR 算回来。

## FPGA 视角：这页以后会变成什么硬件？

最小硬件模块大概会长这样：

```text
input : host_lba, disk_count
output: disk_index, disk_lba

组合逻辑/小状态机：
  disk_index = host_lba mod disk_count
  disk_lba   = host_lba div disk_count
```

真实 RTL 里还会遇到几个问题：

1. `disk_count` 如果固定为 2/4/8，取模和除法可以优化成位切片；
2. `disk_count` 如果是 3/5/6，取模和除法需要更谨慎，可能要用查表、乘法近似或流水线；
3. 如果 chunk 大小不是 1 block，公式要先把 LBA 转成 `chunk_number`，再映射到盘。

Level 0 先故意保持简单：1 chunk = 1 block。等映射直觉稳定后，再把 chunk size 扩展成参数。

## 动手检查

从仓库根目录运行：

```bash
python labs/level0_python_model/demo_layout.py
python -m pytest -q labs/level0_python_model
```

重点观察：

- demo 里的 RAID0 表是不是和上面的 LBA 表一致；
- 测试里的 RAID0 坏盘用例是否符合“映射到坏盘的 LBA 不可读”。

下一关建议看 `docs/raid1_mirror.md`：RAID1 会用更贵的容量换来简单可靠的镜像读取。

---

## 继续阅读

⬅️ [上一篇：RAID 基础](raid_basics.md)  
🏠 [回到网页学习目录](index.md)  
➡️ [下一篇：RAID1 镜像](raid1_mirror.md)
