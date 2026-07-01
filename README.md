# Hermes Multi-Agent — 四 Agent 星型调度体系

> 一个自学的嵌入式程序员，用 AI 不停摸索出来的多 Agent 协作体系。
> 总调度 (Hermes) + 代码执行 (Claude Code) + 网页搜索 (OpenClaw) + 系统操作 (Marvis)。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

📖 [中文完整版](README_CN.md) | 📖 [English Full Version](README_EN.md)

---

## 一句话

**Hermes 总调度 + Claude Code 写代码 + OpenClaw 搜资料 + Marvis 系统操作**

---

## 我是谁

自学嵌入式程序员。没有 CS 背景，靠着对硬件的热爱和对 AI 的死磕，一个人摸索出一套真正能用的四 Agent 协作体系。

这个项目来自真实的 BLE Mesh 固件开发日常——不是论文，是实战。**根据使用经验持续迭代中。**

---

## v2.0 更新 (2026-07)

v1.0 发布后一个月的自进化成果：

| 新增 | 说明 |
|------|------|
| **SOUL.md** | Agent 灵魂文件，定义"我是谁、我能做什么、我的铁律" |
| **三层记忆** | Memory（事实）+ Wiki（知识）+ Skills（流程）分层存储 |
| **Loop 模式** | 设定目标+验收标准，自动循环委派直到通过裁判审查 |
| **自动 Skill 加载** | `skill-router.py` 按用户输入关键词自动推荐并加载 skills |
| **MCP Server 生态** | CodeGraph（代码索引）、Agent-Reach（搜索扩展），Agent 工具链可插拔 |
| **防误判模式** | 派 Claude Code 审查时附带设计决策背景 |
| `_workspace/` 审计 | 每次委派子 Agent 的输入输出存档可追溯 |
| **更新前备份** | `pre-update-backup.sh` 防 npm 更新清空 MCP 配置 |
| **跨 PC 同步** | 不同步 API key/本地 IP/端口号，只同步纯知识和工具 |
| **并行委派** | `terminal(background=true)` 同时开多个 Claude Code CLI + OpenClaw，真正并行 |
| **四 Agent 体系** | 新增 Marvis（腾讯 AI 助手）作为系统操作轨，Windows 文件管理/系统配置/桌面自动化 |
| **Marvis 文件桥接** | WSL2 ↔ Windows 跨 OS 通信，共享目录 + Marvis 定时轮询，零外部依赖 |
| **审计日志** | `audit-log.py` 记录每次委派（Agent/耗时/状态/成本），`--stats` 一键统计 |
| **角色去重** | Agent 角色定义收敛到 `agent-roles.md` 单一来源，SKILL.md 只保留调度逻辑 |

---

## 架构

```
                  ┌──────────────┐
                  │   CLI / 飞书  │  ← 双入口
                  └──────┬───────┘
                         │ @Hermes 发任务
                         ▼
            ┌─────────────────────────┐
            │     Hermes（总调度）      │
            │  Skill 自动路由          │
            │  Memory / Wiki / Skills  │
            │  分析 → 判断 → 派任务    │
            └──┬──────┬──────┬────────┘
               │      │      │
       调代码  │ 搜资料│      │ 系统操作
               ▼      ▼      ▼
        ┌──────┐ ┌──────┐ ┌──────────┐
        │Claude│ │Open  │ │  Marvis  │
        │ Code │ │Claw  │ │  马维斯   │
        │写代码│ │搜资料│ │系统/文件  │
        │5 MCP │ │SearX │ │腾讯独立额度│
        └──────┘ └──────┘ └──────────┘
```

---

## 项目文件

```
skills/hermes-orchestrator/
├── SKILL.md                          # 核心调度逻辑
└── references/
    ├── agent-roles.md                # 四 Agent 角色定义 + 通信协议
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR 边界检查表
    └── pitfalls-collection.md       # 多 Agent 通用陷阱集

scripts/
├── pre-update-backup.sh              # Agent 更新前自动备份
├── skill-router.py                   # 自动 Skill 加载器
├── hermes_loop.py                    # Loop 模式调度器
├── weekly-report.py                  # 周报自动生成
├── memory-archive.py                 # 记忆归档清理
├── audit-log.py                      # 委派审计日志

docs/
├── pitfalls-and-fixes.md             # 更新后问题记录 (13条)
└── architecture-evolution.md         # 体系演进历程
```

---

## 核心能力

### 1. 星型调度 + 自动路由

Hermes 分析任务 → `skill-router.py` 自动匹配 skills → 路由到 Claude Code 或 OpenClaw。默认串行——一次只派一个人。双板审查/搜索+写代码时用 `terminal(background=true)` 并行开多个 Claude Code CLI。

### 2. Loop 自动闭环

```bash
python3 hermes_loop.py --goal "写 TCP echo server" \
  --acceptance "①监听8888 ②回显文本" --max-loops 5
```

设定目标和验收标准，自动循环：写代码 → 编译测试 → 不通过则带失败信息重派 → 通过则汇报。

### 3. 三层记忆体系

| 层 | 存什么 | 例子 |
|----|--------|------|
| **Memory** | 用户偏好/环境/踩坑 | "ISR内禁printf" |
| **Wiki** | 结构化知识库 | BLE Mesh 配网流程 |
| **Skills** | 可执行的流程模板 | MCU 固件开发规范 |

### 4. 边界交叉验证

嵌入式固件 70% 的 bug 不在单个模块内部，而在模块之间的边界：

| 边界 | 检查项 |
|------|--------|
| **UART** | 帧格式一致性 / 波特率 / DMA vs 字节中断模式 |
| **Mesh** | 分包序号 / `pending_valid` 状态 / `data_len` 计算 |
| **Flash** | MAC 保护区 (0xFF000) / 校准区 (0xFE000) |
| **ISR** | 临界区保护 / 中断内禁 printf / TXDONE 逐字节排水 |

### 5. 四 Agent 职责分离

| Agent | 职责 | 通信方式 |
|-------|------|----------|
| **Hermes** | 总调度 + 读代码 + 记忆管理 | CLI 直辖 |
| **Claude Code** | 多文件重写 + 代码审查 + 编译 | terminal heredoc |
| **OpenClaw** | 网页搜索 + 技术调研 + 内容抓取 | terminal CLI |
| **Marvis** | Windows 文件管理 + 系统配置 + 桌面自动化 | 文件桥接 (30min 定时轮询) |

### 6. 审计日志

```bash
python3 audit-log.py --stats
# {"total_delegations": 142, "by_agent": {"claude-code": 98, "openclaw": 31, "marvis": 13}, "total_cost_usd": 21.75}
```

每次委派自动记录 Agent、耗时、状态、成本估算。事后可完整回溯。

---

## 快速开始

```bash
# 复制 orchestrator skill
cp -r skills/hermes-orchestrator ~/.hermes/skills/autonomous-ai-agents/

# 复制通用脚本
cp scripts/skill-router.py ~/.hermes/scripts/
cp scripts/hermes_loop.py ~/.hermes/scripts/
cp scripts/pre-update-backup.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/pre-update-backup.sh
cp scripts/audit-log.py ~/.hermes/scripts/

# 创建 workspace
mkdir -p ~/.hermes/workspace
```

---

## 硬件背景

| 芯片 | 架构 | 协议 | 项目 |
|------|------|------|------|
| Telink TLSR321X | RISC-V | BLE Mesh | 串口透传网关 / 厂测 Dongle |
| Telink TLSR8258 | RISC-V | BLE Mesh | 停车场 Dongle |
| STM32 | ARM Cortex-M | UART/SPI/I2C | 通用 MCU |

---

## 复用指南

- **嵌入式程序员** — `embedded-boundary-checklist.md` 直接可用，替换芯片型号即可
- **其他领域** — 调度逻辑与领域无关，换掉三个 Agent 名字就能复用
- **AI Agent 新手** — 先单 Agent → 加搜索 Agent → 加系统操作 Agent → 最后引入调度 Agent

---

## 设计决策

| 决策 | 原因 |
|------|------|
| 一次只派一个人 | 避免并发冲突，结果可追溯 |
| Agent 与 Skill 分离 | Agent 回答"谁"，Skill 回答"怎么做" |
| `_workspace/` 存档 | 出错后能回溯子 Agent 的输入输出 |
| 边界检查表 | 嵌入式 70% bug 在模块边界 |
| Skill description 含触发场景 | 模糊的 description = 不会被自动加载 |
| SOUL.md 铁律 | 约束 Agent 行为边界，防止越权 |
| 角色定义单一来源 | agent-roles.md 是唯一权威，SKILL.md 只引不写 |
| 审计日志 JSONL | 每行一条委派记录，可追溯、可统计 |

---

## 设计灵感

从 [revfactory/harness](https://github.com/revfactory/harness) 学到的方法论：Agent/Skill 分离、边界交叉验证、Progressive Disclosure。

---

## License

MIT — 开源无限制，随便用。
