# Magi

A multi-agent framework where LLM-powered agents collaborate to solve coding and terminal tasks. A primary coordinator agent orchestrates work and can spawn specialised sub-agents at runtime — each with independent memory, tools, and context.

## Features

- **Multi-agent collaboration** — agents communicate via message passing and can create new agents on the fly.
- **Interactive terminal** — full PTY support lets agents run, monitor, and interact with long-running shell processes.
- **Tiered memory system** — Short-Term Memory (in-process) with automatic summarisation, plus persistent Long-Term Memory stored as Markdown files with YAML frontmatter.
- **Structured reasoning** — every LLM call enforces chain-of-thought via a Pydantic schema (`AgentStep`).
- **Extensible tool surface** — filesystem operations, command execution, memory management, and inter-agent messaging out of the box.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- An Azure OpenAI deployment with the `o4-mini` model

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Kelsier64/magi.git
cd magi

# Install dependencies
uv sync

# Configure credentials
cp .env.example .env
# Edit .env with your Azure OpenAI API key and endpoint:
#   AZURE_OPENAI_API_KEY=your-key
#   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### Run the agent

```bash
uv run python main.py
```

Type in the terminal to interact with the primary agent (Magi-01). The agent will reason, call tools, and respond.

## Project Structure

```
magi/
├── main.py            # Entry point — event loop and stdin listener
├── magi.py            # Agent class, LLM integration, memory management
├── tools.py           # External tools (filesystem, command execution, search)
├── pty_manager.py     # PTY session management for interactive commands
├── models.py          # Pydantic data models (AgentStep, tool, ltm)
├── ltm_loader.py      # Long-Term Memory file parser and metadata updater
├── config.py          # Global configuration constants
│
├── ltm/               # Long-Term Memory storage (Markdown + YAML frontmatter)
├── agent_workspace/   # Sandboxed working directory for agents
├── messages_log/      # JSON dumps of conversation history
├── tests/             # Test suite
├── scripts/           # Helper scripts
└── skills/            # Agent skills (reserved)
```

> For a deep dive into how the components interact, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Configuration

All tunables live in `config.py`:

| Constant | Default | Description |
|---|---|---|
| `SHOW_THOUGHTS` | `False` | Print agent reasoning to stdout |
| `SHOW_TOOL_CALLS` | `False` | Print tool invocations to stdout |
| `USER_NAME` | `"Kelsier"` | Display name for user messages |
| `SUMMARIZE_THRESHOLD` | `30` | Message count before auto-summarisation |
| `MAX_STM_LENGTH` | `1500` | Character limit before STM compression |

## Memory System

Magi uses a two-tier memory architecture:

**Short-Term Memory (STM)** — lives in-process as a string (`stm_content`). Agents record facts with `remember()`, and the system auto-compresses when the content exceeds `MAX_STM_LENGTH`. Conversation history is summarised via LLM when it exceeds the threshold.

**Long-Term Memory (LTM)** — Markdown files in `ltm/` with YAML frontmatter controlling visibility:

```yaml
---
name: rule
description: core rules
active_for:
  - all
visible_to:
  - all
except_for:
  - LTM-Manager
---
# Memory content here
```

- `active_for` — content is injected directly into the agent's system prompt.
- `visible_to` — listed as available but not auto-loaded (can be activated on demand).
- `except_for` — explicitly excluded agents.

## Available Tools

### Agent-internal

| Tool | Description |
|---|---|
| `remember` | Save a fact to short-term memory |
| `summarize_history` | Condense conversation history |
| `active_ltm` | Activate a long-term memory |
| `compress_stm` | Deduplicate and compress STM |
| `wait` | Pause agent execution |
| `send_message` | Message a user or another agent |
| `make_new_agent` | Spawn a new agent at runtime |
| `edit_stm` | Edit another agent's STM |

### External

| Tool | Description |
|---|---|
| `run_command` | Execute a shell command (with PTY) |
| `command_status` | Check background command status |
| `send_command_input` | Send stdin / terminate a command |
| `list_commands` | List all tracked commands |
| `read_file` | Read file contents |
| `write_to_file` | Write / overwrite a file |
| `edit_file` | Replace text in a file |
| `ls` | List directory contents |
| `grep` | Search for patterns in files |

## Running Tests

```bash
uv run pytest
```

## License

This project is currently unlicensed. All rights reserved.
