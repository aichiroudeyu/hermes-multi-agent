# 嵌入式开发边界交叉验证清单

> 从 harness QA Agent Guide 的 "Boundary Mismatch" 方法论改造而来。
> 嵌入式固件中 70% 的 bug 不在单个模块内部，而在模块之间的边界。

---

## 1. UART 收发边界

### 帧格式一致性

| 检查项 | 发送端 | 接收端 | 验证方法 |
|--------|--------|--------|---------|
| 帧头字节 | `0x20 0x20` | 期望 `0x20 0x20` | 两端 grep 帧头常量 |
| 帧尾字节 | `0x02 0x02` | 期望 `0x02 0x02` | 两端 grep 帧尾常量 |
| 数据长度字节序 | LSB first？MSB first？ | 解析顺序一致？ | 人肉验算一个完整帧 |
| Checksum 算法 | 求和 → 取低 8 位？ | 同一算法验证？ | 两端 checksum 函数名一致？ |
| 最大帧长度 | `GY_PARAM_LEN` | 接收缓冲区 ≥ 发送最大帧 | 比较 `#define` 值 |

### DMA/中断 配置一致性

| 检查项 | TX 端 | RX 端 | 陷阱 |
|--------|-------|-------|------|
| 波特率 | 115200 | 115200 | 不匹配 = 全乱码 |
| DMA 模式 vs 字节模式 | 用哪种？ | 用哪种？ | DMA ↔ 字节模式混用会导致丢帧 |
| `uart_set_irq_mask` | 单次调用合并所有 mask | 同 | 多次调用 = 覆盖！ |

### 实战教训

```c
// ❌ 错误：每次覆盖上一次的 mask
uart_set_irq_mask(UART0, UART_RX_IRQ_MASK);
uart_set_irq_mask(UART0, UART_TXDONE_MASK);  // 只剩 TXDONE！

// ✅ 正确：合并一次调用
uart_set_irq_mask(UART0, UART_RX_IRQ_MASK | UART_ERR_IRQ_MASK | UART_RXDONE_MASK | UART_TXDONE_MASK);
```

---

## 2. Mesh 通信边界

### 分包边界

| 检查项 | 发送方 | 接收方 | 陷阱 |
|--------|--------|--------|------|
| 分包序号 | ch1~ch8？01234567？ | 期望的顺序？ | 序号不一致 = 数据拼接错乱 |
| `pending_valid` 状态 | 0→1→2 三态？ | 期望的三态？ | 少一个状态 = 丢包 |
| `data_len` 计算 | `len - 21` 还是 `len - 22`？ | 期望值？ | 差 1 字节 = 截断 or 越界 |
| Mesh Opcode | `0x3333` / `0x3334` | 同一 opcode？ | Dongle + 控制板必须一致 |

### 双板同步检查

修改一个板的 `wxl_uart.h` 中的协议宏后，**必须立即检查另一个板**：

```bash
# Dongle 的
rtk grep "GY_FACTORY_OPCODE" \
  "<project-dir>/dongle/.../wxl_uart.h" \
  "<project-dir>/controller/.../wxl_uart.h"
# → CMD 和 REPLY 值必须一致
```

---

## 3. Flash 存储边界

| 检查项 | 规则 | 原因 |
|--------|------|------|
| 0xFF000 | **严禁擦写** | MAC 地址存储区 |
| 0xFE000 | **严禁擦写** | 校准数据存储区 |
| 写前擦除 | 必须 `flash_erase_sector()` | Flash 只能 1→0，不能 0→1 |
| 擦除粒度 | 4KB (sector) | 误算粒度 = 擦到保护区 |

---

## 4. ISR 边界

| 检查项 | 正确做法 | 禁止 |
|--------|---------|------|
| 临界区保护 | `__disable_irq()` + `__enable_irq()` | 裸操作全局变量 |
| 中断内打印 | **禁止** `printf`/`log_printf` | 中断 >15μs 会导致丢中断 |
| RX_ERR 处理 | 先清 `RXBUF`，再处理 | 不清 RXBUF = 持续中断 |
| TXDONE 排水 | 逐字节清 FIFO | 批量清 = 丢最后几字节 |
| 中断嵌套 | 关中断期间，其他中断排队等待 | 假设其他中断能进来 |
