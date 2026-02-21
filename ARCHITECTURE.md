# Magi Agent Framework Architecture

## Overview
Magi is a multi-agent framework designed to handle user inputs, execute commands, and manage complex coding/terminal tasks using LLMs. It features a primary coordinator agent ("Magi-01") and can spawn sub-agents (like "LTM-Manager") to handle specific workflows. The framework tightly integrates with pseudo-terminal (PTY) workflows to allow agents to run interactive commands, persist state across processes, and interact with the filesystem.

## System Architecture

```mermaid
graph TD
    User([User Input via Stdin]) --> MainLoop[Main Loop (main.py)]
    MainLoop --> Coordinator[Primary Agent: Magi-01]
    MainLoop --> OtherAgents[Sub-Agents e.g. LTM-Manager]
    
    Coordinator --> LTM[Long-Term Memory Loader]
    Coordinator --> Tools[Tool System (tools.py)]
    
    Tools --> PTY[PTY Manager]
    PTY --> OS[Linux OS / Shell]
    
    OtherAgents --> Tools
    OtherAgents --> LTM
    
    LTM --> LTMFiles[(LTM Markdown Files)]
```

## Core Components

### 1. The Main Executor (`main.py`)
- Acts as the entry point of the application.
- Uses a background thread to listen to `stdin` asynchronously, queuing user input without blocking the main event loop.
- The main loop polls all registered agents. If an agent's status is `RUNNING`, it invokes their `step()` method.

### 2. The Agent Core (`magi.py`)
- Defines the `agent` class which represents an interactive AI entity.
- Handles standard features like memory accumulation (Short-Term Memory / `history`).
- Responsible for formatting prompts and calling the LLM provider (e.g., OpenAI/Azure) via `ai_request` and `ai_tool_request`.
- Implements core internal functions:
  - **Memory Management**: `summarize_history`, `compress_stm`, `remember`, `load_my_ltm`.
  - **Inter-Agent Communication**: `send_message`, `make_new_agent`, `edit_stm`.

### 3. Tool System (`tools.py`)
- Provides concrete implementations of tools the agents can call.
- Supported operations include:
  - **Filesystem**: `read_file`, `write_to_file`, `edit_file`, `ls`, `grep`.
  - **Command Execution**: Bridges to the `PTYManager` via `run_command`, `command_status`, `send_command_input`, and `list_commands`.

### 4. Pseudo-Terminal Manager (`pty_manager.py`)
- Allows robust interaction with long-running, interactive terminal commands.
- Implements `CommandManager` and `CommandSession` to spawn processes using `pty.fork()`.
- Agents can run a command asynchronously, poll its `status()`, and write to its `stdin` via `send_input()`. 
- Handles multiplexing terminal output using `select()` so the agent can continually read new output lines.

### 5. Memory Subsystem (LTM & STM)
- **Short-Term Memory (STM)**: Maintained in exactly what is sent to the LLM's context window. Continuously summarized and compressed when it exceeds configured limits (`config.MAX_STM_LENGTH`, `config.SUMMARIZE_THRESHOLD`).
- **Long-Term Memory (LTM)** (`ltm/` & `ltm_loader.py`):
  - LTMs are stored as Markdown files with YAML frontmatter.
  - Frontmatter dictates which agents process the memories via `visible_to` and `active_for` attributes.
  - Automatically loaded into an agent's context block when instantiated or explicitly active.

## Data Models (`models.py`)
Relies on Pydantic to enforce strict data structures for:
- **`AgentStep`**: Enforces Chain of Thought (`reasoning`) and standardized tool calling (`tool_name`, `tool_args`).
- **`tool`**: Represents tool capability definitions.
- **`ltm`**: Represents a parsed LTM memory struct object.

## Configuration (`config.py`)
Stores global application constants, such as token limits for memory triggering, debugging visualizers (`SHOW_THOUGHTS`, `SHOW_TOOL_CALLS`), and save paths.
