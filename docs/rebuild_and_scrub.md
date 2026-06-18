# Rebuild and Scrub - 把潜伏错误逼出来

## 先抓住这句话

RAID5 的 write hole 麻烦就麻烦在：平时正常读，可能一点异常都看不出来。真正把问题逼出来的，往往是 **rebuild** 和 **scrub** 这两个维护动作：

1. rebuild：某块盘坏了，用剩余 data/parity 重建缺失块；
2. scrub：盘还没坏，主动扫描 stripe，重新计算 parity，检查磁盘上的 parity 是否一致；
3. 放到 FPGA RAID 控制器里看，它们都不是“神秘算法”，而是按 stripe 循环读、XOR、比较、写回或上报。

一句话记住：**write path 负责制造一致 stripe；rebuild/scrub 负责在未来证明 stripe 仍然一致。**

## 1. Rebuild：少一块盘时怎么补回来

还是用 4 盘 RAID5 的 stripe 0：
```text
disk0=P  disk1=D0  disk2=D1  disk3=D2
```

如果 `disk2` 坏了，系统读不到 `D1`。RAID5 的单盘重建公式是：
```text
missing = P XOR D0 XOR D2
```

用上一关的正常状态：
```text
D0 = 0xaa
D1 = 0x0f
D2 = 0x00
P  = 0xa5

rebuild_D1 = 0xa5 XOR 0xaa XOR 0x00 = 0x0f
```

这就是 rebuild 的主循环：
```text
for each stripe:
    read all surviving blocks
    missing_block = XOR(surviving blocks)
    write missing_block to replacement disk
```

它好理解，但有一个前提：**幸存块和 parity 必须属于同一个自洽状态**。

## 2. Write hole 为什么会在 rebuild 时爆炸

如果发生过 write hole，stripe 可能变成：
```text
D0 = 0xaa
D1 = 0x0f   # data 已经是新值
D2 = 0x00
P  = 0x66   # parity 仍是旧值
```

正常读 `D1` 时，控制器直接读 `disk2`，看到的是 `0x0f`，看起来没坏。

但如果 `disk2` 后来坏了，rebuild 会算：
```text
rebuild_D1 = P XOR D0 XOR D2
           = 0x66 XOR 0xaa XOR 0x00
           = 0xcc
```

结果恢复出旧值。问题不是 XOR 错，而是输入块已经不属于同一个时间点。

## 3. Scrub：盘没坏时主动巡检

Scrub 可以先理解成“RAID 自检巡逻”。它不等盘坏，而是定期扫描 stripe：
```text
for each stripe:
    read data blocks
    calculated_parity = XOR(data blocks)
    read stored_parity
    if calculated_parity != stored_parity:
        report parity mismatch
```

对上面的 write hole 状态：
```text
calculated_P = 0xaa XOR 0x0f XOR 0x00 = 0xa5
stored_P     = 0x66
```

scrub 会发现：磁盘上的 parity 和数据重新算出来的 parity 不一致。

注意：scrub 能发现 mismatch，但“自动修哪个”并不总是安全。因为控制器只看到 data/parity 不一致，未必知道谁才是业务上正确的版本。

## 4. Scrub 发现 mismatch 后怎么办

最小做法可以分三档：

| 策略 | 动作 | 适合什么时候用 |
|---|---|---|
| report only | 只上报 mismatch，不改盘 | 学习模型、早期 RTL |
| repair parity | 假设 data 正确，重写 parity | 有上层校验或策略确认时 |
| quarantine | 标记 stripe 风险，等待人工/上层处理 | 更接近真实系统 |

这个实验仓库的早期目标建议先做 **report only**：
```text
mismatch_valid = 1
mismatch_stripe = current_stripe
expected_parity = XOR(data blocks)
actual_parity = stored parity
```

等模型和 RTL 都跑顺后，再讨论 repair parity 和更复杂的一致性策略。

## 5. FPGA 里最小需要哪些控制信号

把 rebuild/scrub 映射到 FPGA，没必要一上来就做完整控制器。可以先抽成几个小模块和状态：

### Rebuild 最小状态机
```text
IDLE
  -> ISSUE_READS        # 读幸存盘
  -> WAIT_READS
  -> XOR_SURVIVORS      # XOR 生成 missing block
  -> WRITE_REPLACEMENT
  -> NEXT_STRIPE
  -> DONE
```

先记住这些寄存器/信号：

- `stripe_idx`：现在处理哪个 stripe；
- `failed_disk_id`：缺失的是哪块盘；
- `survivor_data[]`：幸存盘读回的数据；
- `rebuild_data`：XOR 后要写入替换盘的数据；
- `rebuild_valid` / `rebuild_error`：结果有效或异常。

### Scrub 最小状态机
```text
IDLE
  -> ISSUE_READ_STRIPE
  -> WAIT_READS
  -> XOR_DATA
  -> COMPARE_PARITY
  -> REPORT_OR_NEXT
  -> DONE
```

先记住这些寄存器/信号：

- `calculated_parity`：数据块 XOR 后的 parity；
- `stored_parity`：从 parity 盘读回的 parity；
- `mismatch_valid`：发现不一致；
- `mismatch_stripe`：哪一个 stripe 不一致；
- `scrub_mode`：只报告，还是允许修复 parity。

## 6. 和前几关怎么接起来
```text
raid5_parity.md      -> 知道 XOR parity 怎么恢复一块盘
raid5_write_path.md  -> 知道 partial write 为什么要更新 data + parity
write_hole.md        -> 知道中途断电会留下 data/parity mismatch
rebuild_and_scrub.md -> 知道 mismatch 什么时候被发现、如何上报
```

## 7. 如果你想动手验证

从仓库根目录运行：
```bash
python labs/level0_python_model/demo_rebuild_and_scrub.py
```

你会看到同一个 write hole stripe 的两种暴露方式：
```text
scrub result: parity mismatch detected
rebuild_D1 = P XOR D0 XOR D2 = 0xcc
```

这就是本关这一关真正要抓住的直觉：**scrub 尽量在坏盘前发现 mismatch；rebuild 则会在坏盘后依赖幸存块，可能把 mismatch 变成错误恢复数据。**

下一步你可以把这个过程拆成 RTL 状态机：先做 XOR engine，再做按 stripe 循环读、比较和上报。

---

## 继续阅读

⬅️ [上一篇：Write Hole](write_hole.md)<br>
🏠 [回到课程目录](index.md)<br>
➡️ 下一篇：没有，主线到这里就读完了
