---
name: script_write_guide
description: Guide on writing and organizing scripts, including placement, usage documentation for common scripts, and deletion policy for infrequent scripts.
visible_to:
  - Magi-01
---

# Script Write Guide

1. Scripts Directory
   - Place all script files under `../scripts/` relative to the working directory.
   - Optionally organize into subdirectories by category if helpful.

2. Commonly Used Scripts
   - For scripts run frequently, create a usage instruction LTM:
     - Filename: `<script_name>_usage.md` in `../ltm/`.
     - Content template:
       ```markdown
       # <script_name> Usage
       **Purpose**: Brief description of what the script does.
       **Location**: `../scripts/<script_name>`
       **Usage**: How to run the script, including options/arguments.
       **Examples**: Sample commands.
       ```
   - Keep this LTM updated whenever the script’s interface changes.

3. Seldom-Used Scripts
   - Remove one-off or rarely used scripts from `../scripts/` after use.
   - Do not retain temporary scripts unless they become regularly useful.
   - Usage LTMs are not required for these scripts.
