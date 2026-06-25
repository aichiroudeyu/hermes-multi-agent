# Hermes Multi-Agent — Three-Agent Star Topology Orchestration

> Built by a self-taught embedded programmer who simply kept trying, kept iterating with AI.
> Orchestrator (Hermes) + Code Execution (Claude Code) + Web Search (OpenClaw).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[中文版](README_CN.md) | [English](README_EN.md)

---

## About Me

I'm a self-taught embedded firmware programmer. No CS degree, no formal training — just a passion for low-level hardware and a willingness to keep pushing AI tools to their limits. I built this three-agent collaboration system using Hermes, Claude Code, and OpenClaw, and it genuinely works for my daily firmware development.

This isn't a lab experiment. It was born from real-world Telink BLE Mesh firmware development, Dongle factory-test protocol debugging, and DALI/DMX lighting protocol learning. Every pitfall record, every boundary check rule, every orchestration strategy comes from lessons learned the hard way — debugging bugs at 2 AM and saying "never again."

**I will continue maintaining this project, iterating based on my real usage experience.**

---

## Architecture

```
                  ┌──────────────┐
                  │  Feishu/CLI   │  ← Dual entry
                  └──────┬───────┘
                         │ @Hermes sends task
                         ▼
            ┌─────────────────────────┐
            │     Hermes (Orchestrator)│
            │  Analyze → Route → Deploy│
            └──┬──────────┬────────────┘
               │          │
       Code    │          │ Search
               ▼          ▼
        ┌──────┐     ┌──────┐
        │Claude│     │Open  │
        │ Code │     │Claw  │
        │ Coder│     │Search│
        └──────┘     └──────┘
```

**Core principle**: Deploy one agent at a time. Wait for `【DONE】` before deploying the next.

---

## Why This Project Matters

- You're an embedded programmer who wants AI agents to accelerate your workflow
- You already have Claude Code / OpenClaw but don't know how they should work together
- You're interested in multi-agent systems and want a proven, battle-tested reference
- You want to see what a self-taught programmer can achieve with AI

---

## Quick Start

### Prerequisites

- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- [OpenClaw](https://github.com/openclaw/openclaw) (`npm install -g openclaw`)

### Installation

```bash
# Copy orchestrator skill
cp -r skills/hermes-orchestrator ~/.hermes/skills/autonomous-ai-agents/

# Copy backup script
cp scripts/pre-update-backup.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/pre-update-backup.sh

# Create workspace directory
mkdir -p ~/.hermes/workspace
```

---

## File Structure

```
skills/hermes-orchestrator/
├── SKILL.md                          # Core orchestration logic (283 lines)
└── references/
    ├── agent-roles.md                # Three-agent role definitions + communication protocol
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR boundary check tables
    └── pitfalls-collection.md       # Universal multi-agent pitfalls

scripts/
└── pre-update-backup.sh              # Pre-update auto-backup for agent configs
```

---

## Core Capabilities

### 1. Star-Topology Orchestration

Hermes analyzes tasks → routes to Claude Code (code work) or OpenClaw (search). Strictly serial — one agent at a time. Three-tier termination mechanism prevents infinite loops.

### 2. Boundary Cross-Validation

In embedded firmware, 70% of bugs live at module boundaries, not inside modules:

| Boundary | Check Items |
|----------|-------------|
| **UART** | Frame format, baud rate, DMA vs byte-interrupt mode |
| **Mesh** | Fragment sequence, `pending_valid` state, `data_len` calculation |
| **Flash** | MAC protection zone (0xFF000), calibration zone (0xFE000), erase granularity |
| **ISR** | Critical section protection, no printf in ISR, TXDONE byte-by-byte drain |

### 3. Anti-False-Positive Review Mode

When dispatching Claude Code for code review, attach **design decision context** (root cause + external state + test results + user decisions). Prevents design choices from being flagged as bugs.

### 4. `_workspace/` Audit Trail

Every sub-agent task input and return output is archived to `_workspace/` for post-mortem analysis.

### 5. Pre-Update Backup

`pre-update-backup.sh` auto-backs up MCP servers, permissions allowlist, and config files to `~/.hermes/backups/`. npm updates can wipe MCP definitions — backup is your safety net.

---

## Background

### Hardware

| Chip | Architecture | Protocol | Project |
|------|-------------|----------|---------|
| Telink TLSR321X | RISC-V | BLE Mesh | Serial-to-Mesh gateway |
| Telink TLSR8258 | RISC-V | BLE Mesh | Parking lot dongle |
| STM32 | ARM Cortex-M | UART/SPI/I2C | General MCU |

### Protocol Experience

- **BLE Mesh**: Provisioning, grouping, fragment reassembly, factory-test custom opcodes
- **UART Bridge**: Dual-MCU DMA/byte-interrupt mode switching, HS frame protocol
- **DALI / DMX512**: IEC 62386 standard, dimming curves, Manchester encoding

---

## Reuse Guide

### If you're also an embedded programmer

The core files `embedded-boundary-checklist.md` and `pitfalls-collection.md` can be dropped directly into your project. Just replace the chip model references.

### If you're in another domain

`agent-roles.md` and `SKILL.md` contain domain-agnostic orchestration logic. Replace the three agents with your own toolchain and you're good to go.

### If you're new to AI agents

Recommended learning path:
1. Start with Claude Code as a single agent
2. Add OpenClaw for search/research
3. Finally introduce Hermes as the orchestrator

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| One agent at a time | Avoids concurrency conflicts; results are traceable |
| Agent vs Skill separation | Agent = "who", Skill = "how" |
| `_workspace/` archiving | Post-mortem traceability of sub-agent I/O |
| Boundary checklists | 70% of embedded bugs at module boundaries |
| Trigger-rich descriptions | Skills are loaded by keyword matching; vague description = never triggered |

---

## Lineage: Methodologies Borrowed from harness

This project draws from [revfactory/harness](https://github.com/revfactory/harness):

- Agent/Skill separation principle
- Boundary cross-validation methodology
- Progressive Disclosure for skill loading
- Explicit team communication protocols

---

## Roadmap

- [ ] Expand boundary checklists for more chip platforms (ESP32, nRF52)
- [ ] Add CI/CD to auto-test orchestration correctness
- [ ] Create demo video of complete workflow
- [ ] Community contribution guide

---

## License

MIT — use it however you want.

---

## Contact

Got ideas about embedded development + AI agents? Open an issue or PR. This project was built by one self-taught programmer fumbling through AI — hope it helps you too.
