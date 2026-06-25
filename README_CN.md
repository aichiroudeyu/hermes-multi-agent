# Hermes Multi-Agent — 三 Agent 星型调度架构

> 一个自学的嵌入式程序员，用 AI 不停摸索出来的多 Agent 协作体系。
> 总调度 (Hermes) + 代码执行 (Claude Code) + 网页搜索 (OpenClaw)。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[中文版](README_CN.md) | [English](README_EN.md)

---

## 关于我

我是一名自学嵌入式开发的程序员。没有计算机专业背景，靠着对底层硬件的热情和对 AI 工具的不停摸索，用 Hermes、Claude Code、OpenClaw 三个 AI Agent 搭建了一套真正能用于日常固件开发的协作体系。

这个项目不是实验室里的理论产物——它诞生于真实的 Telink BLE Mesh 固件开发、Dongle 厂测协议调试、DALI/DMX 照明协议学习中。每一个踩坑记录、每一条边界检查规则、每一个调度策略，都来自我被 bug 折磨后痛定思痛的总结。

**我会持续维护这个项目，根据自己使用这套体系的经验不断迭代。**

---

## 架构

```
                  ┌──────────────┐
                  │   飞书/CLI    │  ← 双入口
                  └──────┬───────┘
                         │ @Hermes 发任务
                         ▼
            ┌─────────────────────────┐
            │     Hermes（总调度）      │
            │  分析 → 判断 → 派任务    │
            └──┬──────────┬────────────┘
               │          │
       调代码  │          │ 搜资料
               ▼          ▼
        ┌──────┐     ┌──────┐
        │Claude│     │Open  │
        │ Code │     │Claw  │
        │写代码│     │搜资料│
        └──────┘     └──────┘
```

**核心原则**：一次只派一个人，等 `【DONE】` 回来再派下一个。

---

## 为什么你要看这个项目

- 你是一个嵌入式程序员，想用 AI Agent 帮你加速开发
- 你已经有了 Claude Code / OpenClaw，但不知道它们怎么配合
- 你对"多 Agent 协作"感兴趣，需要一个真正跑通的实战案例
- 你想知道一个自学的程序员用 AI 能做到什么程度

---

## 快速开始

### 前置要求

- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- [OpenClaw](https://github.com/openclaw/openclaw) (`npm install -g openclaw`)

### 安装

```bash
# 复制 orchestrator skill
cp -r skills/hermes-orchestrator ~/.hermes/skills/autonomous-ai-agents/

# 复制备份脚本
cp scripts/pre-update-backup.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/pre-update-backup.sh

# 创建 workspace 目录
mkdir -p ~/.hermes/workspace
```

---

## 文件结构

```
skills/hermes-orchestrator/
├── SKILL.md                          # 核心调度逻辑（283行）
└── references/
    ├── agent-roles.md                # 三 Agent 角色定义 + 通信协议
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR 边界检查表
    └── pitfalls-collection.md       # 多 Agent 通用陷阱集

scripts/
└── pre-update-backup.sh              # Agent 更新前自动备份
```

---

## 核心能力

### 1. 星型调度

Hermes 分析任务 → 路由到 Claude Code（写代码）或 OpenClaw（搜资料）。严格串行——一次只派一个人。三层终结机制防止死循环。

### 2. 边界交叉验证

嵌入式固件 70% 的 bug 不在单个模块内部，而在模块之间的边界：

| 边界 | 检查项 |
|------|--------|
| **UART** | 帧格式一致性 / 波特率 / DMA vs 字节中断模式 |
| **Mesh** | 分包序号 / `pending_valid` 状态 / `data_len` 计算 |
| **Flash** | MAC 保护区 (0xFF000) / 校准区 (0xFE000) / 擦除粒度 |
| **ISR** | 临界区保护 / 中断内禁 printf / TXDONE 逐字节排水 |

### 3. 防误判模式

派 Claude Code 审查代码时附带**设计决策背景**（为什么这样改 + 外部状态 + 实测结果 + 用户决策），防止将设计选择误判为 bug。

### 4. `_workspace/` 审计存档

每次委派子 Agent 的任务输入和返回结果都存档到 `_workspace/`，事后可追溯。

### 5. 更新前备份

`pre-update-backup.sh` 自动备份 MCP servers、permissions 白名单、配置文件到 `~/.hermes/backups/`。npm 更新可能清空 MCP 定义——备份就是保命符。

---

## 项目背景

### 硬件

| 芯片 | 架构 | 协议 | 项目 |
|------|------|------|------|
| Telink TLSR321X | RISC-V | BLE Mesh | 串口透传网关 |
| Telink TLSR8258 | RISC-V | BLE Mesh | 停车场 Dongle |
| STM32 | ARM Cortex-M | UART/SPI/I2C | 通用 MCU |

### 协议经验

- **BLE Mesh**：配网、分组、分包合并、厂测自定义 Opcode
- **UART 桥接**：双 MCU DMA/字节中断模式切换、HS 帧协议
- **DALI / DMX512**：IEC 62386 标准、调光曲线、曼彻斯特编码

---

## 复用指南

### 如果你也是嵌入式程序员

核心文件 `embedded-boundary-checklist.md` 和 `pitfalls-collection.md` 可以直接用于你的项目，替换芯片型号即可。

### 如果你是其他领域

`agent-roles.md` 和 `SKILL.md` 中的调度逻辑与领域无关。把三个 Agent 换成你自己的工具链就可复用。

### 如果你刚开始接触 AI Agent

推荐的学习路径：
1. 先熟悉 Claude Code 单 Agent 用法
2. 加入 OpenClaw 做搜索/调研
3. 最后引入 Hermes 做总调度

---

## 设计决策

| 决策 | 原因 |
|------|------|
| 一次只派一个人 | 避免并发冲突，结果可追溯 |
| Agent 与 Skill 分离 | Agent 回答 "谁"，Skill 回答 "怎么做" |
| `_workspace/` 存档 | 出错后能回溯子 Agent 的输入输出 |
| 边界检查表 | 嵌入式 70% bug 在模块边界 |
| 描述含触发场景 | skill 通过 description 关键词触发，模糊的 description = 不会被自动加载 |

---

## 设计起源：从 harness 学到的方法论

本项目借鉴了 [revfactory/harness](https://github.com/revfactory/harness) 的设计：

- Agent/Skill 分离原则
- 边界交叉验证方法论
- Progressive Disclosure 渐进式信息加载
- 显式化团队通信协议

---

## 未来计划

- [ ] 扩展更多芯片平台的边界检查表（ESP32/nRF52）
- [ ] 加入 CI/CD 自动测试多 Agent 调度正确性
- [ ] 制作 demo 视频展示完整工作流
- [ ] 社区贡献指南

---

## License

MIT — 开源无限制，随便用。

---

## 联系

有嵌入式和 AI Agent 结合的想法？欢迎提 Issue 或 PR。这个项目是我一个人用 AI 摸索着写出来的，希望对你也有用。
