# Hermes Multi-Agent — Three-Agent Star Topology Orchestration

> Built by a self-taught embedded programmer who simply kept trying, kept iterating with AI.
> Orchestrator (Hermes) + Code Execution (Claude Code) + Web Search (OpenClaw).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[中文版](README_CN.md) | [English](README_EN.md)

---

## About Me

I'm a self-taught embedded firmware programmer. No CS degree, no formal training — just a passion for low-level hardware and a willingness to keep pushing AI tools to their limits. I built this three-agent collaboration system using Hermes, Claude Code, and OpenClaw, and it genuinely works for my daily firmware development.

This isn't a lab experiment. It was born from real-world Telink BLE Mesh firmware development, Dongle factory-test protocol debugging, and DALI/DMX lighting protocol learning. Every pitfall record, every boundary check rule, every orchestration strategy comes from lessons learned the hard way — debugging bugs at 2 AM and saying "never again."

**Actively maintained and iterated based on real usage experience.**

---

## v2.0 Update (July 2026)

One month of self-evolution since v1.0:

| Addition | Description |
|----------|-------------|
| **SOUL.md** | Agent identity file — defines "who I am, what I can do, my iron rules." Injected on every startup, immutable |
| **Three-Layer Memory** | Memory (facts) + Wiki (knowledge) + Skills (workflows) — hierarchical persistent storage |
| **Loop Auto-Closure Mode** | Set goal + acceptance criteria → auto loop: write code → compile/test → retry with failure context → report |
| **Auto Skill Loading** | `skill-router.py` matches keywords from user input and auto-loads relevant skills |
| **MCP Server Ecosystem** | CodeGraph (code relationship indexing), Agent-Reach (domestic platform search) — pluggable agent toolchain |
| **Anti-False-Positive Review** | Dispatch Claude Code reviews with full design decision context to prevent design choices flagged as bugs |
| `_workspace/` Audit Trail | Every sub-agent task input/output is persisted for full post-mortem traceability |
| **Pre-Update Backup** | `pre-update-backup.sh` auto-backs up MCP server definitions and permissions allowlists |
| **Cross-PC Sync Safety** | No API keys, local IPs, or port numbers in sync packages — only pure knowledge and tools |

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
            │  Auto Skill Routing     │
            │  Memory / Wiki / Skills │
            │  SOUL.md constraints    │
            │  Analyze → Route → Deploy│
            └──┬──────────┬────────────┘
               │          │
       Code    │          │ Search
               ▼          ▼
        ┌──────┐     ┌──────┐
        │Claude│     │Open  │
        │ Code │     │Claw  │
        │ Coder│     │Search│
        │5 MCP │     │SearX │
        └──────┘     └──────┘
```

**Core principle**: Deploy one agent at a time. Wait for `【DONE】` before deploying the next.

---

## Why This Project Matters

- You're an embedded programmer who wants AI agents to accelerate your workflow
- You already have Claude Code / OpenClaw but don't know how they should work together
- You're interested in multi-agent systems and want a proven, battle-tested reference
- You want to see what a self-taught programmer can achieve with AI
- You want to learn how to give agents persistent "memory" and "soul"

---

## File Structure

```
skills/hermes-orchestrator/
├── SKILL.md                          # Core orchestration logic (v6.1)
└── references/
    ├── agent-roles.md                # Three-agent role definitions + communication protocol
    ├── embedded-boundary-checklist.md # UART/Mesh/Flash/ISR boundary check tables
    └── pitfalls-collection.md       # Universal multi-agent pitfalls

scripts/
├── pre-update-backup.sh              # Pre-update auto-backup for agent configs
├── skill-router.py                   # Auto skill loader (156 lines)
├── hermes_loop.py                    # Loop mode scheduler (326 lines)
├── weekly-report.py                  # Weekly report auto-generator
├── memory-archive.py                 # Memory archival and cleanup
└── memory-health-check.py            # Memory health monitoring

docs/
├── pitfalls-and-fixes.md             # Post-update issue log (13 items)
└── architecture-evolution.md         # From zero to v2.0 — the evolution journey
```

---

## Core Capabilities

### 1. Star-Topology Orchestration + Auto Routing

Hermes analyzes tasks → `skill-router.py` auto-matches skills by keywords → routes to Claude Code (code/review) or OpenClaw (search/research). Strictly serial — one agent at a time. Three-tier termination mechanism prevents infinite loops.

### 2. Loop Auto-Closure

```bash
python3 hermes_loop.py --goal "Write TCP echo server in Python" \
  --acceptance "①Listen on 8888 ②Echo text back ③Ctrl+C to exit" --max-loops 5
```

Set a goal and acceptance criteria → auto loop: dispatch Claude Code → judge compiles+tests automatically → retry with failure context if failed → report when passed. ~$0.20 per loop.

### 3. Three-Layer Memory System

| Layer | Stores | Example |
|-------|--------|---------|
| **Memory** | User preferences / environment facts / lessons | "No printf in ISR", "Dongle 50ms delay is client constraint" |
| **Wiki** | Structured knowledge base (12 files) | BLE Mesh provisioning flow, TLSR321X Flash layout |
| **Skills** | Executable workflow templates (162 skills) | MCU firmware dev rules, DALI protocol reference, UART ISR templates |

### 4. Boundary Cross-Validation

In embedded firmware, 70% of bugs live at module boundaries, not inside modules:

| Boundary | Check Items |
|----------|-------------|
| **UART** | Frame format consistency, baud rate, DMA vs byte-interrupt, TXDONE drain |
| **Mesh** | Fragment sequence, `pending_valid` state, `data_len` off-by-1, Opcode conflicts |
| **Flash** | MAC protection zone (0xFF000), calibration zone (0xFE000), 4KB erase granularity |
| **ISR** | Critical section protection, no printf in ISR, `uart_set_irq_mask` overwrite trap |

### 5. SOUL.md Behavioral Constraints

Each agent has an immutable "soul file" — defining identity, capability boundaries, and iron rules. This solves the problem of agent behavior drift in long-running sessions.

### 6. Anti-False-Positive Review Mode

When dispatching Claude Code for code review, attach **full design decision context**:
- Why this approach (protocol constraints, client requirements, hardware limits)
- External state (other boards' behavior, host-side expected format)
- Test results (serial monitor hex dumps)
- User-confirmed design choices

Prevents AI from flagging design decisions as bugs.

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

# Copy utility scripts
cp scripts/skill-router.py ~/.hermes/scripts/
cp scripts/hermes_loop.py ~/.hermes/scripts/
cp scripts/weekly-report.py ~/.hermes/scripts/
cp scripts/memory-archive.py ~/.hermes/scripts/
cp scripts/memory-health-check.py ~/.hermes/scripts/
cp scripts/pre-update-backup.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/pre-update-backup.sh

# Create workspace directory
mkdir -p ~/.hermes/workspace
```

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

`skill-router.py` and `hermes_loop.py` have zero embedded dependencies — usable by any language/domain agent setup.

### If you're in another domain

`agent-roles.md` and `SKILL.md` contain domain-agnostic orchestration logic. Replace the three agents with your own toolchain and you're good to go.

The **three-layer memory system** (Memory→Wiki→Skills) is a domain-agnostic agent knowledge management solution.

### If you're new to AI agents

Recommended learning path:
1. Start with Claude Code as a single agent
2. Add OpenClaw for search/research
3. Introduce Hermes as the orchestrator
4. Configure SOUL.md + three-layer memory to stabilize agent behavior
5. Use Loop mode for autonomous trial-and-error

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| One agent at a time | Avoids concurrency conflicts; results are traceable |
| Agent vs Skill separation | Agent = "who", Skill = "how" |
| `_workspace/` archiving | Post-mortem traceability of sub-agent I/O |
| Boundary checklists | 70% of embedded bugs at module boundaries |
| Trigger-rich descriptions | Vague description = skill never auto-loaded |
| SOUL.md iron rules | Immutable constraints prevent behavior drift over long runs |
| Cross-PC sync excludes config | Prevents API key leakage through sync packages |
| Backup MCP allowlists before update | npm update can wipe MCP server definitions |

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
