# Hermes Multi-Agent 体系演进历程

> 从"让 AI 帮我写几行代码"到一个有灵魂、有记忆、能自我进化的四 Agent 协作体系。
> 时间跨度：2026-05 ~ 2026-07

---

## 阶段一：单 Agent 裸用 (2026-05 之前)

**状态**: Claude Code 独立使用，Hermes 独立使用，互不通信。

**痛点**:
- Claude Code 改代码不错，但搜技术资料要退出换 OpenClaw，切来切去
- Hermes 有 terminal 全权限但不会写复杂代码
- 每个 session 从零开始，没有记忆——每次都要重新交代项目背景

---

## 阶段二：手工调度 (2026-05 初)

**突破**: 让 Hermes 来分析任务类型 → 手动告诉用户该调谁。

```
用户 → Hermes（分析） → "建议调 Claude Code 改代码"
                        → 用户手动切过去
```

**有了但别扭**：Hermes 只能建议，不能真正"调"另一个 Agent。

---

## 阶段三：星型调度 v1.0 (2026-05-20)

**突破**: `delegate_task` 工具让 Hermes 真正调度子 Agent。

```
用户 → Hermes → delegate_task(Claude Code) → 等返回 → delegate_task(OpenClaw)
```

**此时架构**:
- `hermes-orchestrator` skill 诞生
- 确立"一次只派一个人"原则
- 确立 `【DONE】` 通信协议

**问题**: Agent 仍然没有记忆。下次 session 不知道上次做了什么。

---

## 阶段四：Memory 层 (2026-05-21)

**突破**: Hermes memory 工具 + Wiki 共享知识层。

- **Memory**: 用户偏好、环境信息、踩坑记录持久化
- **Wiki**: 12 个 Markdown 文件组成结构化知识库（BLE Mesh 基础、TLSR321X 手册、多 Agent 架构）

每次新 session 自动注入 Memory + 相关 Wiki → Hermes 不再从零开始。

---

## 阶段五：Skills 爆炸 + 自动路由 (2026-06)

**突破**: 162 个 Skills 覆盖嵌入式、DevOps、飞书、MLOps。

**问题**: Skills 太多了，手动挑不现实。

**方案**: `skill-router.py` — 抓取用户输入关键词 → 匹配 skills → 自动加载。

```bash
python3 ~/.hermes/scripts/skill-router.py "Debug Dongle UART 双回复问题"
# → 推荐: dongle-factory-test, 3218-debug-lessons, mcu-dual-uart-bridge
```

---

## 阶段六：SOUL.md + 行为约束 (2026-06)

**问题**: Agent 长期运行后行为漂移——忘记自己的角色、越过能力边界。

**方案**: SOUL.md — 每次启动注入，不可覆盖。

```
定义:
- 我是谁（身份、模型、专长）
- 我能做什么 / 不能做什么
- 我的四个手下及分工
- 我遵守的铁律（安全、3218 项目、工作流）
```

这是整个体系最关键的转变：从"工具"到"有身份的同事"。

---

## 阶段七：Loop 模式 + MCP 生态 (2026-06 下旬)

**Loop 模式**: 设定目标+验收标准 → Hermes 自动循环委派 → 裁判审查 → 不通过重来。

```
python3 hermes_loop.py --goal "..." --acceptance "..." --max-loops 5
```

**MCP Server 生态**:
- CodeGraph: 代码关系图谱索引（支持 7 个项目）
- Agent-Reach: 国内平台搜索（B站/小红书）
- lighting-protocol: DALI/DMX 协议查询
- token-savior: Token 压缩
- telink-docs: Telink 官方 SDK 文档

Agent 工具链变得可插拔、可扩展。

**并行委派**: `delegate_task` 走 deepseek-v4-flash 子 agent、max_concurrent_children=3，实用性有限。真正并行靠 `terminal(background=true)` 同时开多个 Claude Code CLI heredoc，不限数量。双板代码审查、搜索+写代码同时进行时主动并行。安全规则：不同目录、只读或一读一写、不 make、不同 Git 仓库、不碰 MCP SQLite 写入。

---

## 阶段八：跨 PC 同步 + 安全治理 (2026-06-29)

**双 PC 同步**: `daily-sync.sh` 自动打包同步 skills/wiki/scripts，但**排除 API key 和本地环境配置**。

**安全加固**:
- `pre-update-backup.sh` 防 npm 更新清空 MCP
- `api-leak-prevention` skill 记录 3 次泄露教训
- Hermes 安全过滤器规则确认（写文件时截断 token 的根因）

---

## 阶段九：Marvis 通道 + 开源 (2026-07-01)\n\n**四 Agent 体系建立**: 新增 Marvis（腾讯桌面 AI 助手 v1.60）作为系统操作轨。\n\n**Marvis 文件桥接**:\n- 共享目录 `C:\\Users\\user\\.hermes-marvis-bridge\\`\n- `bridge-listener.py` 2 秒实时轮询（pythonw 后台无窗口）\n- `schtasks ONLOGON` 开机自启（需完整 pythonw 路径，延迟 30 秒）\n- `winotify` 桌面通知（替代不兼容 Python 3.12 的 win10toast）\n- 通信协议: task → processing → result JSON\n\n**流程**:\n```\nHermes(WSL2) 写 task.json → bridge-listener 2s内标记processing → winotify弹通知\n→ 用户看到通知 → 手动找Marvis执行 → Marvis写回result.json → Hermes读取\n```\n\n**已知限制**: Marvis 无 CLI/HTTP API，用户需手动转发。未来等 Marvis 开放本地 API 后升级为全自动。\n\n**开源**: `aichiroudeyu/hermes-multi-agent` MIT 许可

---

## 关键设计决策时间线

| 时间 | 决策 | 为什么 |
|------|------|--------|
| 05-20 | 一次只派一个人 | 避免并发冲突，结果可追溯 |
| 05-21 | 三层记忆分离 | 不同频次的更新节奏、不同的查询模式 |
| 06-04 | SOUL.md 铁律 | 防止 Agent 长期运行行为漂移 |
| 06-22 | Skill description 含触发场景 | 模糊的 description = 永远不会被自动加载 |
| 06-25 | 跨 PC 同步不含 config | 防止 API key 泄露 |
| 06-25 | 更新前备份 MCP | npm 更新可能清空 MCP servers |
| 06-29 | GitHub 开源 MIT | 让更多嵌入式+AI 交叉领域的人受益 |
| 06-30 | 并行走 terminal bg 不靠 delegate_task | delegate_task 走子 Agent 非 Claude Code CLI，terminal bg 真正并行 |
| 07-01 | Marvis 文件桥接 2s 实时轮询 | bridge-listener.py + winotify 替代 30min 定时轮询，通道投产 |

---

## 未来方向

- [ ] 四 Agent 扩展（加入 AutoCLI 做固定站点信息采集）
- [ ] DSPy 自动化 prompt 优化
- [ ] CI/CD 自动验证调度正确性
- [ ] 扩展更多芯片平台的检查表

---

*2026-07-01 更新*
