---
name: ltm architecture
description: how to write ltm
active_for: 
- all
visible_to: 
- all
---
LTMs( Long-Term Memories) is agent's memory in markdown files.

# LTM Architecture :
- **Language**: The content of the memory MUST be written mainly in **English**.
- **Format**: All Long-Term Memories (LTMs) MUST be written as Markdown (`.md`) files.
- **Metadata**: Every LTM file MUST begin with a YAML frontmatter block containing `name`, `description`(short description including purpose and when to load), and `visible_to` (list of agents for discoverability). The `active_for` property (list of agents for automatic loading MUST only be used when defining agents' core rules). Do NOT add any other properties.
- **location**: All LTM files are stored in the `../ltm/` directory.
- **priority**: LTMs are loaded in the order of their names alphabetically.however you dont have to add number in front of the name.
