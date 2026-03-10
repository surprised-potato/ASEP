---
description: Onboarding for new agents to ASEP
---

Welcome to ASEP (Automated Structural Engineering Pipeline). This workflow will get you up to speed with the project's architecture and critical rules.

### 1. Read the Structural Analysis Skill
The core logic and "gotchas" for structural simulation are documented in the skill file. You MUST read this first.
- [structural_analysis/SKILL.md](file:///c:/Users/ACER/Documents/GitHub/ASEP/.agents/skills/structural_analysis/SKILL.md)

### 2. Understand the Modular Pipeline (No Notebooks)
The project has moved AWAY from Jupyter Notebooks for core logic. You MUST use the modular CLI approach to avoid `UnicodeEncodeError` and string escaping issues.
- `aisc_database.py`: Database loading and AISC capacity checks.
- `truss_builder.py`: Geometry and load definitions using `anastruct`.
- `optimizer.py`: Iterative resizing and deflection checks.
- `simulate_full_system.py`: The main entry point (Python script, not a notebook).

### 3. Review the GUIs
If you are working on the user interface, check:
- `anastruct_gui.py`: The primary PyQt6-based application.
- `app.py`: The Tkinter/OpenSeesPy alternative.

### 4. Consult Project Memory
For a quick reference of critical rules and unit conversions, refer to:
- [project_memory.md](file:///c:/Users/ACER/Documents/GitHub/ASEP/.agents/project_memory.md)
