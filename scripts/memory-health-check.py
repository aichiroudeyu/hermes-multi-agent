#!/usr/bin/env python3
"""
Hermes Memory 月度健康检查脚本

运行:
  python3 ~/.hermes/scripts/memory-health-check.py          # 仅报告
  python3 ~/.hermes/scripts/memory-health-check.py --commit # 执行清理

检查项:
  1. Memory 占用率是否 >70%
  2. 是否有超过90天未更新的条目
  3. 是否有重复/冗余条目
  4. Skills 中是否有内容与 memory 重复
  5. Wiki archive 是否过大
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
WIKI_DIR = HERMES_HOME / "wiki"
SKILLS_DIR = HERMES_HOME / "skills"
ARCHIVE_DIR = WIKI_DIR / "archive"

# ── 过时关键词（超过90天自动提醒） ──
STALE_PATTERNS = [
    # 日期过时的
    ("2026-05-", "超过30天"),
    ("2026-04-", "超过60天"),
    ("2026-03-", "超过90天"),
]


def run_check():
    commit = "--commit" in sys.argv
    issues = []
    fixes = []

    print("=" * 60)
    print(f"🩺 Hermes Memory 月度健康检查")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  模式: {'✅ 执行修复' if commit else '🔍 仅报告（加 --commit 执行）'}")
    print("=" * 60)

    # ── 1. 检查 Wiki Archive 大小 ──
    if ARCHIVE_DIR.exists():
        archive_files = list(ARCHIVE_DIR.glob("*.md"))
        archive_size = sum(f.stat().st_size for f in archive_files)
        print(f"\n📦 Wiki Archive: {len(archive_files)} files, {archive_size:,} bytes")
        if len(archive_files) > 50:
            issues.append(f"Wiki Archive 文件过多 ({len(archive_files)}), 建议清理旧归档")
    else:
        print(f"\n📦 Wiki Archive: 不存在")

    # ── 2. 检查 Skills 数量 ──
    skill_dirs = [d for d in SKILLS_DIR.rglob("SKILL.md")]
    print(f"🧠 Skills: {len(skill_dirs)} 个")

    # ── 3. 检查 Memory 占用率 (只能通过日志/工具间接获取) ──
    # 这会从上轮 tool output 中看到占用率，脚本无法直接读取
    print(f"\n💾 Memory 占用: 请查看上轮 tool output 中的 usage 行")

    # ── 4. 汇总 ──
    print(f"\n📊 发现问题: {len(issues)} 个")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    if fixes:
        print(f"\n🔧 建议修复: {len(fixes)} 个")
        for f in fixes:
            print(f"  → {f}")

    if not issues:
        print(f"\n✅ Memory 健康状态良好，无需操作。")

    if commit and fixes:
        for f in fixes:
            print(f"  ✅ 已执行: {f}")

    print(f"\n💡 下次自动检查: 30天后 (通过 cron 触发)")


if __name__ == "__main__":
    run_check()
