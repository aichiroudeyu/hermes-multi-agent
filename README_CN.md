# Hermes Multi-Agent — 四 Agent 星型调度体系

> 一个自学的嵌入式程序员，用 AI 不停摸索出来的多 Agent 协作体系。
> 总调度 (Hermes) + 代码执行 (Claude Code) + 网页搜索 (OpenClaw) + 系统操作 (Marvis)。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[中文版](README_CN.md) | [English](README_EN.md)

---

## 关于我

我是一名自学嵌入式开发的程序员。没有计算机专业背景，靠着对底层硬件的热情和对 AI 工具的不停摸索，用 Hermes、Claude Code、OpenClaw、Marvis 四个 AI Agent 搭建了一套真正能用于日常固件开发的协作体系。

这个项目不是实验室里的理论产物——它诞生于真实的 Telink BLE Mesh 固件开发、Dongle 厂测协议调试、DALI/DMX 照明协议学习中。每一个踩坑记录、每一条边界检查规则、每一个调度策略，都来自我被 bug 折磨后痛定思痛的总结。

**根据使用经验持续迭代中。**

---

## v2.0 更新 (2026-07)

v1.0 发布后一个月内，这套体系在实战中完成了多项自进化：

| 新增 | 说明 |
|------|------|
| **SOUL.md** | Agent 灵魂文件——定义"我是谁、我能做什么、我的铁律"，每次启动注入不可覆盖 |
| **三层记忆** | Memory（用户偏好/环境事实）+ Wiki（结构化知识库）+ Skills（可执行流程模板）三层持久化 |
| **Loop 自动闭环模式** | 设定目标+验收标准，自动循环：写代码→编译测试→不通过带失败信息重派→通过汇报 |
| **自动 Skill 加载** | `skill-router.py` 抓取用户输入关键词，自动匹配并加载相关 skills |
| **MCP Server 生态** | CodeGraph（代码关系图谱索引）、Agent-Reach（国内平台搜索），Agent 工具链可插拔扩展 |
| **防误判模式** | 派 Claude Code 审查代码时附带完整设计决策背景，防止将设计选择误判为 bug |
| `_workspace/` 审计存档 | 每次委派子 Agent 的任务输入和返回结果持久化存档，事后可完整回溯 |
| **更新前备份** | `pre-update-backup.sh` 自动备份 MCP servers 定义、permissions 白名单，防 npm 更新清空 |
| **跨 PC 同步安全** | 不打包同步 API key、本地 IP、端口号，只传纯知识和工具 |
| **并行委派** | `terminal(background=true)` 同时开多个 Claude Code CLI + OpenClaw，真正并行 |
| **四 Agent 体系** | 新增 Marvis（腾讯 AI 助手）作为系统操作轨，Windows 文件管理/系统配置/桌面自动化 |
|| **Marvis 文件桥接** | WSL2 ↔ Windows 跨 OS 通信，bridge-listener 2s 实时轮询 + winotify 桌面通知，零外部依赖 |
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
            │  SOUL.md 行为约束       │
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

**核心原则**：默认串行——一次只派一个人，等 `【DONE】` 回来再派下一个。

**并行模式**：双板代码审查、搜索+写代码同时进行时，Hermes 用 `terminal(background=true)` 同时开多个 Claude Code CLI + OpenClaw，不受 `delegate_task` 的并发限制。安全条件：不同目录 + 只读或一读一写 + 不 make + 不同 Git 仓库。

---

## 为什么你要看这个项目

- 你是一个嵌入式程序员，想用 AI Agent 帮你加速开发
- 你已经有了 Claude Code / OpenClaw，但不知道它们怎么配合
- 你对"多 Agent 协作"感兴趣，需要一个真正跑通的实战案例
- 你想知道一个自学程序员用 AI 能做到什么程度
- 你想了解如何给 Agent 建立持久的"记忆"和"灵魂"

---

## 项目文件

```
skills/hermes-orchestrator/
├── SKILL.md                          # 核心调度逻辑 (v6.1)
└── references/
    ├── agent-roles.md                # 四 Agent 角色定义 + 通信协议
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR 边界检查表
    └── pitfalls-collection.md       # 多 Agent 通用陷阱集

scripts/
├── pre-update-backup.sh              # Agent 更新前自动备份
├── skill-router.py                   # 自动 Skill 加载器 (156行)
├── hermes_loop.py                    # Loop 模式调度器 (326行)
├── weekly-report.py                  # 周报自动生成
├── memory-archive.py                 # 记忆归档清理
├── memory-archive.py                 # 记忆归档清理
├── audit-log.py                      # 委派审计日志

bridge/
├── bridge-listener.py                # Marvis 桥接监听器 (winotify, 2s轮询)
├── bridge-solution.md                # 通信方案设计文档

docs/
├── pitfalls-and-fixes.md             # Agent 更新后问题记录 (13条)
└── architecture-evolution.md         # 体系从零到 v2.0 的演进历程
```

---

## 核心能力

### 1. 星型调度 + 自动路由

Hermes 分析任务 → `skill-router.py` 按关键词自动匹配 skills → 路由到 Claude Code（写代码/审查）或 OpenClaw（搜资料/调研）。严格串行——一次只派一个人。三层终结机制防止死循环。

### 2. Loop 自动闭环

```bash
python3 hermes_loop.py --goal "用 Python 写 TCP echo server" \
  --acceptance "①监听8888 ②回显文本 ③Ctrl+C退出" --max-loops 5
```

设定目标和验收标准，自动循环：委派 Claude Code 写代码 → 裁判自动编译+测试 → 不通过则带失败信息重派 → 通过则汇报结果。成本约 $0.20/轮。

### 3. 三层记忆体系

| 层 | 存储内容 | 例子 |
|----|----------|------|
| **Memory** | 用户偏好/环境事实/踩坑教训 | "ISR内禁printf"、"Dongle 50ms延迟是甲方硬约束" |
| **Wiki** | 结构化知识库 (12文件) | BLE Mesh 配网流程、TLSR321X Flash布局 |
| **Skills** | 可执行的流程模板 (162个) | MCU固件开发规范、DALI协议参考、UART ISR模板 |

### 4. 边界交叉验证

嵌入式固件 70% 的 bug 不在单个模块内部，而在模块之间的边界：

| 边界 | 检查项 |
|------|--------|
| **UART** | 帧格式一致性 / 波特率 / DMA vs 字节中断 / TXDONE 排水 |
| **Mesh** | 分包序号 / `pending_valid` 状态 / `data_len` off-by-1 / Opcode 冲突 |
| **Flash** | MAC 保护区 (0xFF000) / 校准区 (0xFE000) / 4KB 擦除粒度 |
| **ISR** | 临界区保护 / 中断内禁 printf / `uart_set_irq_mask` 覆盖陷阱 |

### 5. SOUL.md 行为约束

每个 Agent 有不可覆盖的"灵魂文件"——定义身份、能力边界、铁律。这解决了"Agent 在长期运行中行为漂移"的问题。

### 6. 防误判模式

派 Claude Code 审查代码时附带**完整设计决策背景**：
- 为什么这样改（协议约束、甲方要求、硬件限制）
- 外部状态（其他板子的配合逻辑、上位机期望格式）
- 实测结果（串口助手抓包 hex dump）
- 用户已确认的设计选择

防止 AI 将设计选择误判为 bug。

### 7. 安全并行委派

`delegate_task` 走 deepseek-v4-flash 子 agent 且 max_concurrent_children 有限。真正的并行靠 `terminal(background=true)`：

```
Hermes 同时开:
├── claude heredoc 审查 Dongle 代码    (background=true)
├── claude heredoc 审查控制板代码      (background=true)
└── OpenClaw 搜索技术方案              (background=true)
```

不限数量。安全规则：不同目录、只读或一读一写、不 make、不同 Git 仓库、不碰 MCP SQLite 写入。

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

# 复制通用脚本
cp scripts/skill-router.py ~/.hermes/scripts/
cp scripts/hermes_loop.py ~/.hermes/scripts/
cp scripts/weekly-report.py ~/.hermes/scripts/
cp scripts/memory-archive.py ~/.hermes/scripts/
cp scripts/memory-health-check.py ~/.hermes/scripts/
cp scripts/pre-update-backup.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/pre-update-backup.sh

# 创建 workspace 目录
mkdir -p ~/.hermes/workspace
```

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

`skill-router.py` 和 `hermes_loop.py` 不依赖任何嵌入式知识，任何语言/领域的 Agent 都能用。

### 如果你是其他领域

`agent-roles.md` 和 `SKILL.md` 中的调度逻辑与领域无关。把三个 Agent 换成你自己的工具链就能复用。

**三层记忆体系**（Memory→Wiki→Skills）是通用的 Agent 知识管理方案，与具体领域无关。

### 如果你刚开始接触 AI Agent

推荐的学习路径：
1. 先熟悉 Claude Code 单 Agent 用法
2. 加入 OpenClaw 做搜索/调研
3. 引入 Hermes 做总调度
4. 配置 SOUL.md + 三层记忆让 Agent 行为稳定
5. 用 Loop 模式让 Agent 自主试错

---

## 设计决策

| 决策 | 原因 |
|------|------|
| 一次只派一个人 | 避免并发冲突，结果可追溯 |
| Agent 与 Skill 分离 | Agent 回答"谁"，Skill 回答"怎么做" |
| `_workspace/` 存档 | 出错后能回溯子 Agent 的输入输出 |
| 边界检查表 | 嵌入式 70% bug 在模块边界 |
| description 含触发场景 | 模糊的 description = skill 不会被自动加载 |
| SOUL.md 铁律 | 用不可覆盖的约束防止 Agent 长期运行时行为漂移 |
| 角色定义单一来源 | agent-roles.md 是唯一权威，SKILL.md 只引不写 |
| 审计日志 JSONL | 每行一条委派记录，可追溯、可统计 |
| 跨 PC 同步不含 config | 防止 API key 通过同步包泄露 |
| 更新前备份 MCP 白名单 | npm 更新可能清空 MCP servers 定义 |
| 并行走 terminal bg 不靠 delegate_task | delegate_task 走子 Agent 非 Claude Code CLI，terminal bg 真正并行 |

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
