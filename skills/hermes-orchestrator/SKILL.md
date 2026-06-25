---
name: hermes-orchestrator
description: "Hermes 三Agent团队调度的核心规则。在以下场景必须加载: (1) 用户提到'调Claude Code'/'写代码'/'审查代码', (2) 需要搜资料时决定用curl还是OpenClaw, (3) 飞书收到@消息需要分析任务类型, (4) Agent更新/配置变更。不用于: Hermes自带的文件读写(那是terminal工具的事)。"
version: 6.1.0
author: Hermes Agent
tags: [Multi-Agent, Orchestrator, Claude, OpenClaw, Feishu]
related_skills: [claude-code, mcu-firmware-dev, wsl2-setup, dali-protocol-reference]
---

# Hermes 三 Agent 星型调度架构 v6.0

## 架构总览

```
                    ┌──────────────┐
                    │   飞书/CLI    │  ← 双入口
                    └──────┬───────┘
                           │ @Hermes 发任务
                           ▼
              ┌─────────────────────────┐
              │     Hermes（总调度）      │
              │  开发轨 + 记忆 + 编译     │
              │  分析任务 → 判断该调谁    │
              └──┬──────────┬────────────┘
                 │          │
         调代码  │          │ 搜资料
                 ▼          ▼
          ┌──────┐     ┌──────┐
          │Claude│     │Open  │
          │ Code │     │Claw  │
          │写代码│     │搜资料│
          └──────┘     └──────┘

  OpenHuman 已退役（源码保留 ~/openhumaource/，需用时可重新加入）
```

> **详细角色定义、工具链、通信协议**: `references/agent-roles.md`

---

## 一、真隔离

三个 Agent 是三个独立进程，物理隔离：

| Agent | 进程 | 崩溃影响 |
|-------|------|---------|
| Hermes | `hermes gateway run` (systemd) | 总调度崩，全员停 |
| Claude Code | `claude -p` 一次性调用 | 崩了只丢当前任务，Hermes 重试 |
| OpenClaw | `openclaw agent` 一次性调用 | 同上 |

**规则：任一子 Agent 崩了，Hermes 捕获错误，最多重试 2 次，然后汇报失败。**

### `_workspace/` 中间产物存档

每次派子 Agent 前，把输入 prompt 写入 `~/.hermes/workspace/`，子 Agent 返回的 `【DONE】` 完整内容也存档。用于事后审计。

```bash
# 派 Claude Code 前
echo "$prompt" > ~/.hermes/workspace/$(date +%Y%m%d_%H%M)_claude-code_${task}.md

# 子 Agent 返回后，存档
cat > ~/.hermes/workspace/$(date +%Y%m%d_%H%M)_claude-code_${task}_result.md << 'AGENT_OUTPUT'
<子Agent返回的完整内容含【DONE】>
AGENT_OUTPUT
```

命名规范：`{YYYYMMDD_HHMM}_{agent}_{task}.md` 和 `{YYYYMMDD_HHMM}_{agent}_{task}_result.md`

**不存 `_workspace/` 的情况**：Hermes 自己处理的纯聊天/简单命令/文件读写/API 查询。只存委派给子 Agent 的任务。

---

## 二、接力不群殴（时序控制）

**核心规则：Hermes 一次只派一个人，等结果回来再派下一个。**

```
任务流程：

1. 用户发任务（飞书 @Hermes 或 CLI）
        │
2. Hermes 分析任务类型
        │
   ┌────┼────┐
   ▼    ▼    ▼
  需要  需要  需要
  代码  搜索  平台
        │
3. 调对应 Agent（只调一个！）
        │
4. 等待 Agent 返回结果（必须带【DONE】）
        │
5. Hermes 审查输出质量
   ├─ 合格 → 汇报用户，任务结束
   ├─ 需要补充 → 调同一个 Agent 继续
   └─ 需要下一步 → 调下一个 Agent（严格串行）
        │
6. 任务完结 → 发送【任务结束】→ 不 @ 任何人
```

**强制规则：**
- `delegate_task` 一次最多派 1 个子任务
- 严禁同时调 Claude Code + OpenClaw
- 必须等上一步的【DONE】信号，才能走下一步

---

## 三、三层终结机制

### 第一层：只响应 @ 自己的消息
飞书群聊中只处理 @ 自己的消息。

### 第二层：统一结束词【DONE】
每个子 Agent 返回结果必须以 `【DONE】` 结尾。

Claude Code 调用时追加：
```
--append-system-prompt "完成任务后，在回复末尾输出【DONE】。"
```

### 第三层：收尾不 @ 任何人
Hermes 汇报最终结果时，不 @ 任何子 Agent。用 `【任务结束】` 结尾。

### 死循环防护
- Claude Code 固定 `--max-turns 8`
- OpenClaw 固定超时 120s
- 无 `【DONE】` → 重试最多 2 次 → 终止

---

## 四、防误判模式（委派 Claude Code 审查）

> **完整误判表 + 背景注入模板**: `references/pitfalls-collection.md` § Claude Code 审查误判

核心原则：派 Claude Code 审查必须附带设计决策背景（根因 + 外部状态 + 实测结果 + 用户决策）。

---

## 五、管理层

### 执行纪律
- **宣布即执行**：说"开始"之后立即动手，不得空转
- 写完代码后用 `rtk` 前缀命令保持 token 节省

### 成本感知
每次派 Agent 前估算成本：💰 预估成本：Claude Code ~$0.15 | OpenClaw ~$0.05

---

## 六、调用规范

### Claude Code
```bash
cd /path/to/project && claude -p "任务" \
  --add-dir /path/to/project \
  --max-turns 8 \
  --permission-mode bypassPermissions \
  --output-format text \
  --append-system-prompt "完成任务后末尾输出【DONE】。"
```

**铁律**：Telink 项目必须注入 "用 telink-docs MCP 查 SDK API"

### OpenClaw
```bash
openclaw agent --agent main --session-id "id-$(date +%s)" --local \
  --message "搜索任务。末尾输出【DONE】。" \
  --timeout 120
```

---

## 七、模型分层策略

```
调度层: deepseek-v4-pro @ DeepSeek (Hermes CLI)
视觉层: claude-opus-4-8 @ apikeyfun (vision_analyze)
代码层: claude-opus-4-8 @ apikeyfun (Claude Code)
搜索层: kimi-k2.7-code @ moonshot + deepseek-v4-flash (OpenClaw)
委派层: deepseek-v4-flash @ DeepSeek (子 Agent)
```

---

## 八、共享记忆（Wiki 层）

Wiki 位于 `~/.hermes/wiki/`，是所有 Agent 的共享知识库。

| 目录 | 用途 |
|------|------|
| `system/` | 系统级知识（角色、环境、约束） |
| `projects/3218/` | 3218 项目（实战教训） |
| `pages/` | 百科式知识页面 |

---

## 九、飞书触发规则

1. 纯聊天/咨询 → Hermes 自己回答
2. 代码任务 → 调 Claude Code
3. 搜索任务 → 调 OpenClaw
4. 飞书通知 → Hermes 直连（WebSocket）

回复格式：
```
[分析结果]

[子Agent输出 或 直接回答]

【任务结束】
```

---

## 十、Agent 更新流程

> ⚠️ **更新前必须备份**：`bash ~/.hermes/scripts/pre-update-backup.sh`

```bash
proxy
hermes update
npm install -g @anthropic-ai/claude-code@latest openclaw@latest
```

**更新后必检**：`hermes status` / `claude mcp list` / `openclaw models` / API Server enabled=false

> **更新风险速查**: `references/pitfalls-collection.md` § MCP/配置陷阱

---

## 十一、Skills 保护规则

- `curator.enabled: false` 永久禁用自动清理
- 所有 agent 创建的 skill 必须 `pin` 保护
- Hermes 更新后必须检查 curator 状态

---

## 十二、API Server 安全

`enabled: true` + `key: ""` + `host: 0.0.0.0` + `model: claude-opus-4-7` = 单日 687 万 token 泄漏。

**永远设为 `enabled: false`。**

---

## 十三、嵌入式开发约束

> **UART/Mesh/Flash/ISR 边界交叉验证清单**: `references/embedded-boundary-checklist.md`

核心铁律：
- 禁止擦写 Flash 0xFF000 (MAC) 和 0xFE000 (校准)
- 中断保护用 `__disable_irq` 桥接
- `uart_set_irq_mask` 单次调用合并所有 mask（多次调用 = 覆盖）
- 所有 Telink 项目委派 Claude Code 时注入 telink-docs MCP 指令
- 代码用 snake_case，中文注释

---

## 十四、Session 闭幕铁律

每次大范围改动/更新后必须走完以下闭环：

1. **完整验证**：Hermes Gateway/OpenClaw Gateway systemd → `claude mcp list` 全部 ✔ → SearXNG 搜索→ SkillClaw `v1/models` → Agent-Reach `--version`
2. **验证后推送**：用 HTTPS + 代理 (`export https_proxy=...; git push`)
3. **README.md 更新时间**：`sed -i "s/^> 最后更新.*/> 最后更新：$(date)/" README.md`
4. **会话内完成所有变更**：skill/reference/README 必须在关闭会话前完成并推送，不依赖后台 cron

---

## 参考文件

```
references/
├── agent-roles.md                  ← 三 Agent 角色定义 + 通信协议
├── embedded-boundary-checklist.md  ← UART/Mesh/Flash/ISR 边界检查表
├── pitfalls-collection.md          ← 所有踩坑记录（patch/审查/MCP/OpenClaw/SkillClaw/Gitee）
├── search-strategy.md              ← 搜索策略 v3：OpenClaw 统一搜索
├── harness-analysis.md            ← harness 设计模式分析（2026-06-25 源码学习）
├── gitee-capacity-limits.md       ← Gitee 免费版 500MB/5GB 限额
├── feishu-setup-pitfalls.md
├── telink-mcp-oauth-persistence.md
├── webui-model-picker-debug.md
├── searxng-wsl2-troubleshooting.md
├── gitee-wsl2-push-issues.md
├── protocol-mcp-workflow.md
├── wiki-knowledge-feedback.md
├── api-server-token-leak.md
└── ...
```

---

> **版本**: v6.1.0 (2026-06-25) — 新增 Session 闭幕铁律（完整验证+HTTPS推送+README更新+会话内完成）。descriptions 全量升级 → 含触发场景+排除规则。
