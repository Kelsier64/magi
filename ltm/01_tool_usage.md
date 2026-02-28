---
name: tool usage
description: how to use tools
active_for: 
- all
visible_to: 
- all
---

# Tool Usage

To use a tool, you MUST output a valid JSON object matching the `AgentStep` schema.
1. `reasoning`: Explain YOUR THINKING PROCESS in first person perspective. Why are you taking this step? What do you expect to see?
2. `tool_name`: The exact name of the tool to call.
3. `tool_args`: The parameters for the tool.

- Your output and actions will be recorded in your memory from a first-person perspective, use the 'send_message' tool to communicate with other agents or users.
- If you have completed the task or cannot proceed, use the `wait` tool.