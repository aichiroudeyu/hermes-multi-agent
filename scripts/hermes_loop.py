#!/usr/bin/env python3
"""
Hermes Loop 调度器 — AI 自主试错闭环

用法:
  python3 hermes_loop.py \
    --goal "用 Python 写 TCP echo server" \
    --acceptance "①监听8888 ②回显文本 ③Ctrl+C退出" \
    --max-loops 5 \
    --workdir /tmp/loop-test

Hermes 会在每轮调用 Claude Code → 编译/测试 → 不通过就带失败信息重派 → 通过则汇报。
"""

import argparse
import shlex
import subprocess
import sys
import os
import json
import time
import re
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────
# 配置
# ──────────────────────────────────────────

CLAUDE_CMD = "claude"
DEFAULT_MAX_LOOPS = 5
DEFAULT_TIMEOUT = 300  # 单轮超时（秒）
COST_PER_LOOP_ESTIMATE = 0.15  # USD
COST_PER_REVIEW_ESTIMATE = 0.05

# ──────────────────────────────────────────
# 裁判函数
# ──────────────────────────────────────────

def judge(workdir: str, acceptance: str) -> dict:
    """
    裁判审查：自动编译+测试，返回结论。
    结论格式: {"pass": True/False, "build": "...", "test": "...", "reason": "...", "suggestion": "..."}
    """
    result = {"pass": True, "build": "", "test": "", "reason": "", "suggestion": ""}

    # ── 检测项目类型 ──
    files = os.listdir(workdir)
    is_c = any(f.endswith(".c") or f.endswith(".h") for f in files)
    is_python = any(f.endswith(".py") for f in files)
    is_rust = any(f.endswith(".rs") for f in files) or os.path.exists(f"{workdir}/Cargo.toml")
    has_makefile = os.path.exists(f"{workdir}/Makefile")

    # ── 编译 ──
    build_output = ""
    if is_c:
        # C 项目：尝试 gcc 编译所有 .c 文件
        build_r = subprocess.run(
            f"cd {workdir} && gcc -Wall -Wextra -o /tmp/hermes_loop_bin *.c 2>&1",
            shell=True, capture_output=True, text=True, timeout=60
        )
        build_output = build_r.stdout + build_r.stderr
        if build_r.returncode != 0:
            result["pass"] = False
            result["build"] = f"❌ 编译失败:\n{build_output[-500:]}"
            result["reason"] = "编译失败"
            result["suggestion"] = f"修复编译错误:\n{build_output[-300:]}"
            return result
        else:
            result["build"] = "✅ 编译通过"

            # 尝试运行
            run_r = subprocess.run(
                f"cd {workdir} && timeout 5 /tmp/hermes_loop_bin 2>&1; echo 'EXIT_CODE:'$?",
                shell=True, capture_output=True, text=True, timeout=10
            )
            result["test"] = run_r.stdout[:500]

    elif is_python:
        # Python 项目：语法检查
        for f in files:
            if f.endswith(".py"):
                py_r = subprocess.run(
                    f"cd {workdir} && python3 -m py_compile {f} 2>&1",
                    shell=True, capture_output=True, text=True, timeout=30
                )
                if py_r.returncode != 0:
                    result["pass"] = False
                    result["build"] = f"❌ 语法错误 ({f}):\n{py_r.stderr[-300:]}"
                    result["reason"] = f"Python 语法错误: {f}"
                    result["suggestion"] = f"修复 {f} 的语法错误"
                    return result
        result["build"] = "✅ 语法检查通过"

        # 尝试运行 pytest（如果存在）
        test_files = [f for f in files if f.startswith("test_") and f.endswith(".py")]
        if test_files:
            test_r = subprocess.run(
                f"cd {workdir} && python3 -m pytest -v --tb=short 2>&1",
                shell=True, capture_output=True, text=True, timeout=60
            )
            result["test"] = test_r.stdout[-500:] + test_r.stderr[-500:]
            if test_r.returncode != 0:
                result["pass"] = False
                result["reason"] = "测试失败"
                # 提取失败信息
                fail_lines = [l for l in test_r.stdout.split("\n") if "FAIL" in l or "Error" in l or "assert" in l]
                result["suggestion"] = "\n".join(fail_lines[-5:])
                return result
        else:
            # 无测试文件，直接运行主文件
            main_files = [f for f in files if f.endswith(".py") and not f.startswith("test_")]
            if main_files:
                run_r = subprocess.run(
                    f"cd {workdir} && timeout 10 python3 {main_files[0]} 2>&1; echo 'EXIT_CODE:'$?",
                    shell=True, capture_output=True, text=True, timeout=15
                )
                result["test"] = run_r.stdout[:500]
                if "Traceback" in run_r.stdout or run_r.stderr:
                    result["pass"] = False
                    result["reason"] = "运行时错误"
                    result["suggestion"] = run_r.stdout[-300:] + run_r.stderr[-300:]
                    return result
        result["test"] = "✅ 运行正常"

    elif is_rust:
        build_r = subprocess.run(
            f"cd {workdir} && cargo build 2>&1",
            shell=True, capture_output=True, text=True, timeout=120
        )
        build_output = build_r.stdout + build_r.stderr
        if build_r.returncode != 0:
            result["pass"] = False
            result["build"] = f"❌ cargo build 失败:\n{build_output[-500:]}"
            result["reason"] = "编译失败"
            result["suggestion"] = build_output[-300:]
            return result
        result["build"] = "✅ cargo build 通过"
        # cargo test
        test_r = subprocess.run(
            f"cd {workdir} && cargo test 2>&1",
            shell=True, capture_output=True, text=True, timeout=60
        )
        result["test"] = test_r.stdout[-500:] + test_r.stderr[-500:]
        if test_r.returncode != 0:
            result["pass"] = False
            result["reason"] = "cargo test 失败"
            result["suggestion"] = result["test"][-300:]
            return result

    elif has_makefile:
        build_r = subprocess.run(
            f"cd {workdir} && make 2>&1",
            shell=True, capture_output=True, text=True, timeout=60
        )
        build_output = build_r.stdout + build_r.stderr
        if build_r.returncode != 0:
            result["pass"] = False
            result["build"] = f"❌ make 失败:\n{build_output[-500:]}"
            result["reason"] = "make 编译失败"
            result["suggestion"] = build_output[-300:]
            return result
        result["build"] = "✅ make 通过"

    else:
        result["build"] = "ℹ️ 未检测到标准项目类型，跳过自动编译"

    # ── 与验收标准对照 ──
    # (基础版：列出验收项提示用户检查)
    acceptance_items = [a.strip() for a in acceptance.replace("①", "\n①").replace("②", "\n②").replace("③", "\n③").split("\n") if a.strip()]
    result["acceptance_check"] = f"请人工确认以下验收标准是否满足:\n" + "\n".join(f"  [{i+1}] {item}" for i, item in enumerate(acceptance_items) if item)

    return result


def call_claude(goal: str, workdir: str, lessons: str, acceptance: str, timeout: int) -> dict:
    """
    调用 Claude Code 执行任务。返回 {"output": "...", "success": bool}
    """
    # 构造 context
    prompt = f"""完成任务后只输出结果，末尾加【DONE】，不要继续对话。

## 任务
{goal}

## 验收标准
{acceptance}

## 工作目录
{workdir}

## 指令
- 所有代码文件写入 {workdir}
- 写完后自行编译/语法检查验证
- 如果验收标准中有测试要求，请一并写好测试代码
- 末尾输出【DONE】
"""
    if lessons:
        prompt += f"\n## 上一轮失败教训（请避免重复）\n{lessons}\n"

    cmd = (
        f"cd {workdir} && {CLAUDE_CMD} -p {shlex.quote(prompt)} "
        f"--add-dir {workdir} "
        f"--max-turns 8 "
        f"--permission-mode bypassPermissions "
        f"--output-format text "
        f"--model deepseek/deepseek-chat"
    )

    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        output = r.stdout + r.stderr
        success = "【DONE】" in output and r.returncode == 0
        return {"output": output, "success": success}
    except subprocess.TimeoutExpired:
        return {"output": f"⏱ Claude Code 超时 ({timeout}s)", "success": False}
    except Exception as e:
        return {"output": str(e), "success": False}


# ──────────────────────────────────────────
# 主循环
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Hermes Loop 调度器")
    parser.add_argument("--goal", required=True, help="任务目标")
    parser.add_argument("--acceptance", required=True, help="验收标准（如 ①编译通过 ②测试全绿）")
    parser.add_argument("--max-loops", type=int, default=DEFAULT_MAX_LOOPS, help=f"最大循环轮次 (默认 {DEFAULT_MAX_LOOPS})")
    parser.add_argument("--workdir", default="/tmp/hermes-loop", help="工作目录")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"单轮超时秒数 (默认 {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    os.makedirs(args.workdir, exist_ok=True)

    failures = []  # 失败教训

    print("=" * 60)
    print(f"🌀 Hermes Loop 启动")
    print(f"  目标: {args.goal}")
    print(f"  验收: {args.acceptance}")
    print(f"  上限: {args.max_loops} 轮")
    print(f"  目录: {args.workdir}")
    print("=" * 60)

    total_cost = 0.0

    for loop_num in range(1, args.max_loops + 1):
        print(f"\n{'─' * 60}")
        print(f"🔄 第 {loop_num}/{args.max_loops} 轮")
        print(f"{'─' * 60}")

        # 注入教训
        lessons = ""
        if failures:
            lessons = "\n".join(f"  - {f}" for f in failures)
            print(f"📝 注入教训 ({len(failures)} 条):")
            for f in failures:
                print(f"  ❌ {f}")

        # ── 步骤 1: 委派 Claude Code ──
        print(f"🚀 委派 Claude Code...")
        claude_result = call_claude(args.goal, args.workdir, lessons, args.acceptance, args.timeout)
        total_cost += COST_PER_LOOP_ESTIMATE
        print(f"💰 累计成本: ${total_cost:.2f}")

        if not claude_result["success"]:
            print(f"❌ Claude Code 调用失败")
            print(claude_result["output"][-300:])
            failures.append(f"第{loop_num}轮: Claude Code 调用失败或未输出【DONE】")
            continue

        # ── 步骤 2: 裁判审查 ──
        print(f"🔍 裁判审查...")
        judgement = judge(args.workdir, args.acceptance)
        total_cost += COST_PER_REVIEW_ESTIMATE

        print(f"  build: {judgement['build'][:100]}")
        if judgement.get("test"):
            print(f"  test: {judgement['test'][:200]}")

        if judgement["pass"]:
            print(f"\n{'=' * 60}")
            print(f"✅ Loop 通过！第 {loop_num} 轮完成")
            print(f"{'=' * 60}")
            print(f"总成本: ${total_cost:.2f}")
            print(f"\n最终文件 ({args.workdir}):")
            for f in sorted(os.listdir(args.workdir)):
                fpath = os.path.join(args.workdir, f)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath)
                    print(f"  {f} ({size}B)")
            print(f"\n裁判结果:")
            print(f"  编译: {judgement['build']}")
            print(f"  测试: {judgement.get('test', 'N/A')}")
            print(judgement.get("acceptance_check", ""))
            print(f"\n【任务结束】")
            return 0

        # ── 不通过 ──
        reason = judgement.get("reason", "未知原因")
        suggestion = judgement.get("suggestion", "")
        print(f"❌ 不通过: {reason}")
        if suggestion:
            print(f"💡 建议: {suggestion[:200]}")

        failure_entry = f"第{loop_num}轮: {reason}"
        if suggestion:
            failure_entry += f" ({suggestion[:100]})"
        failures.append(failure_entry)

    # ── 超出上限 ──
    print(f"\n{'=' * 60}")
    print(f"❌ Loop 失败 — 达到上限 {args.max_loops} 轮")
    print(f"{'=' * 60}")
    print(f"总成本: ${total_cost:.2f}")
    print(f"\n失败教训 ({len(failures)} 条):")
    for f in failures:
        print(f"  {f}")
    print(f"\n当前工作文件: {args.workdir}")
    print(f"【任务结束】")
    return 1


if __name__ == "__main__":
    sys.exit(main())
