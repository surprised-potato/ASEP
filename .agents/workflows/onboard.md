---
description: Onboard to the ASEP project by loading all agent skills and project memory into context.
---

# Onboarding Workflow

Run this workflow at the start of a new conversation to load the full project context.

## Steps

// turbo-all

1. Read the **memory skill** to understand how project knowledge is organized:
   ```
   view_file .agents/skills/memory/SKILL.md
   ```

2. Read the **structural analysis skill** to load the full pipeline architecture, module reference, gotchas, and run commands:
   ```
   view_file .agents/skills/structural_analysis/SKILL.md
   ```

3. List the current project structure to confirm the workspace state:
   ```
   list_dir c:\Users\Daniel\Downloads\ASEP
   ```

4. List existing project outputs to see what analyses have been run:
   ```
   list_dir c:\Users\Daniel\Downloads\ASEP\output
   ```

5. Confirm you are ready by summarizing:
   - Project directory layout
   - Available skills loaded
   - Existing project outputs found
   - The run command: `python -m src.simulate_full_system <project_name>`
