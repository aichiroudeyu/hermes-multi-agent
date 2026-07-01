#!/usr/bin/env python3
"""
Marvis Bridge 监听器 v2
轮询桥接目录，发现新任务 → 弹 Windows 通知提醒用户找 Marvis 执行。

运行: pythonw bridge-listener.py   (后台无窗口)
"""

import os
import json
import time
import traceback

BRIDGE = r"C:\Users\user\.hermes-marvis-bridge"
POLL_INTERVAL = 2  # 轮询间隔（秒）


def notify(title: str, msg: str) -> None:
    """Windows 原生通知（winotify，Python 3.12+ 兼容）"""
    try:
        from winotify import Notification
        Notification(app_id="Hermes Bridge", title=title, msg=msg[:120]).show()
    except ImportError:
        pass


def process_task(task_file: str) -> None:
    task_path = os.path.join(BRIDGE, task_file)
    processing_path = task_path.replace(".json", "_processing.json")

    try:
        with open(task_path, "r", encoding="utf-8") as f:
            task = json.load(f)
    except Exception:
        return

    # 标记处理中
    os.rename(task_path, processing_path)
    task_id = task.get("task_id", task_file)
    task_desc = task.get("task", "")[:100]

    print(f"[TASK] {task_id}: {task_desc}")
    notify("Hermes → Marvis 新任务", f"{task_id}\n{task_desc}")


def main():
    os.makedirs(BRIDGE, exist_ok=True)
    print(f"[LISTEN] {BRIDGE}  |  间隔 {POLL_INTERVAL}s  |  等待 Hermes...")

    while True:
        try:
            tasks = sorted([
                f for f in os.listdir(BRIDGE)
                if f.startswith("task_")
                and f.endswith(".json")
                and "_result" not in f
                and "_processing" not in f
            ])
            for task_file in tasks:
                process_task(task_file)
        except Exception:
            traceback.print_exc()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
