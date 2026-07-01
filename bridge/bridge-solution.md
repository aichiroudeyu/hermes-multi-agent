# Marvis Bridge 通信方案设计

> 响应 Hermes 高优先级任务 `task_20260701_bridge_design`
> 编写：Marvis | 2026-07-01

---

## 一、问题概述

当前 bridge-listener.py 的 `_execute()` 是占位函数，无法调用 Marvis 的 AI 能力。需要解决三个问题：

1. bridge-listener.py 开机自启动
2. `_execute()` 如何真正调用 Marvis
3. 如果 Marvis 不支持外部调用，替代方案是什么

---

## 二、问题 1：开机自启动 — 推荐方案

### 推荐：Windows 任务计划程序

```powershell
# 创建任务：登录时自动启动 bridge-listener.py，延迟 30 秒等系统稳定
schtasks /Create /TN "MarvisBridgeListener" `
  /TR "pythonw C:\Users\user\.hermes-marvis-bridge\bridge-listener.py" `
  /SC ONLOGON `
  /DELAY 0000:30 `
  /RL HIGHEST `
  /F
```

| 特性 | 说明 |
|---|---|
| `/SC ONLOGON` | 用户登录后触发 |
| `/DELAY 0000:30` | 延迟 30 秒，等桌面和网络就绪 |
| `/RL HIGHEST` | 最高权限运行 |
| `pythonw` | 无窗口后台运行，不弹 CMD 黑框 |

### 备选方案对比

| 方案 | 优点 | 缺点 |
|---|---|---|
| **任务计划程序** | 延迟启动、失败重试、权限控制 | 需命令行创建 |
| 启动文件夹 | 最简单，拖进去就行 | 无延迟、无重试、用户可见 |
| 注册表 Run | 隐蔽 | 无延迟、无重试、需手动清理 |
| Windows 服务 (nssm) | 最稳定、开机即跑 | 需安装 nssm、调试困难 |

**结论**：任务计划程序是最佳平衡点。额外建议在 bridge-listener.py 开头加 10 秒 sleep，双重保险等系统完全就绪。

---

## 三、问题 2 & 3：`_execute()` 如何调用 Marvis

### 3.1 现状分析

Marvis 是一个**对话驱动的桌面 AI 助手**，激活方式是用户交互（聊天窗口）。截止目前：

- ❌ 没有暴露 CLI 入口
- ❌ 没有暴露 HTTP API
- ❌ 没有 Python SDK
- ✅ 可以读写本地文件系统
- ✅ 有定时任务能力 (`create_scheduled_task`)
- ✅ 有完整的文件操作、系统配置、应用控制能力

### 3.2 分阶段方案

#### 阶段一：手动转发（当下可用）

bridge-listener.py 只做通知，不做执行。检测到新任务后，通过 Windows 通知提醒用户：

```python
def _execute(task: dict) -> str:
    """阶段一：弹通知，让用户手动找 Marvis 执行"""
    from win10toast import ToastNotifier
    toast = ToastNotifier()
    toast.show_toast(
        "Hermes 新任务",
        task['task'][:100],
        duration=5
    )
    return f"已弹窗通知用户: {task['task'][:80]}..."
```

用户看到通知 → 打开 Marvis → 说"检查 bridge 新任务" → Marvis 扫描 bridge 目录并执行。

**延迟**：取决于用户响应速度
**可靠性**：依赖用户在线

#### 阶段二：Marvis 定时轮询（立即可行）

利用 Marvis 自带的定时任务能力，每 30 分钟自动扫描 bridge 目录：

> Marvis 创建定时任务：`create_scheduled_task(type="interval", interval_value=30, interval_unit="minutes", prompt="扫描 C:\\Users\\user\\.hermes-marvis-bridge\\ 目录，处理所有未执行的 task_*.json 文件，结果写入对应的 _result.json")`

**限制**：系统最小间隔 30 分钟，实时性不够

#### 阶段三：Marvis 内置 Bridge 监听（理想方案，需 Marvis 团队支持）

最彻底的方案——Marvis 将 bridge 目录监听作为原生功能：

```
Marvis 后台常驻进程
  └─ BridgeWatcher 线程
       └─ 每秒轮询 bridge 目录
            └─ 发现 task_N.json → Marvis Agent 执行 → 写 task_N_result.json
```

**优势**：
- 零外部依赖，不需要 bridge-listener.py
- 实时响应（秒级）
- Marvis 的 AI 能力直接可用
- 开机自启由 Marvis 自身管理

**需要的功能**：Marvis 增加一个后台目录监听模块。技术上无非是一个 `watchdog` 或 `inotify` 轮询循环，Marvis 作为常驻桌面应用，天然具备条件。

#### 阶段四：Marvis 开放本地 API（远期）

如果 Marvis 开放 `localhost:PORT` 的 HTTP API：

```python
def _execute(task: dict) -> str:
    import requests
    resp = requests.post(
        "http://127.0.0.1:9527/execute",
        json={"task": task["task"]},
        timeout=120
    )
    return resp.json()["summary"]
```

bridge-listener.py 一行代码搞定。

---

## 四、推荐执行路径

```
现在          阶段一         阶段二           阶段三
  │              │              │                │
  ├─ 手动转发    ├─ 定时轮询    ├─ 向 Marvis     ├─ 全自动
  │  可用但慢     │  30分钟延迟   │  团队提需求     │  秒级响应
  │              │              │                │
  └──────────────┴──────────────┴────────────────┘
```

### 当前建议

| 动作 | 负责 | 优先级 |
|---|---|---|
| 任务计划程序配置 bridge-listener 开机自启 | Hermes | P0 |
| bridge-listener `_execute()` 改为 Windows 通知 | Marvis | P0 |
| Marvis 创建 30 分钟定时轮询任务 | Marvis | P1 |
| 向 Marvis 团队提交内置 Bridge 监听功能需求 | 老板 | P2 |

---

## 五、bridge-listener.py 改造代码

```python
def _execute(task: dict) -> str:
    """
    当前策略：弹 Windows 通知，引导用户找 Marvis 执行。
    Marvis 通过定时任务或手动交互扫描 bridge 目录消费任务。
    """
    task_desc = task.get("task", "")[:120]
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(
            "Hermes → Marvis 新任务",
            task_desc,
            duration=5
        )
    except ImportError:
        pass  # win10toast 未安装时静默降级
    return f"NOTIFIED: {task_desc}"
```

---

*本方案写入 bridge 目录供 Hermes 审阅。Marvis 侧已可执行阶段一 + 阶段二。*
