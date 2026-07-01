#!/usr/bin/env python3
"""
Hermes Agent 审计日志系统
写入 ~/.hermes/workspace/audit-log.jsonl，每行一条委派记录。

用法:
  echo '{"agent":"claude-code","task":"审查 Dongle UART","duration_s":45,"status":"DONE","tokens_est":12000,"cost_est":0.15}' | python3 audit-log.py

  python3 audit-log.py --query "claude-code"          # 查所有 Claude Code 委派记录
  python3 audit-log.py --stats                          # 统计摘要
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / ".hermes" / "workspace" / "audit-log.jsonl"


def ensure_log():
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("")
    return LOG_FILE


def append(entry: dict) -> None:
    """追加一条委派记录"""
    ensure_log()
    entry.setdefault("timestamp", datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def query(agent: str = None, limit: int = 20) -> list:
    """查询最近的委派记录，可按 agent 过滤"""
    if not LOG_FILE.exists():
        return []
    results = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if agent and entry.get("agent") != agent:
                continue
            results.append(entry)
    return results[-limit:]


def stats() -> dict:
    """统计摘要"""
    total = 0
    by_agent = {}
    total_cost = 0.0
    total_duration = 0

    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total += 1
                agent = entry.get("agent", "unknown")
                by_agent[agent] = by_agent.get(agent, 0) + 1
                total_cost += entry.get("cost_est", 0)
                total_duration += entry.get("duration_s", 0)

    return {
        "total_delegations": total,
        "by_agent": by_agent,
        "total_cost_usd": round(total_cost, 4),
        "total_duration_s": total_duration,
        "avg_duration_s": round(total_duration / total, 1) if total > 0 else 0,
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--query":
        agent = sys.argv[2] if len(sys.argv) > 2 else None
        for entry in query(agent):
            print(json.dumps(entry, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "--stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=2))
    else:
        # stdin mode: 从管道读 JSON
        raw = sys.stdin.read().strip()
        if raw:
            try:
                entry = json.loads(raw)
                append(entry)
                print(f"OK {entry.get('agent')} {entry.get('status')}")
            except json.JSONDecodeError as e:
                print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
