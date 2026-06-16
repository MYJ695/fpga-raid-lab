# References - 资料索引

## 结论

目前没找到成熟、可信、可直接复用的完整 FPGA RAID 控制器开源 RTL。资料应按“可复用子模块”和“算法参考”两类维护。

## 开源子模块

### SATA Host / HBA

- WangXuan95/FPGA-SATA-HBA  
  https://github.com/WangXuan95/FPGA-SATA-HBA

用途：可作为 FPGA 直连 SATA 硬盘的接口参考。

### Reed-Solomon / GF

- winsonbook/Reed-Solomon-  
  https://github.com/winsonbook/Reed-Solomon-

- lauchinyuan/reed_solomon_codes  
  https://github.com/lauchinyuan/reed_solomon_codes

- wyvernSemi/eccExamples  
  https://github.com/wyvernSemi/eccExamples

- eingkim/Multipliacation_Division_ofGaloisField_usingVerilog  
  https://github.com/eingkim/Multipliacation_Division_ofGaloisField_usingVerilog

用途：RAID6 P/Q parity、GF(2^8) 学习参考。

## 算法参考方向

### Linux MD RAID

关键词：

- Linux md raid5.c
- Linux RAID5 stripe cache
- Linux RAID write-intent bitmap
- RAID5 read modify write
- RAID write hole

价值：公开、成熟、能学习 RAID5/6 控制逻辑。

## 搜索结论记录

已查关键词：

- FPGA RAID Verilog
- RAID5 Verilog FPGA
- RAID controller Verilog
- hardware raid fpga github
- RAID SystemVerilog
- RAID VHDL

结果：没有发现成熟完整 RTL，很多 `raid fpga` 命中的是游戏项目，不是存储 RAID。
