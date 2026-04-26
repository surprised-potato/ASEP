---
description: Onboarding for new agents to ASEP
---

Welcome to ASEP (Automated Structural Engineering Pipeline). This workflow will get you up to speed with the project's architecture and critical rules.

### 1. Read the Structural Analysis Skill
The core logic and "gotchas" for structural simulation are documented in the skill file. You MUST read this first.
- `.agents/skills/structural_analysis/SKILL.md`

### 2. Understand the Modular Pipeline (No Notebooks)
The project has moved AWAY from Jupyter Notebooks for core logic. You MUST use the modular CLI approach to avoid `UnicodeEncodeError` and string escaping issues.

**Bar Project Pipeline** (primary, actively maintained):
- `bar_builder.py`: Howe truss geometry (21m span, level bottom chord, Isosceles triangle)
- `bar_optimizer.py`: Iterative sizing, deflection check, multi-load-case, RC column optimization
- `bar_report.py`: Dynamic Markdown report with slenderness checks and footing design
- `run_bar.py`: CLI entry point — `python -m src.run_bar --project_name <name> --chord_family <L|2L> --web_family <L|HSS>`

**BAMC/Legacy Pipeline**:
- `aisc_database.py`: Database loading and AISC capacity checks.
- `truss_builder.py`: Geometry and load definitions using `anastruct`.
- `optimizer.py`: Iterative resizing and deflection checks.
- `simulate_full_system.py`: Entry point — `python -m src.simulate_full_system <project_name>`

### 3. Key Rules
- **Parameterize everything**: Loads, tributary width, soil bearing, column sizes — never hardcode.
- **All return paths must match**: If a function returns N values, ALL code paths (including early returns) must return N values.
- **ASCII in print(), Unicode in Markdown**: Windows cp1252 console can't render Greek letters.
- **Rebuild, don't mutate**: Modify member properties by rebuilding the anastruct system, not patching `element_map`.

### 4. Consult Project Memory
For how skills and memory are managed:
- `.agents/skills/memory/SKILL.md`
