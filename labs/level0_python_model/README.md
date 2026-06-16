# Level 0 - Python RAID 小队

这一关先不碰 FPGA。我们用几块“虚拟硬盘”证明 RAID 的三件核心事：

1. **映射**：一个逻辑块到底落在哪块盘；
2. **冗余**：坏一块盘时还能不能读；
3. **恢复**：换新盘后能不能把缺失数据补回来。

## 快速运行

```bash
cd labs/level0_python_model
python -m pytest -q
```

如果没有 pytest，可先安装：

```bash
python -m pip install pytest
```

## 先看一眼布局

```bash
python demo_layout.py
```

它会打印三张小表：

- RAID0：LBA 如何轮流落到多块盘；
- RAID1：同一个 LBA 如何复制到镜像盘；
- RAID5：每个 stripe 的数据块和轮转 parity 在哪里。

示意：

```text
stripe   | disk0 | disk1 | disk2 | disk3
---------+-------+-------+-------+------
stripe 0 | P     | D0    | D1    | D2
stripe 1 | D3    | P     | D4    | D5
```

## 文件

- `raid_model.py`：VirtualDisk、RAID0、RAID1、RAID5 最小模型；
- `test_raid_model.py`：基础行为和边界行为测试；
- `demo_layout.py`：打印 RAID0/1/5 的 ASCII 布局。

## 当前边界

- 固定块大小，默认每块是 4 bytes，方便把 `b"ABCD"` 当成一个逻辑块观察；
- RAID0 只负责条带化，任意成员盘故障都会让映射到该盘的数据不可读；
- RAID1 支持从幸存镜像读取，但本模型不模拟 degraded write；
- RAID5 只支持 full-stripe 写入、单盘降级读取和单盘重建；
- 暂不处理 partial write、write hole、元数据、缓存和真实硬盘错误码；
- 这里的模型是 RTL 之前的 golden model，不是高性能存储库。
