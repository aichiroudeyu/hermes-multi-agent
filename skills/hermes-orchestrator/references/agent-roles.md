# 四 Agent 角色定义

> 从 `hermes-orchestrator` SKILL.md 中拆分出来的纯角色定义文件。
> 每次修改角色边界只需更新此文件，不影响调度逻辑。
> v2.1：新增 Marvis（系统操作轨）

---

## Hermes — 总调度 + 嵌入式开发轨

### 定位
四 Agent 星型拓扑的核心。分析任务 → 判断该调谁 → 一次只派一个人 → 等【DONE】再派下一个。

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

## Marvis — 系统操作轨

### 定位
Windows 桌面环境智能助手。补 Claude Code 和 OpenClaw 都覆盖不到的空白：文件系统操作、Windows 系统配置、桌面软件自动化。

### 能做
- **文件系统**: 搜索、内容问答、格式转换、批量整理归类
- **系统配置**: Windows 设置查询与修改、定时任务调度、进程管理、窗口桌面管理
- **端侧应用**: Android 模拟器应用控制、微信小程序交互、Windows 桌面软件自动化

### 不能做
- 写嵌入式固件代码 → 派 Claude Code
- 网页搜索/调研 → 派 OpenClaw
- 跨 WSL2 的 Linux 操作 → Hermes 直辖

### 调用方式（文件桥接 + Marvis 定时轮询）

Hermes (WSL2) 和 Marvis (Windows) 跨 OS 边界，通过共享目录通信：

```
  WSL2 (Hermes)                    Windows (Marvis)
  ┌──────────────┐                ┌──────────────────┐
  │ 写 task_N.json│  ──/mnt/c/──▶  │ 定时任务每30分钟   │
  │ 到 bridge/    │                │ 扫描 bridge 目录   │
  │              │  ◀──/mnt/c/──  │ 消费任务→写result  │
  │ 轮询 result   │                │                  │
  └──────────────┘                └──────────────────┘

  共享目录：C:\Users\user\.hermes-marvis-bridge\
  WSL2 路径：/mnt/c/Users/user/.hermes-marvis-bridge/
```

Marvis 使用自身定时任务能力自动扫描，无需外部守护脚本。30 分钟延迟对嵌入式固件开发场景完全可接受。

任务格式 (`task_{id}.json`)：
```json
{
  "task_id": "task_001",
  "task": "将桌面下所有 PDF 按年份归类到子文件夹",
  "priority": "normal",
  "timestamp": "2026-07-01T12:00:00+08:00"
}
```

结果格式 (`task_{id}_result.json`)：
```json
{
  "task_id": "task_001",
  "status": "DONE",
  "summary": "已将 23 个 PDF 按年份归入 5 个子文件夹",
  "artifacts": [],
  "timestamp": "2026-07-01T12:00:15+08:00"
}
```

### 并发锁约定
- Hermes 写任务前检查同名 result 不存在（幂等）
- Marvis 处理前将任务文件重命名为 `task_{id}_processing.json`
- Hermes 超时 35 分钟（30 分钟轮询间隔 + 5 分钟执行时间），超时视为失败

### 触发关键词
文件整理、格式转换、批量重命名、查找文件、系统设置、定时任务、进程管理、桌面整理、打开/关闭/安装/卸载应用、Windows 配置

---

## 星型通信协议

```
用户 (@Hermes) → Hermes 分析
                   │
      ┌────────────┼────────────┬────────────┐
      ▼            │            ▼            ▼
 纯聊天/        需要代码     需要搜索     需要系统操作
 简单任务        工作         任务         /文件管理
      │            │            │            │
      ▼            ▼            ▼            ▼
  Hermes      Claude Code   OpenClaw      Marvis
  自己答      --max-turns 8  --timeout 120  文件桥接
      │            │            │            │
      └────────────┼────────────┼────────────┘
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
