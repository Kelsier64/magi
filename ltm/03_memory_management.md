---
name: memory management
description: how to manage memory
active_for: 
- all
visible_to: 
- all
except_for:
- LTM-Manager
---
# Memory Management

1. **Retaining Information**: Use the `remember(text)` tool to proactively record brief notes about important facts, environmental variables, errors found, or specific constraints. Do not use this to summarize entire dialogues. 
2. **Managing Context**: When the session becomes too long or you have completed a major task step, use `summarize_history()` to clear the chat buffer. The system will automatically construct an intelligent summary of your actions and save it into your short-term memory while retaining your immediate context train of thought. Do not try to clean the history manually.

3. **Permanent Storage (LTM)**: If you synthesize a highly critical fact or standard that must be remembered permanently, contact `LTM-Manager` via the `send_message` tool. 
    your ltm is in ../ltm/
    - You can ask `LTM-Manager` to **search** for information in your Long-Term Memory.
    - You can ask `LTM-Manager` to **edit** or **remove** or **create** memories.