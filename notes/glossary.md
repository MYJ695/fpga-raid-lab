# Glossary - 术语小抄

## RAID

Redundant Array of Independent Disks。把多块盘组织成一个逻辑盘。

## LBA

Logical Block Address。主机看到的逻辑块地址。

## Chunk

一个条带单元。比如 64KB 数据放在某一块盘上。

## Stripe

一组 chunk。RAID 的基本组织单位。

## Parity

校验块。RAID5 里通常是 XOR 校验。

## Full-stripe write

一次写满整个 stripe，可以直接计算新校验。

## Partial write

只写 stripe 的一部分。RAID5 中会触发 read-modify-write 或 reconstruct write。

## Read-Modify-Write

RAID5 小写常用流程：

```text
new_parity = old_parity XOR old_data XOR new_data
```

## Write Hole

数据和校验没有原子更新，掉电后可能不一致。

## Degraded Mode

阵列坏了一块盘，但仍然能靠校验继续工作。

## Rebuild

换新盘后，根据其他盘和校验恢复缺失数据。

## Scrub

后台巡检，检查数据和校验是否一致。
