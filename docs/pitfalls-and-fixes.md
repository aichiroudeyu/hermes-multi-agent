# Agent 体系更新后问题记录

> 时间：2026-06-18 ~ 2026-06-29
> 触发事件：Hermes/Claude Code/OpenClaw 三 Agent 同步更新
> 收录 13 个已解决问题

---

## 问题速览

| # | 问题 | 严重度 | 状态 |
|---|------|:---:|:---:|
| 1 | Claude Code 新版本启动卡死 | RED | DONE 回退 2.1.175 |
| 2 | pipe/heredoc 调用方式逐一失效 | RED | DONE heredoc 唯一可靠 |
| 3 | SearXNG wikidata 引擎初始化超时 | RED | DONE inactive: true |
| 4 | 容器重建后代理环境变量丢失 | RED | DONE 重建+注入代理 |
| 5 | JSON API 403 Forbidden | RED | DONE 配置恢复 |
| 6 | MCP servers 更新后清空 | YELLOW | DONE pre-update-backup |
| 7 | hermes-web-ui 意外停止 | YELLOW | DONE 手动重启 |
| 8 | OpenClaw SearXNG 双开关 | YELLOW | DONE 配置补丁 |
| 9 | GLM-5.2 环境变量 | YELLOW | DONE 用户终端手动 |
| 10 | config.yaml API key 泄露 | YELLOW | DONE 移除打包 |
| 11 | delegate_task 无主动通知 | GREEN | DONE 行为约定 |
| 12 | 代理端口 8566→7897 | GREEN | DONE bashrc 更新 |
| 13 | Google/DDG CAPTCHA | GREEN | WARN 不可避 |

---

## 关键教训

### 1. Hermes 安全过滤器截断 token
所有经 Hermes terminal 写入的 API key 被替换为 `sk-xxxx...xxxx`。
涉及 token 的文件一律用户手动编辑。

### 2. SearXNG disabled vs inactive
`disabled: true` 不阻止引擎初始化，`ProcessorMap.init()` 只检查 `inactive`。
禁用引擎用 `inactive: true` 或 `use_default_settings.engines.remove`。

### 3. Claude Code 双模型配置
- opus-4-8：settings.json env 段控制，默认模型
- DeepSeek v4-pro：alias ccds，环境变量临时覆盖
- Hermes terminal 不可传 token，DeepSeek 委派需用户手动

### 4. 容器网络依赖代理
`podman run -e http_proxy=... -e https_proxy=...`

### 5. 同步安全
不同步 API key、本地 IP、端口号。
daily-sync.sh 移除 config.yaml 打包。

---

## 更新日期
2026-06-29
