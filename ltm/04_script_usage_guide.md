---
name: script_usage_guide
description: Guidelines for placing and documenting scripts in ../scripts directory, including usage instructions for common scripts and lifecycle for seldom-used scripts.
visible_to: ["Magi-01","LTM-Manager"]
active_for: ["Magi-01"]
---

# Script Usage Guide

1. Scripts Directory
   - Place all scripts under `../scripts/`.
   - Organize into subdirectories by category if helpful.

2. Commonly Used Scripts
   - For frequently run scripts, create a usage instruction LTM alongside:
     - Filename: `<script_name>_usage.md` in `../ltm/`.
     - Content example:
       ```markdown
       # <script_name> Usage
       **Purpose**: ...
       **Location**: `../scripts/<script_name>`
       **Usage**: ...
       **Examples**: ...
       ```
   - Keep this LTM updated with any interface changes.

3. Seldom-Used Scripts
   - Remove one-off or rarely used scripts from `../scripts/` after use.
   - Do not retain temporary scripts unless they become regularly useful.
