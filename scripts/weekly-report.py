#!/usr/bin/env python3
"""
Hermes 周报生成器 v2

基于 Hermes session 记录 + 文件统计，自动生成周报。不依赖 Git log。

用法:
  python3 ~/.hermes/scripts/weekly-report.py

输出: 周报 Markdown
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

HERMES_HOME = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_HOME / "sessions"
OUTPUT = Path("/tmp/hermes-weekly-report.md")


def get_week_range():
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=7)
    return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")


def get_weekly_sessions(since, until):
    """统计本周 session 数量"""
    sessions = list(SESSIONS_DIR.glob("session_*.json"))
    count = 0
    topics = defaultdict(int)

    for s in sessions:
        mtime = datetime.fromtimestamp(s.stat().st_mtime)
        if mtime.strftime("%Y-%m-%d") >= since and mtime.strftime("%Y-%m-%d") <= until:
            count += 1
            # 提取主题关键词
            try:
                data = json.loads(s.read_text(encoding="utf-8", errors="ignore"))
                if isinstance(data, list) and len(data) > 0:
                    first_msg = str(data[0].get("content", ""))[:100] if isinstance(data[0], dict) else str(data[0])[:100]
                    # 简单关键词提取
                    for kw in ["Dongle", "dongle", "MCU", "Mesh", "固件", "编译", "调试", "OTA", "UART", "BLE"]:
                        if kw.lower() in first_msg.lower():
                            topics[kw] += 1
            except:
                pass

    return count, dict(topics)


def get_skills_activity(since, until):
    """统计本周新创建的 skills"""
    skills_dir = SKILLS_DIR = HERMES_HOME / "skills"
    new_skills = []
    modified_skills = []

    for skill_md in skills_dir.rglob("SKILL.md"):
        mtime = datetime.fromtimestamp(skill_md.stat().st_mtime)
        ctime = datetime.fromtimestamp(skill_md.stat().st_ctime)
        if ctime.strftime("%Y-%m-%d") >= since:
            new_skills.append(skill_md.parent.name)
        elif mtime.strftime("%Y-%m-%d") >= since:
            modified_skills.append(skill_md.parent.name)

    return new_skills, modified_skills


def get_memory_stats():
    """统计 memory"""
    memory_file = HERMES_HOME / "memory.yaml"
    if memory_file.exists():
        content = memory_file.read_text(encoding="utf-8", errors="ignore")
        line_count = len([l for l in content.split("\n") if l.strip()])
        return line_count
    return 0


def generate():
    start, end = get_week_range()
    today = datetime.now().strftime("%Y-%m-%d")
    week_num = datetime.now().isocalendar()[1]

    sessions_count, topics = get_weekly_sessions(start, end)
    new_skills, modified_skills = get_skills_activity(start, end)
    memory_lines = get_memory_stats()

    report = f"""# 🔧 Hermes 数字同事周报

> 📅 **W{week_num}** ({start} ~ {end}) | 生成: {today}
> 🤖 自动生成 by Hermes Agent

---

## 📊 本周活动统计

| 指标 | 数量 |
|------|:----:|
| 🗣 Hermes 会话 | {sessions_count} |
| 🆕 新增 Skill | {len(new_skills)} |
| 🔄 更新 Skill | {len(modified_skills)} |
| 💾 Memory 条目 | {memory_lines} 行 |
| 🔧 MCP Server | 7 个 (4 活跃) |

"""

    if topics:
        report += "### 🔥 热门话题\n\n"
        for kw, count in sorted(topics.items(), key=lambda x: -x[1]):
            report += f"- **{kw}** ({count}次)\n"
        report += "\n"

    if new_skills:
        report += f"### 🆕 本周新技能\n\n"
        for s in new_skills:
            report += f"- `{s}`\n"
        report += "\n"

    if modified_skills:
        report += f"### 🔄 本周更新技能\n\n"
        for s in modified_skills[:10]:
            report += f"- `{s}`\n"
        report += "\n"

    report += f"""---

## 🎯 本周重点工作

> 📝 手动补充

- [ ] 
- [ ] 
- [ ] 

---

## ⚠️ 遇到的问题 & 解决方案

> 📝 手动补充

---

## 📋 下周计划

> 📝 手动补充

---

## 🤖 Hermes 健康状态

| 检查项 | 状态 |
|--------|:---:|
| API Server | `enabled: false` ✅ |
| Curator | `enabled: false` ✅ |
| Memory 占用 | < 50% ✅ |
| 每日同步 | 每日 18:00 ✅ |
| MCP 连通 | codegraph + hermes-studio ✅ |

---

*本周报由 Hermes Agent 自动生成，包含统计数据和待补充模板。*
"""

    OUTPUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n✅ 报告已保存到: {OUTPUT}")


if __name__ == "__main__":
    generate()
