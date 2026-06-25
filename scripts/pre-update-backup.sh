#!/bin/bash
# 更新前备份所有 Agent 配置
BACKUP_DIR="$HOME/.hermes/backups/pre-update-$(date +%Y%m%d_%H%M)"
mkdir -p "$BACKUP_DIR"

# Hermes 配置
cp ~/.hermes/config.yaml "$BACKUP_DIR/"
cp ~/.hermes/auth.json "$BACKUP_DIR/" 2>/dev/null

# Claude Code 配置
cp ~/.claude/settings.json "$BACKUP_DIR/" 2>/dev/null
cp ~/.claude.json "$BACKUP_DIR/" 2>/dev/null
cp ~/.claude/.credentials.json "$BACKUP_DIR/" 2>/dev/null

# OpenClaw 配置
cp ~/.openclaw/openclaw.json "$BACKUP_DIR/" 2>/dev/null

# SkillClaw 配置
cp ~/.skillclaw/config.yaml "$BACKUP_DIR/" 2>/dev/null

# Agent-Reach 配置
cp -r ~/.agents/skills/agent-reach "$BACKUP_DIR/" 2>/dev/null
cp -r ~/.claude/skills/agent-reach "$BACKUP_DIR/claude-skill-agent-reach" 2>/dev/null
cp -r ~/.openclaw/skills/agent-reach "$BACKUP_DIR/openclaw-skill-agent-reach" 2>/dev/null

# MCP 工具白名单（permissions.allow 中的 mcp 条目）
python3 -c "
import json
c = json.load(open('$HOME/.claude/settings.json'))
permits = c.get('permissions', {}).get('allow', [])
mcp_tools = [t for t in permits if 'mcp__' in t]
with open('$BACKUP_DIR/mcp-allowlist.txt', 'w') as f:
    for t in sorted(mcp_tools):
        f.write(t + '\n')
print(f'MCP tools in allowlist: {len(mcp_tools)}')
" 2>/dev/null

# 备份前版本的 npm 列表
npm ls -g --depth=0 > "$BACKUP_DIR/npm-global-versions.txt" 2>/dev/null

# 生成更新风险提示文件
cat > "$BACKUP_DIR/RISK-NOTES.md" << 'EOF'
# 更新风险提示（2026-06-25 实战总结）

## 会丢失的配置
| 场景 | 丢失内容 | 恢复方式 |
|------|---------|---------|
| npm 更新 Claude Code | MCP servers 定义可能清空 | `claude mcp add` 逐个重新注册 |
| Claude Code 更新 | permissions.allow 白名单 | 从此备份的 mcp-allowlist.txt 恢复 |
| `/tmp` 被清理 | git clone 源码 + venv | 重新 git clone + pip install |
| npm 更新后 systemd unit | 版本号标注（纯 cosmetic） | 不影响功能，可忽略 |

## 不会丢失的配置
| 文件 | 内容 |
|------|------|
| `~/.claude/.credentials.json` | OAuth token（独立文件，不受 npm 影响）|
| `~/.hermes/config.yaml` | Hermes 主配置（hermes update 不覆盖）|
| `~/.openclaw/openclaw.json` | OpenClaw 配置（npm 升级不覆盖）|
| `~/.claude/skills/` | Claude Code skills（持久目录）|
| `~/.openclaw/skills/` | OpenClaw skills（持久目录）|
| `~/.hermes/skills/` | Hermes skills（持久目录）|

## MCP Server 恢复速查
```bash
claude mcp add -s user codegraph -- codegraph serve --mcp
claude mcp add -s user --transport http telink-docs https://telink.mcp.kapa.ai
claude mcp add -s user lighting-protocol -- python3 ~/.hermes/scripts/lighting-protocol-mcp.py

# 然后手动恢复 permissions.allow 白名单
```
EOF

echo "✅ 备份完成: $BACKUP_DIR"
ls -la "$BACKUP_DIR/"
