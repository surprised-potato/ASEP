---
name: structural_analysis_selection
description: Modular architecture for automated structural simulation and AISC member selection, avoiding Jupyter string generation and anastruct property update bugs.
---

# Modular Structural Analysis Skill

This skill documents the preferred architecture for simulating structural systems using `anastruct` and performing automated member sizing with the AISC Shapes Database.

## Key Learnings & Rules (CRITICAL)

1. **Do NOT update element properties post-creation**: `anastruct` does not cleanly re-evaluate deflections continuously when `ss.element_map[eid].EA` or `EI` are modified directly before a second `solve()`.
2. **Rebuild the system for optimization**: During iterative optimization (e.g., resizing members to meet $L/\delta$ limits), you MUST completely reconstruct the `SystemElements` instance and inject the `EA` and `EI` properties directly into `ss.add_element(..., EA=..., EI=...)` at creation time.
3. **Use `add_element` for Custom Properties**: `add_truss_element` does not accept `EA` and `EI` keyword arguments in all versions! Use `add_element` combined with `spring={1: 0, 2: 0}` to simulate hinged truss connections while explicitly setting stiffness properties.
4. **Avoid massive Notebook generation**: Do not use Python scripts to generate huge strings of Python code to write to `.ipynb` files. This causes `UnicodeEncodeError`, `NameError`, and string escaping nightmares.
5. **Use a Modular CLI Approach**: Separate concerns into distinct Python files:
   - `aisc_database.py`: Excel loading and AISC capacity math.
   - `truss_builder.py`: Pure `anastruct` geometry definitions.
   - `optimizer.py`: The iterative scaling loop.
   - `report_generator.py`: Output generation to Markdown with inline `.png` plots.
   - `simulate_full_system.py`: A clean orchestration script.

## Procedures

### 1. Database Loading (`aisc_database.py`)
Load the Excel database (`aisc-shapes-database-v160-2.xlsx`) and build a class containing filtering and capacity checks (Slenderness limits like $KL/r \leq 200$, Tension $\phi P_n$, Compression $F_{cr}$).

### 2. Geometry Creation (`truss_builder.py`)
```python
# Correct instantiation with properties
ss.add_element(
    location=[[x1, y1], [x2, y2]], 
    EA=area_si * E_si, 
    EI=inertia_si * E_si, 
    spring={1: 0, 2: 0} # Hinges
)
```

### 3. Iterative Optimization (`optimizer.py`)
To optimize structural deflection (e.g. $L/\delta \geq 240$):
1. Build the truss with current shape properties.
2. Run `ss.solve()`.
3. Check `ss.system_displacement_vector` (max vertical displacement).
4. If it fails, select the next heaviest shapes from the AISC database based on forces.
5. **Re-call the geometry creation function** with the new shapes to build a fresh, new `SystemElements` object before the next `solve()`.

### 4. Markdown Reporting (`report_generator.py`)
Instead of a notebook, use `fig = ss.show_displacement(show=False)` to save `.png` plots locally, and write tables of selected shapes and pass/fail metrics into a cleanly formatted `.md` file.
