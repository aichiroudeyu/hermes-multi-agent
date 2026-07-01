#!/usr/bin/env python3
"""
Hermes 自动 Skill 选择器

根据用户输入的关键词，推荐需要加载的 skills。

用法:
  python3 ~/.hermes/scripts/skill-router.py "Debug Dongle UART 双回复问题"

返回:
  - 推荐的 skills 列表
  - 为什么推荐
"""

import json
import re
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes" / "skills"

# ── 关键词 → 技能映射 ──
# 格式: (关键词列表, skill名, 推荐理由)
ROUTES = [
    # 3218 嵌入式
    (["dongle", "厂测", "2525", "0x3333", "0x3334", "gy_uart", "hs帧", "透传"],
     "dongle-factory-test", "Dongle 厂测协议和固件开发规则"),
    (["mcu1", "mcu2", "控制板", "uart桥接", "双mcu"],
     "mcu-dual-uart-bridge", "双MCU UART桥接架构"),
    (["调试", "bug", "双回复", "回声", "回环", "溢出", "卡死"],
     "3218-debug-lessons", "3218调试教训和已知bug"),
    (["telink", "tlsr321x", "tlsr8258", "sdk", "ble mesh"],
     "tl321x-firmware-iron-rules", "TLSR321X固件开发铁律"),
    (["mesh配网", "mesh_info", "provision", "组网"],
     "tl321x-firmware-iron-rules", "Mesh配网铁律"),
    (["固件", "编译", "烧录", "makefile", "eclipse", "工程", ".gitignore"],
     "telink-project-management", "Telink工程管理"),
    (["mcu firmware", "stm32", "嵌入式", "isr", "中断", "dma", "gpio"],
     "mcu-firmware-dev", "MCU固件开发规范"),
    (["blender", "机械臂", "骨骼", "动画", "csv驱动"],
     "blender-python", "Blender机械臂动画"),
    (["mcp", "telink-docs", "kapa", "sdk文档"],
     "telink-mcp-setup", "Telink MCP文档查询"),

    # Agent 体系
    (["编排", "调度", "派任务", "子agent", "orchestrator"],
     "hermes-orchestrator", "四Agent星型调度架构"),
    (["claude code", "委派", "代码审查", "--add-dir"],
     "claude-code", "Claude Code调用规范"),
    (["openclaw", "搜索", "searxng", "网页"],
     "openclaw-searxng-config", "OpenClaw搜索配置"),
    (["openhuman", "飞书", "webhook", "双向通道"],
     "hermes-openhuman-bridge", "Hermes↔OpenHuman通道"),
    (["loop", "循环", "试错", "自主修复", "自动重试"],
     "loop-orchestrator", "Loop自动闭环模式"),

    # 系统运维
    (["api泄露", "安全", "8653", "api_server", "token"],
     "api-leak-prevention", "API泄露预防和排查"),
    (["更新", "升级", "版本", "npm", "hermes update"],
     "hermes-ecosystem-recovery", "生态升级和故障恢复"),
    (["恢复", "同步", "备份恢复", "另一台", "双pc", "另一台pc"],
     "hermes-ecosystem-recovery", "双PC同步和备份恢复"),
    (["配置", "config", "yaml", "模型切换", "provider"],
     "hermes-config-troubleshooting", "配置问题诊断"),
    (["docker", "searxng", "容器"],
     "searxng-docker-setup", "Docker+SearXNG部署"),
    (["wsl2", "wsl", "代理", "proxy", "网络"],
     "wsl2-setup", "WSL2环境和代理配置"),
    (["git", "github", "gitee", "ssh", "token", "推送"],
     "github-ssh-token-workflow", "Git认证工作流"),
    (["飞书", "feishu", "lark", "cli_"],
     "hermes-orchestrator", "飞书集成配置"),

    # 工具类
    (["rtk", "token优化", "节省"],
     "token-optimizer", "RTK token节约"),
    (["记忆", "memory", "归档", "清理"],
     "context-optimization", "上下文和记忆优化"),
    (["桌宠", "exe", "pyinstaller", "tkinter", "gif"],
     "windows-desktop-pet", "Windows桌面宠物"),
    (["截图", "图片", "视觉", "看图"],
     "wsl-windows-utils", "WSL截图工具"),

    # MCP
    (["figma", "设计稿", "ui", "前端"],
     "native-mcp", "Figma MCP设计转代码"),
    (["chrome", "devtools", "调试网页", "浏览器"],
     "native-mcp", "Chrome DevTools MCP"),
    (["zapier", "自动化", "跨软件", "zap"],
     "native-mcp", "Zapier MCP自动化"),
    (["blender", "3d", "建模"],
     "native-mcp", "Blender MCP 3D建模"),

    # 通用
    (["计划", "plan", "方案", "设计"],
     "writing-plans", "实现计划编写"),
    (["审查", "review", "代码质量", "安全"],
     "requesting-code-review", "代码审查流程"),
    (["测试", "tdd", "pytest", "test"],
     "test-driven-development", "测试驱动开发"),
    (["脚本", "bash", "shell", ".sh"],
     "shell-scripting", "Shell脚本编写规范"),
]


def route(text: str) -> list:
    """Analyze text and return recommended skills"""
    text_lower = text.lower()
    recommendations = []

    for keywords, skill_name, reason in ROUTES:
        for kw in keywords:
            if kw.lower() in text_lower:
                recommendations.append({
                    "skill": skill_name,
                    "reason": reason,
                    "matched_keyword": kw
                })
                break  # one match per route

    # Deduplicate by skill name
    seen = set()
    unique = []
    for r in recommendations:
        if r["skill"] not in seen:
            seen.add(r["skill"])
            unique.append(r)

    return unique


def main():
    import sys

    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()

    if not text.strip():
        print(json.dumps({"skills": [], "hint": "No input text provided"}, ensure_ascii=False, indent=2))
        return

    results = route(text)

    # 限制最多推荐 5 个（避免 token 过多）
    results = results[:5]

    output = {
        "input": text[:100],
        "recommended_skills": len(results),
        "skills": results
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
