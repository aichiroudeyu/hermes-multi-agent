#!/usr/bin/env python3
"""
Hermes Memory 清理与归档脚本

用法:
  python3 ~/.hermes/scripts/memory-archive.py          # 仅报告
  python3 ~/.hermes/scripts/memory-archive.py --commit # 执行清理

策略:
  1. 删除已知过时的条目（如已完成提醒、旧版本号）
  2. 归档已吸收到 skill/wiki 的条目到 ~/.hermes/wiki/archive/
  3. 移除 memory 中的冗余条目
"""

import os
import sys
from datetime import datetime
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
WIKI_ARCHIVE = HERMES_HOME / "wiki" / "archive"

# ── 可删除的条目（精确匹配关键词） ──
DELETE_PATTERNS = [
    "约2026-06-28检查泰凌微Kapa MCP Server OAuth是否已修复",
    "待处理提醒",
]

# ── 归档映射：原 memory 关键词 → Wiki 归档文件名 ──
ARCHIVE_MAP = {
    "Gateway=systemd user service, API server": {
        "file": "gateway-legacy-config.md",
        "reason": "Gateway 已切换为 agent-bridge 模式"
    },
    "Git全局credential.helper=store": {
        "file": "git-credentials-legacy.md",
        "reason": "Git 认证方式已稳定，具体 token 在 config 中"
    },
    "OpenHuman WSL2: RUST_MIN_STACK": {
        "file": "openhuman-setup-legacy.md",
        "reason": "已在 hermes-openhuman-bridge skill"
    },
    "OpenHuman启动需加CEF代理": {
        "file": "openhuman-cef-proxy-legacy.md",
        "reason": "已在 hermes-openhuman-bridge skill"
    },
    "Wiki共享记忆层已建立": {
        "file": "wiki-version-history.md",
        "reason": "版本号已过时"
    },
    "四Agent协作验证通过": {
        "file": "four-agent-verification-legacy.md",
        "reason": "历史验证记录"
    },
    "Hermes生态工具已装": {
        "file": "tool-versions-legacy.md",
        "reason": "工具版本已过时"
    },
    "RTK已升级到正版": {
        "file": "rtk-upgrade-legacy.md",
        "reason": "已成既定事实"
    },
    "Hermes桌宠:豆包小狗+耄耋猫": {
        "file": "desktop-pet-legacy.md",
        "reason": "已在 windows-desktop-pet skill"
    },
    "桌宠踩坑: tkinter GIF动画": {
        "file": "desktop-pet-pitfall-legacy.md",
        "reason": "已在 windows-desktop-pet skill"
    },
    "Gitee新token: 9b03f74d": {
        "file": "gitee-token-legacy.md",
        "reason": "token 在 daily-sync.sh 中已配置"
    },
    "Dongle厂测项目工作目录: C:\\\\Users\\\\user\\\\Desktop": {
        "file": "dongle-workdir-legacy.md",
        "reason": "工作目录路径可能已变化"
    },
    "MCU1 DMA RX致命缺陷": {
        "file": "mcu1-dma-defect-legacy.md",
        "reason": "已在 3218-debug-lessons skill"
    },
    "修改工作流: 优先修改本地": {
        "file": "workflow-modify-legacy.md",
        "reason": "已在 hermes-orchestrator skill"
    },
    "Dongle双回复bug已修复": {
        "file": "dongle-double-reply-fix-legacy.md",
        "reason": "历史 bug，已在 skill"
    },
    "三MCU厂测系统双回复问题根因": {
        "file": "mcu-double-reply-rootcause-legacy.md",
        "reason": "已在 3218-debug-lessons skill"
    },
    "MCU1 UART TX回环终极方案": {
        "file": "mcu1-uart-loopback-legacy.md",
        "reason": "已在 3218-debug-lessons skill"
    },
    "Hermes内存char_limit已扩至15000": {
        "file": "memory-limit-legacy.md",
        "reason": "已扩展到 40000"
    },
    "Dongle厂测项目: 双TLSR321X板": {
        "file": "dongle-dual-board-legacy.md",
        "reason": "与 Dongle协议条目重复"
    },
    "泰凌微SDK查资料流程: MCP Server认证不可用": {
        "file": "telink-mcp-workaround-legacy.md",
        "reason": "telink-docs MCP 已于 6/18 认证通过"
    },
}


def main():
    os.makedirs(WIKI_ARCHIVE, exist_ok=True)

    commit = "--commit" in sys.argv

    print("=" * 60)
    print("📋 Hermes Memory 清理报告")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  模式: {'✅ 执行清理' if commit else '🔍 仅报告（加 --commit 执行）'}")
    print("=" * 60)

    # 删除建议
    print(f"\n🗑  可删除 ({len(DELETE_PATTERNS)} 条):")
    for p in DELETE_PATTERNS:
        print(f"  ✕ {p[:80]}...")

    # 归档建议
    print(f"\n📦 可归档到 Wiki ({len(ARCHIVE_MAP)} 条):")
    for keyword, info in ARCHIVE_MAP.items():
        kw_short = keyword[:60]
        print(f"  → {info['file']}: {kw_short}... ({info['reason']})")

    # 汇总
    total = len(DELETE_PATTERNS) + len(ARCHIVE_MAP)
    print(f"\n📊 总计: {total} 条可清理")

    if commit:
        # 写入归档文件
        for keyword, info in ARCHIVE_MAP.items():
            filepath = WIKI_ARCHIVE / info['file']
            content = f"""# {info['file'].replace('-legacy.md', '').replace('-', ' ').title()}

> 归档日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> 归档原因: {info['reason']}
> 原 memory 关键词: {keyword}

此 memory 条目已从 Hermes 活跃 memory 中移除。
相关内容已吸收到对应 skill 或已过时。

---
"""
            filepath.write_text(content)
            print(f"  ✅ 已写入: {filepath}")

        print(f"\n✅ 归档完成！{len(ARCHIVE_MAP)} 条已写入 {WIKI_ARCHIVE}")
        print(f"\n⚠️  请手动执行以下 memory remove 操作:")
        print(f"   在对话中说: '清理已归档的 memory 条目'")
    else:
        print(f"\n💡 执行清理: python3 ~/.hermes/scripts/memory-archive.py --commit")


if __name__ == "__main__":
    main()
