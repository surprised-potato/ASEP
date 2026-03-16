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
    - **Steel**: Preferred shapes (W, HSS, L, etc.) and grade.
    - **Concrete**: Support type (Pedestal, Wall, Footing type).
5.  **Output Requirements**:
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

### Project Architecture

5. **Avoid massive Notebook generation**: Do not use Python scripts to generate huge strings of Python code to write to `.ipynb` files. This causes `UnicodeEncodeError`, `NameError`, and string escaping nightmares.
6. **Use a Modular CLI Approach**: Separate concerns into distinct Python files:
   - `aisc_database.py`: Excel loading, AISC capacity math, geometric width filtering.
   - `truss_builder.py`: Pure `anastruct` geometry definitions and load application.
   - `optimizer.py`: The iterative scaling loop with geometric constraints.
   - `report_generator.py`: Output generation to Markdown with inline `.png` plots.
   - `simulate_full_system.py`: A clean orchestration script.

### Unit Conversion Constants (Imperial ↔ SI)

These are used frequently in the codebase:

| Conversion | Factor | Usage |
| --- | --- | --- |
| Area: in² → m² | `× 0.00064516` | `EA = Area_in2 * 0.00064516 * 200e9` |
| Inertia: in⁴ → m⁴ | `× 4.1623e-7` | `EI = Ix_in4 * 4.1623e-7 * 200e9` |
| Force: kN → kips | `× 0.224809` | AISC checks use kips |
| Length: m → in | `× 39.3701` | AISC checks use inches |
| Weight: plf (lb/ft) → kg/m | `× 1.488` | For mass estimation |

---

## Load Computation & Combinations

### 1. Line Load from Area Pressure (Load Computation)
When converting area loads ($kN/m^2$ or $kPa$) to line loads ($kN/m$) for frame analysis, use the frame spacing (Tributary Width):
$$w [kN/m] = p [kPa] \times Spacing [m]$$

**Standard Methodology for Report Inclusion:**
Include a "Loading Data" section in the report that explicitly shows:
- **Dead Load ($DL$):** $0.9 kPa \times 4.7m = 4.23 kN/m$
- **Wind Load ($WL$):** $0.9 kPa \times 4.7m = 4.23 kN/m$
- **Load Proxy for Seismic:** $0.10 \times DL = 0.42 kN/m$

### 2. Standard Load Combinations (NSCP/LRFD)
Follow the National Structural Code of the Philippines (NSCP 2015) or LRFD patterns. Core combinations for steel analysis:

| ID | Combination | Usage |
| --- | --- | --- |
| **LC1** | $1.4 D$ | Basic gravity (dead load only) |
| **LC2** | $1.2 D + 1.6 L + 0.5 (L_r \text{ or } R)$ | Standard occupancy gravity |
| **LC3** | $1.2 D + 1.0 W + L + 0.5 (L_r \text{ or } R)$ | Wind + Gravity |
| **LC4** | $1.2 D + 1.0 E + L + 0.2 S$ | Seismic + Gravity |
| **LC5** | $0.9 D + 1.0 W$ | Wind Uplift (Net suction) |

*Note: In `anastruct`, build a `SystemElements` instance per load combination or use superposition for linear analysis.*

---

## Module Reference

### 1. Database Loading & Selection (`aisc_database.py`)

**Class**: `AISCDatabase`

Loads the Excel database (`aisc-shapes-database-v160-2.xlsx`) and provides filtering and capacity checks.

**Key capabilities:**
- **Shape types supported**: `W`, `HSS`, `L`, `WT`, `2L`
- **Capacity checks**: AISC Chapter E compression ($F_{cr}$, $\phi P_n$) and tension ($\phi P_n = 0.9 F_y A_g$)
- **Slenderness limits**: $KL/r \leq 200$ (compression), $KL/r \leq 300$ (tension)
- **Geometric width filtering** (`bf_max` parameter): Filters out shapes wider than a specified limit. Width is calculated differently per shape type:
  - `WT`: uses `bf` (flange width)
  - `L`: uses `max(b, d)` (outstanding leg dimension)
  - `2L`: uses `2*b + 0.375` (assumes 3/8" gusset plate gap)
  - `W`: uses `bf` (flange width)
- **Material**: Currently enforced as A36 steel ($F_y = 36$ ksi) for all shapes.

**Key methods:**
```python
# Select all passing shapes, sorted lightest-first
candidates = aisc_db.select_candidates(Pu_kN, L_m, family='L', bf_max=4.0)

# Select the single lightest passing shape
shape = aisc_db.select_lightest(Pu_kN, L_m, family='WT', bf_max=None)
```

**Return dict keys per shape:**
`Label`, `Weight` (plf), `Area` (in²), `Ix` (in⁴), `KL/r`, `Capacity_kN`, `bf_in`

---

### 2. Geometry Creation (`truss_builder.py`)

**Functions:**
- `build_longitudinal_truss(results_map=None)` → `(SystemElements, mapping_dict)`
- `build_transverse_stiffening_truss(transfer_load_kn, results_map=None)` → `(SystemElements, mapping_dict)`
- `build_transverse_frame()` → `SystemElements`
- `get_max_group_forces(system, ids)` → `float` (max absolute axial force in kN)

**Current longitudinal truss geometry:**
- 16 panels, 18.7m span, 0.6m depth, 1.0m rise (sloped)
- Bottom chord base elevation: `y_base = 7.2` (sits atop columns)
- Two fixed-base columns: Left = 7.2m tall, Right = 8.2m tall
- Loads: `-4.6 kN/m` distributed on top chord (gravity), `3.2 kN/m` lateral on first bottom chord panel

**Pattern for injecting AISC properties:**
```python
def get_props(group_name):
    r = results_map.get(group_name)
    if r:
        return float(r['Area'] * 0.00064516) * 200e9, float(r['Ix'] * 4.1623e-7) * 200e9
    return 0, 0  # defaults
```

---

### 3. Iterative Optimization (`optimizer.py`)

**Function**: `run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="WT", web_family="L")`

**Optimization sequence:**
1. Build truss with default stiffness → `solve()` → extract member forces.
2. **Size chords first** (Top Chord, Bottom Chord) using `select_lightest()`.
3. **Derive chord flange width** (`bf_chord`) from the narrowest selected chord.
4. **Size webs with geometric constraint** (`bf_max=bf_chord`). If an `L` shape fails the width or capacity check, **automatically fall back to `2L`** (double angle).
5. Enter deflection optimization loop:
   - Rebuild system with current properties → `solve()` → check $L/\delta$.
   - If deflection fails, step up to the next heaviest chord from the candidate list.
   - Repeat until $L/\delta \geq$ target or max iterations reached.
6. **Size columns** from the max vertical support reaction using `W` shapes.
7. **Compute total truss weight** (kg) and **estimated material cost** (PHP) at a configurable rate.

**Geometric web constraint logic:**
```python
bf_chord = min(top_chord['bf_in'], bottom_chord['bf_in'])

res = aisc_db.select_lightest(p, L, family='L', bf_max=bf_chord)
if res is None and family == 'L':
    # Fallback: single angle too wide → use double angle
    res = aisc_db.select_lightest(p, L, family='2L', bf_max=bf_chord)
```

**Cost estimation:**
```python
for group in truss_groups:
    weight_lbs = plf * (L_m * 3.28084) * member_count
    total_weight_kg += weight_lbs * 0.453592
total_cost_php = total_weight_kg * 60  # PHP/kg rate
```

---

### 4. Markdown Reporting (`report_generator.py`)

**Function**: `generate_markdown_report(longitudinal_data, longitudinal_data_2l, frame_data)`

**Report sections generated:**
1. **Section 1**: Longitudinal Truss (WT Chords, L Webs) — member table, deflection, plots, weight, cost
2. **Section 1B**: Alternative Longitudinal Truss (2L Chords) — same format
3. **Section 1C**: Alternative Concrete Substructure — computed from support reactions:
   - **Square Column**: Sized by slenderness ($L/h \leq 30$), includes eccentricity moment ($M_u = P_u \times e$)
   - **Isolated Footing**: Sized by allowable soil bearing pressure (100 kPa)
   - Material assumptions: $f'_c = 21$ MPa, $f_y = 275$ MPa (Grade 40)
4. **Section 2**: Transverse Moment Frame — structure, axial, displacement, reaction plots

**Plot generation pattern:**
```python
fig = ss.show_structure(show=False)
fig.savefig('images/longitudinal_structure.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

---

### 5. Orchestration (`simulate_full_system.py`)

Clean entry point that calls optimization functions in sequence and passes results to the report generator. Run with: `python simulate_full_system.py`

---

## Advanced Result Extraction

### 1. Standardized Reaction Extraction
When preparing data for foundation design (footings), always extract the full set of reactions ($R_x, R_y, M_z$) from support nodes.

```python
def get_reactions(ss, node_id):
    res = ss.get_node_results_system(node_id)
    if isinstance(res, dict):
        return {
            'Rx': abs(res.get('Fx', 0.0)),
            'Ry': abs(res.get('Fy', 0.0)),
            'Mz': abs(res.get('Tz', 0.0))
        }
    elif isinstance(res, (list, np.ndarray)):
        return {
            'Rx': abs(res[0]),
            'Ry': abs(res[1]),
            'Mz': abs(res[2])
        }
    return {'Rx': 0.0, 'Ry': 0.0, 'Mz': 0.0}
```

### 2. Deflection & Force Envelopes
For linear systems with multiple load combinations, the max effect (Envelope) should be used for member selection.
- **Deflection**: Max vertical displacement at span middle or apex.
- **Axial/Shear/Moment**: Max absolute values across all elements in a group.

---

## Standard Structural Report Outline

Every structural analysis report MUST follow this logical flow:

1.  **Project Overview**: Frame type, span, spacing, and column height.
2.  **Structural Assumptions**: Material properties ($F_y, f'_c$) and soil parameters.
3.  **Loading Data**:
    - Load Computation (Pressure $\to$ Line Load).
    - Load Combinations (NSCP/LRFD Cases).
4.  **Analysis Results**: 
    - Selected Member Tables (AISC Label, Weight, Capacity Ratio).
    - Deflection Summary (Max vs Allowable $L/240$).
5.  **Support Reactions**: Summary table for $R_x, R_y, M_z$.
6.  **Substructure Design**: Concrete pedestal and isolated footing sizing.
7.  **Conclusion & Visualizations**:
    - Structure/Loads Plot.
    - Axial Force/Moment Diagrams.
    - Displacement/Reactions Plots.

---

## Common Pitfalls & Fixes

| Problem | Root Cause | Fix |
| --- | --- | --- |
| `math domain error` in footing calc | Reaction force is negative (downward) | Use `abs()` before `math.sqrt()` |
| `NameError: avg_reaction_kn` | Variable deleted during refactor | Ensure `avg_reaction_kn = max_react_y` is assigned before `return` |
| `TypeError` on node results | Node objects vs IDs | Use `nid = node.id if hasattr(node, 'id') else node` |
| Web member juts out of chord flange | Angle leg wider than WT flange | Pass `bf_max=chord_bf` to `select_lightest()`, fallback to `2L` |
| Deflection doesn't change after re-solve | Properties set via `element_map` | Rebuild entire `SystemElements` with `add_element(EA=..., EI=...)` |
| `KeyError` on `element.node_map` | Keys are node IDs, not indices | Use `list(el.node_map.keys())[0]` or `.id` attribute of the node. |
