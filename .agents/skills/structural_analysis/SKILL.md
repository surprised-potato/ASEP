---
name: structural_analysis_selection
description: Modular architecture for automated structural simulation and AISC member selection, avoiding Jupyter string generation and anastruct property update bugs.
---

# Modular Structural Analysis Skill

This skill documents the preferred architecture for simulating structural systems using `anastruct` and performing automated member sizing with the AISC Shapes Database v16.0.

## Workflow Steps (MANDATORY)

### Step 0: Initial Interview
Before starting any analysis, the agent MUST interview the user to capture the following requirements. DO NOT proceed without these parameters:
1.  **Structure Type**: (e.g., Gable Frame, Mono-slope, Truss, Floor System)
2.  **Dimensions**:
    - **Span**: Total length between supports ($m$)
    - **Spacing**: Distance between frames/trusses ($m$)
    - **Height**: Column or eave height ($m$)
    - **Pitch/Slope**: Roof slope in degrees or ratio
3.  **Loading Requirements**:
    - **Gravity**: Dead/Live loads in $kPa$ or $kN/m$ (include finishes, solar panels, etc.)
    - **Wind**: Design wind speed or lateral pressure ($kPa$)
    - **Seismic**: Any specific regional requirements (if known)
4.  **Material Preferences**:
    - **Steel**: Preferred shapes (W, HSS, L, 2L, etc.) and grade.
    - **Concrete**: Support type (Pedestal, Wall, Footing type).
5.  **Soil Data** (if available): Allowable bearing capacity ($kPa$), foundation depth ($m$).
6.  **Output Requirements**:
    - Specific plots or reports required.

### Step 1: Planning...

## Key Learnings & Rules (CRITICAL)

### anastruct Gotchas

1. **Do NOT update element properties post-creation**: `anastruct` does not cleanly re-evaluate deflections when `ss.element_map[eid].EA` or `EI` are modified directly before a second `solve()`.
2. **Rebuild the system for optimization**: During iterative optimization (e.g., resizing members to meet $L/\delta$ limits), you MUST completely reconstruct the `SystemElements` instance and inject `EA` and `EI` properties directly into `ss.add_element(..., EA=..., EI=...)` at creation time.
3. **Use `add_element` for Custom Properties**: `add_truss_element` does not accept `EA` and `EI` keyword arguments in all versions! Use `add_element` combined with `spring={1: 0, 2: 0}` to simulate hinged truss connections while explicitly setting stiffness properties:
   ```python
   ss.add_element(
       location=[[x1, y1], [x2, y2]], 
       EA=area_si * E_si, 
       EI=inertia_si * E_si, 
       spring={1: 0, 2: 0} # Hinges for truss behavior
   )
   ```
4. **Node ID handling**: When extracting support reactions, `anastruct` may return `Node` objects or plain integer IDs depending on the version. Always use `nid = node.id if hasattr(node, 'id') else node` before calling `ss.get_node_results_system(nid)`.

### Parameter Passing — Avoid Hardcoding

5. **Never hardcode member family in the sizing loop.** Use `d['family']` from the `truss_groups` dict, not a literal like `family='2L'` or `family='HSS'`. This was a critical bug — the `chord_family` and `web_family` CLI arguments were ignored because the sizing functions hardcoded the family string.
6. **Never hardcode load parameters.** Compute loads from unit pressures and tributary width:
   ```python
   trib_width = 5.0       # m — parameterize this
   dl_q_kn_m = -(dl_kpa * trib_width)
   ll_q_kn_m = -(ll_kpa * trib_width)
   wind_q_kn_m = wind_kpa * trib_width
   ```
   Export `trib_width`, `dl_kpa`, `ll_kpa`, `wind_kpa` in the return dict so the report can label loads dynamically.
7. **Never hardcode report labels.** Dynamic labels must pull from the data dict:
   - Chord construction: detect from `res["Top Chord"]["Label"]` prefix (`L` → "Single Angles", `2L` → "Double Angles", etc.)
   - Web construction: detect from `res["Vertical Webs"]["Label"]` prefix (`HSS` → "Pipe", `L` → "Single Angles")
   - Load descriptions: use `trib_width`, `dl_kpa`, etc. from data dict, not literal strings like `"6m trib."`.

### Capacity Value Chain (CRITICAL BUG FIX)

8. **`check_shape()` must return `phi_Pn`.** The function computes axial capacity internally but originally returned only `(passes, ratio, klr)` — discarding the capacity. Fixed to return a 4-tuple: `(passes, ratio, klr, phi_Pn_kips)`.
   - **ALL return paths** must return 4 values, including early-return failure paths:
     ```python
     if rmin <= 0: return False, 99.0, 999, 0.0  # <-- 4th value!
     ```
9. **`select_candidates()` must store `Capacity_kN`.** Convert from kips: `capacity_kN = phi_Pn_kips * 4.44822`.
10. **RC columns use `phi_Pn_kN`** (from the column optimizer), not `Capacity_kN`. The report must fall back: `cap = shape.get('Capacity_kN') or shape.get('phi_Pn_kN', 0)`.

### Windows Console Encoding

11. **Avoid Unicode symbols in `print()` statements.** Windows cp1252 console encoding cannot render `φ`, `δ`, `×` etc. Use ASCII equivalents: `phiPn`, `delta_ns`, `x` in console output. Unicode is fine in the Markdown report (rendered by the editor/browser).

### Project Architecture

12. **Avoid massive Notebook generation**: Do not use Python scripts to generate huge strings of Python code to write to `.ipynb` files. This causes `UnicodeEncodeError`, `NameError`, and string escaping nightmares.
13. **Use a Modular CLI Approach**: The project follows a clean directory structure:

```
ASEP/
├── data/                        # Reference data (AISC xlsx)
│   └── aisc-shapes-database-v160-2.xlsx
├── src/                         # Core pipeline (Python package)
│   ├── __init__.py
│   ├── aisc_database.py         # Excel loading, AISC capacity math, width filtering
│   ├── truss_builder.py         # BAMC/Longitudinal anastruct geometry
│   ├── optimizer.py             # BAMC iterative scaling loop
│   ├── report_generator.py      # BAMC Markdown report + PNG plots
│   ├── simulate_full_system.py  # BAMC entry point
│   ├── bar_builder.py           # Bar project Howe truss geometry (21m)
│   ├── bar_optimizer.py         # Bar project iterative optimization + RC column sizing
│   ├── bar_report.py            # Bar project Markdown report generator
│   ├── run_bar.py               # Bar project CLI entry point
│   ├── bar_truss_builder.py     # Alternative bar truss builder
│   ├── bar_truss_optimizer.py   # Alternative bar optimizer
│   └── run_bar_truss.py         # Alternative bar entry point
├── output/                      # Generated artifacts (per-project)
│   ├── bar_project_singles/     # Single angle (L) variant
│   ├── Bar_Project_RC_Final/    # Double angle (2L) + HSS variant
│   └── ...                      # Other project outputs
├── gui/                         # GUI experiments
├── notebooks/                   # Jupyter notebooks
├── archive/                     # Old scripts
└── .agents/                     # Agent skills & workflows
```

14. **Imports within `src/`**: All cross-module imports MUST use relative imports (e.g., `from .optimizer import ...`, `from .aisc_database import aisc_db`).
15. **Path resolution**: Modules that need to access `data/` or `output/` directories use `_PROJECT_ROOT`:
   ```python
   import os
   _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   db_path = os.path.join(_PROJECT_ROOT, 'data', 'aisc-shapes-database-v160-2.xlsx')
   output_dir = os.path.join(_PROJECT_ROOT, 'output', project_name)
   ```

---

## Run Commands

### Bar Project (Howe Truss — Primary)
```bash
# All single angles (chords + webs)
python -m src.run_bar --project_name bar_project_singles --chord_family L --web_family L

# Double angles chords + HSS webs (original)
python -m src.run_bar --project_name Bar_Project_RC_Final --chord_family 2L --web_family HSS

# Mixed — any combination
python -m src.run_bar --project_name <name> --chord_family <L|2L|WT> --web_family <L|HSS>
```

### BAMC / Longitudinal Truss (Legacy)
```bash
python -m src.simulate_full_system <project_name>
```

---

## Load Computation & Combinations

### 1. Line Load from Area Pressure (Load Computation)
When converting area loads ($kN/m^2$ or $kPa$) to line loads ($kN/m$) for frame analysis, use the frame spacing (Tributary Width):
$$w [kN/m] = p [kPa] \times Spacing [m]$$

**Always parameterize** — store `trib_width`, `dl_kpa`, `ll_kpa`, `wind_kpa` as named variables, not magic numbers.

### 2. Standard Load Combinations (NSCP/LRFD)
Follow the National Structural Code of the Philippines (NSCP 2015) or LRFD patterns. Core combinations for steel analysis:

| ID | Combination | Usage |
| --- | --- | --- |
| **LC1** | $1.2 D + 1.6 L$ | Standard gravity |
| **LC2** | $1.2 D + 1.0 L + E$ | Gravity + Earthquake |
| **LC3** | $1.2 D + W$ | Gravity + Wind |

---

## Module Reference

### 1. Database Loading & Selection (`aisc_database.py`)

**Class**: `AISCDatabase`

Loads the Excel database (`aisc-shapes-database-v160-2.xlsx`) and provides filtering and capacity checks.

**Key capabilities:**
- **Shape types supported**: `W`, `HSS`, `L`, `WT`, `2L`
- **Capacity checks**: AISC Chapter E compression ($F_{cr}$, $\phi P_n$) and tension ($\phi P_n = 0.9 F_y A_g$)
- **Slenderness limits**: $KL/r \leq 200$ (compression), $KL/r \leq 300$ (tension)
- **Combined Interaction (AISC H1-1)**: Automatically evaluates $P/P_n + M/M_n$ interaction for combined axial and bending loads.
- **Material**: Currently enforced as A36 steel ($F_y = 36$ ksi) for all shapes.

**Key methods:**
```python
# check_shape returns 4 values: (passes, ratio, klr, phi_Pn_kips)
passes, ratio, klr, phi_Pn = aisc_db.check_shape(row, Pu_kips, L_in, Fy=36)

# Select all passing shapes, sorted lightest-first
candidates = aisc_db.select_candidates(Pu_kN, L_m, family='L', bf_max=4.0)

# Select the single lightest passing shape
shape = aisc_db.select_lightest(Pu_kN, L_m, family='WT')
```

**Return dict keys per shape:**
`Label`, `Weight` (plf), `Area` (in²), `Ix` (in⁴), `KL/r`, `Capacity_Ratio`, `Capacity_kN`, `bf_in`, `tw_in`

---

### 2. Bar Project Pipeline (`bar_builder.py` → `bar_optimizer.py` → `bar_report.py`)

**Entry point**: `run_bar.py` — CLI args: `--project_name`, `--chord_family`, `--web_family`

**Optimization sequence** (`bar_optimizer.py`):
1. **Phase 1: Iterative Member Sizing** (Factored 1.2D + 1.6L)
   - Build truss → solve → extract forces → select lightest members → repeat until convergence (max 5 iterations)
   - Chords sized with `select_lightest(family=d['family'])` — respects CLI arg
   - Webs sized with `select_lightest(family=d['family'])` for `L`; rectangular-pipe filter for `HSS`
2. **Phase 2: Deflection Check** (Service D + L)
   - If L/δ < target, step up to next heavier chord candidate
3. **Phase 3: Multi-Load-Case Analysis** (LC1 Gravity, LC2 Gravity+EQ, LC3 Gravity+Wind)
   - Governs member sizing and reactions
4. **Phase 4: RC Column Optimization** (`_optimize_rc_column()`)
   - Iterates column sizes from 200mm up in 50mm increments
   - Checks: Axial capacity (φPn ≥ Pu) AND slenderness (kLu/r ≤ 60)
   - Computes moment magnification (δns) for slender columns
   - Returns column dict with `h_mm`, `kLu_r`, `phi_Pn_kN`, `delta_ns`, `n_bars`, `bar_dia`

**Report generation** (`bar_report.py`):
- All labels are dynamic (chord type, web type, loads, column sizes, reinforcement)
- Footing sized from `qa` (soil bearing) with minimum = column width + 200mm overhang
- Foundation depth is a parameter (default 1.0m)
- Column section shows slenderness check, axial capacity check, and moment magnification

---

### 3. Geometry Creation (`truss_builder.py`) — BAMC Legacy

**Functions:**
- `build_longitudinal_truss(results_map=None)` → `(SystemElements, mapping_dict)`
- `build_transverse_stiffening_truss(transfer_load_kn, results_map=None)` → `(SystemElements, mapping_dict)`
- `build_transverse_frame()` → `SystemElements`
- `get_max_group_forces(system, ids)` → `float` (max absolute axial force in kN)

**Pattern for injecting AISC properties:**
```python
def get_props(group_name):
    r = results_map.get(group_name)
    if r:
        return float(r['Area'] * 0.00064516) * 200e9, float(r['Ix'] * 4.1623e-7) * 200e9
    return 0, 0  # defaults
```

---

## RC Column Design (NSCP/ACI 318)

### Optimization Function: `_optimize_rc_column(pu_kn, col_height_m, fc=21, fy_rebar=275)`

**Design Checks:**
1. **Axial Capacity**: $\phi P_n = 0.80 \times 0.65 \times [0.85 f'_c (A_g - A_{st}) + f_y A_{st}]$ with $A_{st} = 1\% A_g$ minimum
2. **Slenderness**: $kL_u/r \leq 60$ where $k=1.0$ (braced frame), $r = h/\sqrt{12}$
   - **Short column**: $kL_u/r \leq 34$ → no magnification needed
   - **Slender column**: $34 < kL_u/r \leq 60$ → moment magnification required
3. **Moment Magnification** ($\delta_{ns}$):
   - $E_c = 4700\sqrt{f'_c}$, $EI_{eff} = 0.4 E_c I_g / (1 + \beta_{dns})$, $\beta_{dns} = 0.6$
   - $P_c = \pi^2 EI_{eff} / (kL_u)^2$
   - $e_{min} = \max(15mm, 0.03h)$
   - $\delta_{ns} = C_m / (1 - P_u / 0.75 P_c)$

**Reinforcement Selection:**
| Column Size | Bars | Dia |
|:---|:---|:---|
| ≤ 250mm | 4 | 12mm |
| 250–350mm | 4 | 16mm |
| > 350mm | 8 | 16mm |

---

## Footing Design

**Parameters:**
- `qa`: Allowable soil bearing capacity ($kPa$) — from soil test
- `foundation_depth`: Foundation depth below grade ($m$)
- Minimum footing size = column width + 200mm (100mm overhang each side)
- Minimum footing thickness = 200mm

**Sizing:**
```python
p_service = pu / 1.5
area_req = p_service / qa
size = max(min_footing, ceil(sqrt(area_req) * 10) / 10)  # round up to 0.1m
```

---

## Standard Structural Report Outline

Every structural analysis report MUST follow this logical flow:

1.  **Truss Configuration**: Frame type, span, panels, member families, supports, steel/concrete grades.
2.  **Applied Loads**: Gravity (DL + LL with tributary width), Earthquake (NSCP static), Wind (pressure × tributary width).
3.  **Load Case Summary**: Axial forces and reactions per load case with governing envelope.
4.  **Deflection Check**: Max deflection vs L/240 target.
5.  **Optimized Member Selection**: Shape, weight, KL/r, governing force, **capacity** (kN), governing LC.
6.  **Substructure Design**: Column sizing (with slenderness check), footing sizing (with bearing pressure check).
7.  **Structural Plots**: Structure, axial forces, deflection, reactions for gravity and wind cases.

---

## Common Pitfalls & Fixes

| Problem | Root Cause | Fix |
| --- | --- | --- |
| `Capacity (kN)` column is all zeros | `check_shape()` discarded `phi_Pn`; `select_candidates()` never stored `Capacity_kN` | Return 4-tuple from `check_shape()`, store as `Capacity_kN` in candidate dict |
| Chord family CLI arg ignored | `family='2L'` hardcoded in sizing loop instead of using `d['family']` | Use `d['family']` from `truss_groups` dict |
| Web family CLI arg ignored | `family='HSS'` hardcoded in web sizing block | Branch on `d['family']`: use rect-pipe filter for `HSS`, `select_lightest` for `L` |
| Report says "6m trib" after changing to 5m | Tributary width hardcoded in report strings | Pull `trib_width`, `dl_kpa`, `ll_kpa` from data dict, format dynamically |
| Report shows "Double Angles (2L)" for single angles | Chord/web construction label hardcoded | Detect from `shape['Label']` prefix: `L` → "Single Angles", `HSS` → "Pipe" |
| `UnicodeEncodeError` with φ/δ in print() | Windows cp1252 console can't encode Greek letters | Use ASCII in `print()` (e.g., `phiPn`); Unicode is fine in Markdown output |
| `ValueError: not enough values to unpack` | Early-return paths in `check_shape()` still returned 3-tuple after adding 4th value | Update ALL return paths: `return False, 99.0, klr, 0.0` |
| Column size always 400×400 | Column not optimized — hardcoded in optimizer | Added `_optimize_rc_column()` after Phase 3 with slenderness + capacity checks |
| Footing always 1.0×1.0m | Minimum footing size hardcoded at 1.0m regardless of load | Reduced minimum to column width + 200mm overhang |
| `math domain error` in footing calc | Reaction force is negative (downward) | Use `abs()` before `math.sqrt()` |
| `TypeError` on node results | Node objects vs IDs | Use `nid = node.id if hasattr(node, 'id') else node` |
| Deflection doesn't change after re-solve | Properties set via `element_map` | Rebuild entire `SystemElements` with `add_element(EA=..., EI=...)` |
