# 多 Agent 踩坑大全

> 从 `hermes-orchestrator` SKILL.md 拆分出来的所有陷阱记录。
> 主 skill 只保留调度逻辑，坑放这里按需查阅。

---

## Patch 工具陷阱

### 1. `replace_all=True` 毁掉整个文件

**场景**：修改 `mesh_config.h` 中 `#if(GY_DEV_TP_DONGLE)` 区块的 UART 引脚，但文件里有 5 个设备型号的 `#elif` 区块，每块都有相同的 `#define GY_PIN_UART_TX`。

**正确做法**：old_string 必须包含唯一标识（如 `#if(GY_DEV_TYPE == GY_DEV_TP_DONGLE)`）。如果不唯一，用 `write_file` 重写整个文件。

### 2. Tab 字符变成 `\t` 字面量

`patch` 的 old_string/new_string 中写 `\t` 会被当成两个字面字符。

**正确做法**：直接从源码复制含真实 tab 的文本，或用 `write_file`。

### 3. 花括号匹配被打乱

改控制流结构时（如 `if(len >= 2)` → `if(len < 2) return;`），原来的 `}` 没删导致编译错误。

**正确做法**：用 `write_file` 一次性重写整段函数，不分两次 patch。

### 4. 连续失败 3 次 → `write_file`

当 patch 连续失败 3 次时，切换到 `write_file`，不再尝试 patch。

---

## Claude Code 审查误判

### 误判类型

| 误判 | Claude Code 会说 | 实际原因 |
|------|-----------------|---------|
| 策略选择质疑 | "RXDONE 批量接收在低波特率下不可靠" | 是设计选择，不是 bug |
| 延时参数质疑 | "Flash erase 后只等 10ms 偏极限" | 用户实测确认 OK |
| 调试代码质疑 | "log_printf 应该加条件编译" | 用户主动要求的调试功能 |
| 帧长度越界 | "长度检查不完善" | 模板工程 len 校验已限制在 GY_PARAM_LEN 内 |
| DMA ISR 截断 | "RXDONE 超时截断大数据帧" | DMA 模式不触发此路径 |
| DMA TX 死锁 | "gy_uart_send 内 while(!flag)" | 模板已验证的 DMA 双缓冲设计 |

### 正确委派模式

派 Claude Code 审查必须附带设计决策背景：
1. **为什么要这样改**（根因分析）
2. **外部设备/环境的实际状态**
3. **实测验证结果**
4. **用户确认的修改**

---

## MCP / 配置 陷阱

### npm 更新丢 MCP servers

`npm update -g @anthropic-ai/claude-code` 可能清空 `settings.json` 中 `mcpServers` 段。

**恢复**：
```bash
claude mcp add -s user codegraph -- codegraph serve --mcp
claude mcp add -s user --transport http telink-docs https://telink.mcp.kapa.ai
claude mcp add -s user lighting-protocol -- python3 ~/.hermes/scripts/lighting-protocol-mcp.py
```

**防御**：更新前跑 `bash ~/.hermes/scripts/pre-update-backup.sh`

### MCP 工具权限白名单

新增 MCP Server 后工具被拦截，需把工具名加入 `~/.claude/settings.json` 的 `permissions.allow`。格式：`mcp__<server-name>__<tool-name>`。

### `claude mcp remove` 会清 OAuth token

执行 `claude mcp remove` 时自动清理 `~/.claude/.credentials.json` 中对应 token。不要随意 remove 需 OAuth 的 MCP server。

### Hermes 视觉模型配置

`config.yaml` 有两个 `vision:` 段——`auxiliary.vision`（第184行）和顶层 `vision`（第695行）。实际生效的是 `auxiliary.vision`。`hermes config set vision.model` 只改顶层 → 无效。

---

## OpenClaw 陷阱

### 模型配置路径

`agents.defaults.models` 只是别名表，**不决定实际模型**。默认模型在 `agents.defaults.model.primary`。

正确改法：
```json
"agents": {
  "defaults": {
    "model": {
      "primary": "moonshot/kimi-k2.7-code",
      "fallbacks": ["deepseek/deepseek-v4-flash"]
    }
  }
}
```

### agent --local 不稳定

WSL2 下 `openclaw agent --local` 间歇超时。交互式 `openclaw chat` 更稳定。搜索用 `--timeout 180` + stdout 重定向文件。

### 同时两个 CLI 冲突

两个 `openclaw` 进程抢同一个 session 文件 → 报错 `session file changed`。解决：`pkill` + 删坏 session。

### SearXNG 搜索引擎全 disabled

默认几乎所有引擎 disabled，只剩 sogou。修复：启用 google/bing → 重启 Docker。

### SearXNG 国内 WSL2 基本不可用

google/bing 国内无代理不通。唯一通的 sogou 中文质量差。方案：SearXNG 只做后端，OpenClaw 坐公交过去。

### SkillClaw 代理上下文限制

OpenClaw primary 设为 `skillclaw/skillclaw-model` 时，SkillClaw Proxy (30000端口) 将请求转发到 deepseek-chat，但代理层上下文限制仅 ~12K tokens，触发 `context overflow` 后压缩失败。

**解决**：OpenClaw primary 改用 `moonshot/kimi-k2.7-code` (262K) 直连，绕过 SkillClaw 代理。SkillClaw 仍保留 Evolve 功能，但不做流量中转。

---

## Gitee 推送 陷阱

### WSL2 git push 间歇超时

根因：DNS 污染 + 代理 LAN 未开 + WSL2 NAT 长连接不友好。

修复：
- 开代理 LAN（Windows 代理软件）
- `export https_proxy=http://<proxy-host>:<proxy-port>`

### 单个文件不要连着旧文件走

WSL2 到 Windows 文件系统的 git 操作极慢。方案：`cp -r` 到 `~/tmp/` (ext4) → git push → 删临时目录。

---

## 嵌入式特定陷阱

### `write_file` 覆盖整个文件

不是追加。如果不小心传了部分内容，整个文件被截断。**永远用 `patch` 做修改**。

### 双板协议宏同步

改完 Dongle 的 `wxl_uart.h` 后必须立即检查控制板。详见 `embedded-boundary-checklist.md`。

### 从已有工程创建新工程

必须原封不动拷贝全部文件。禁止以"精简"为由删除 SDK 文件。差异仅通过 `#ifdef` 宏开关控制。

### API Server 安全

`enabled: true` + `key: ""` + `host: 0.0.0.0` + `model: claude-opus-4-7` = 一天泄漏 687 万 token。必须设为 `enabled: false`。
