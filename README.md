# Hermes Multi-Agent — 三 Agent 星型调度架构

> 一个自学的嵌入式程序员，用 AI 不停摸索出来的多 Agent 协作体系。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

📖 [中文完整版](README_CN.md) | 📖 [English Full Version](README_EN.md)

---

## 一句话介绍

**Hermes 总调度 + Claude Code 写代码 + OpenClaw 搜资料 — 一次只派一个人，等 `【DONE】` 再派下一个。**

---

## 我是谁

自学嵌入式程序员。没有 CS 背景，靠着对硬件的热爱和对 AI 的死磕，一个人摸索出一套真正能用的三 Agent 协作体系。这个项目来自真实的 BLE Mesh 固件开发日常——不是论文，是实战。

**根据使用经验持续迭代中。**

---

## 快速开始

```bash
cp -r skills/hermes-orchestrator ~/.hermes/skills/autonomous-ai-agents/
mkdir -p ~/.hermes/workspace
```

---

## 文件

```
skills/hermes-orchestrator/
├── SKILL.md                          # 核心调度 (283行)
└── references/
    ├── agent-roles.md                # 角色定义+协议
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR 检查表
    └── pitfalls-collection.md       # 多 Agent 陷阱集
scripts/pre-update-backup.sh          # 更新前备份
```

---

## License

MIT
