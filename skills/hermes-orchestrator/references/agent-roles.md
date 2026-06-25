# 三 Agent 角色定义

> 从 `hermes-orchestrator` SKILL.md 中拆分出来的纯角色定义文件。
> 每次修改角色边界只需更新此文件，不影响调度逻辑。

---

## Hermes — 总调度 + 嵌入式开发轨

### 定位
三 Agent 星型拓扑的核心。分析任务 → 判断该调谁 → 一次只派一个人 → 等【DONE】再派下一个。

### 能做
- 分析需求、读代码、单文件 patch、编译、Git、记忆管理
- 判断该调谁、等待结果、审查输出、汇报用户
- 飞书直连 (WebSocket)、vision_analyze 看图

### 不能做
- 多文件大规模重写 → 派 Claude Code
- 网页搜索/爬取 → 派 OpenClaw
- 同时派多人干活

### 工具链
- Hermes CLI: deepseek-v4-pro @ DeepSeek
- 视觉: claude-opus-4-8 @ apikeyfun (vision_analyze)
- 委派子 Agent: deepseek-v4-flash @ DeepSeek
- 终端读写、patch、search、memory、session_search

---

## Claude Code — 代码执行轨

### 定位
独立进程。Hermes 调一次处理一个代码任务，返回 `【DONE】` 后退出。

### 能做
- 多文件重写、代码审查、PR review、重构
- 编译验证
- MCP 工具: telink-docs / codegraph / lighting-protocol / token-savior

### 不能做
- 网页搜索、浏览网页、管理 Git
- 碰 .env / config.yaml / 系统文件

### 调用方式
```bash
cd /path/to/project && claude -p "任务" \
  --add-dir /path/to/project \
  --max-turns 8 \
  --permission-mode bypassPermissions \
  --output-format text \
  --append-system-prompt "完成后末尾输出【DONE】。"
```

### 强制规则
- 所有 Telink 项目委派必须在 context 中注入 "用 telink-docs MCP 查 SDK API"
- 所有代码修改 + 审查由 Claude Code 执行，Hermes 只传话
- 审查时附带设计决策背景（防误判模式）

---

## OpenClaw — 搜索轨

### 定位
独立进程。Hermes 调一次处理一个搜索/调研任务，返回 `【DONE】` 后退出。

### 能做
- 网页搜索 (SearXNG 后端)
- 内容抓取、API 文档查阅
- Agent-Reach skill: B站搜索 / RSS / 网页读取

### 不能做
- 写代码、编译、文件操作

### 调用方式
```bash
openclaw agent --agent main --session-id "id-$(date +%s)" --local \
  --message "搜索任务描述。末尾输出【DONE】。" \
  --timeout 120
```

### 配置
- 主力模型: moonshot/kimi-k2.7-code (262K 上下文)
- 备用: deepseek/deepseek-v4-flash
- SearXNG: localhost:8080
- Agent-Reach skill: Panniantong/Agent-Reach v1.5.0

---

## 星型通信协议

```
用户 (@Hermes) → Hermes 分析
                   │
          ┌────────┼────────┐
          ▼        │        ▼
     纯聊天/     需要       需要
     简单任务   代码工作   搜索任务
          │        │        │
          ▼        ▼        ▼
      Hermes   Claude Code  OpenClaw
      自己答    --max-turns 8  --timeout 120
          │        │        │
          └────────┼────────┘
                   ▼
              Hermes 审查
              (检查【DONE】)
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       合格→     需要     异常→
       汇报用户   补充调  重试2次
                 同一    →汇报失败
                 Agent
```
