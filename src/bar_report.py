"""
Bar Project — Structural report generator.

Generates a markdown report with structural plots for the Howe truss with
2 interior columns. Includes separate foundation design for exterior and
interior columns.
"""

import os
import matplotlib.pyplot as plt
import math
from .aisc_database import aisc_db

# Resolve project root (one level up from src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_bar_report(truss_data, project_name="Bar_Project"):
    """Generates a markdown report for the bar Howe truss analysis."""

    output_dir = os.path.join(_PROJECT_ROOT, 'output', project_name)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)

    report = ["# Bar Project — Structural Optimization Report\n"]

    ss = truss_data['system']
    res = truss_data['results']
    ratio = truss_data['ratio']
    max_d = truss_data['max_deflection_m']
    gov_react_y = truss_data.get('gov_react_y', truss_data.get('end_reaction', 0))
    gov_react_x = truss_data.get('gov_react_x', 0)
    gov_react_y_ext = truss_data.get('gov_react_y_ext', gov_react_y)
    gov_react_y_int = truss_data.get('gov_react_y_int', 0)
    lc_data = truss_data.get('load_cases', {})

    has_int_cols = truss_data.get('has_int_cols', True)

    # ============================================================
    # 1. TRUSS CONFIGURATION
    # ============================================================
    report.append("## 1. Truss Configuration\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append("| Span | `21.0 m` |")
    report.append("| End Depth | `0.0 m` (Isosceles Triangle) |")
    report.append("| Depth at Midspan (Peak) | `2.0 m` |")
    report.append("| Bottom Chord | **Level at y = 0.0 m** |")
    report.append("| Column Height | `4.0 m` (Fixed base, RC columns) |")
    report.append("| Panels | `21 @ 1.0 m` |")
    report.append("| Type | **Isosceles Triangle Howe Truss** |")
    report.append("| Chord Construction | **Double Angles (2L)** — back-to-back for gusset plates |")
    report.append("| Web Construction | **Square or Rectangular Pipe (Cold Rolled Tubular Steel)** |")
    report.append("| Connections | Site-welded using `6mm` or `10mm` gusset plates |")
    if has_int_cols:
        report.append("| Supports | **4 fixed-base RC columns**: 2 exterior + 2 interior |")
        report.append("| Interior Column Locations | Exactly at 7.0 m and 14.0 m |")
    else:
        report.append("| Supports | **2 fixed-base RC columns**: Exterior only (Long Span) |")
    report.append("| Steel Grade | `A36 (Fy = 36 ksi)` |\n")
    report.append("| Concrete Grade | `21 MPa (3000 psi)` |\n")

    # ============================================================
    # 2. LOADS
    # ============================================================
    report.append("## 2. Applied Loads\n")
    report.append("### Gravity Loads\n")
    base_dl = truss_data.get('base_gravity', -3.0)
    base_ll = truss_data.get('live_gravity', -3.6)
    self_w_q = truss_data.get('self_weight_q', 0)
    total_dl = truss_data.get('total_gravity', base_dl)

    report.append("| Component | Value |")
    report.append("| --- | --- |")
    report.append("| Dead Load (Roof + Ceiling) | `3.0 kN/m` (0.5 kPa × 6m trib.) |")
    report.append(f"| Truss + RC Col Self-Weight | `{abs(self_w_q):.3f} kN/m` |")
    report.append(f"| **Total Dead Load (D)** | **`{abs(total_dl):.3f} kN/m`** |")
    report.append(f"| **Live Load (L)** | **`{abs(base_ll):.3f} kN/m`** (0.6 kPa × 6m trib.) |\n")

    report.append("### Earthquake (Static Method — NSCP)\n")
    Cs = truss_data.get('Cs', 0.20)
    W_seis = truss_data.get('W_seismic', 0)
    V_base = truss_data.get('V_base_shear', 0)
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Seismic Coefficient ($C_s$) | `{Cs}` (Zone 4, Soil Type D, R=8.5) |")
    report.append(f"| Seismic Weight ($W$) | `{W_seis:.2f} kN` |")
    report.append(f"| Base Shear ($V = C_s \\times W$) | **`{V_base:.2f} kN`** |")
    report.append(f"| Lateral q per exterior column ($V / 4 / h$) | `{V_base / (4*4):.2f} kN/m` |\n")

    wind_q = truss_data.get('wind_q_kn_m', 4.8)
    report.append("### Wind Load\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append("| Wind Pressure | `800 Pa` |")
    report.append("| Tributary Width | `6.0 m` |")
    report.append(f"| Lateral Load on Ext. Columns | **`{wind_q:.1f} kN/m`** (800 Pa × 6m) |\n")

    # ============================================================
    # 3. LOAD CASE COMPARISON TABLE
    # ============================================================
    report.append("## 3. Load Case Summary\n")

    if lc_data:
        groups = ["Top Chord", "Bottom Chord", "Vertical Webs", "Diagonal Webs", "Exterior Columns"]
        if has_int_cols:
            groups.append("Interior Columns")

        # Forces per group per LC
        report.append("### Axial Forces (kN) per Load Case\n")
        header = "| Member Group | " + " | ".join(lc.replace(":", " —") for lc in lc_data.keys()) + " | **Governing** |"
        sep = "| --- | " + " | ".join(["---"] * len(lc_data)) + " | --- |"
        report.append(header)
        report.append(sep)
        for g in groups:
            row = f"| {g}"
            for lc_name, lcr in lc_data.items():
                f = lcr['forces'].get(g, 0)
                row += f" | {f:.2f}"
            gov_f = truss_data.get('governing_forces', {}).get(g, 0)
            row += f" | **{gov_f:.2f}** |"
            report.append(row)

        # Reactions per LC
        report.append("\n### Support Reactions per Load Case\n")
        header2 = "| Reaction | " + " | ".join(lc.replace(":", " —") for lc in lc_data.keys()) + " | **Governing** |"
        report.append(header2)
        report.append(sep)

        fy_row = "| Vertical ($F_y$) — Max"
        fx_row = "| Horizontal ($F_x$) — Max"
        fy_ext_row = "| Vertical ($F_y$) — Exterior"
        
        for lc_name, lcr in lc_data.items():
            fy_row += f" | {lcr['max_react_y']:.2f}"
            fx_row += f" | {lcr['max_react_x']:.2f}"
            fy_ext_row += f" | {lcr['max_react_y_ext']:.2f}"
            
        fy_row += f" | **{gov_react_y:.2f}** |"
        fx_row += f" | **{gov_react_x:.2f}** |"
        fy_ext_row += f" | **{gov_react_y_ext:.2f}** |"
        report.append(fy_row)
        report.append(fy_ext_row)

        if has_int_cols:
            fy_int_row = "| Vertical ($F_y$) — Interior"
            for lc_name, lcr in lc_data.items():
                fy_int_row += f" | {lcr['max_react_y_int']:.2f}"
            fy_int_row += f" | **{gov_react_y_int:.2f}** |"
            report.append(fy_int_row)

        report.append(f"\n> **Governing Vertical Reaction (Exterior):** `{gov_react_y_ext:.2f} kN`")
        if has_int_cols:
            report.append(f"> **Governing Vertical Reaction (Interior):** `{gov_react_y_int:.2f} kN`")
        report.append(f"> **Governing Horizontal Reaction:** `{gov_react_x:.2f} kN` ({truss_data.get('gov_react_x_lc', '')})\n")

    # ============================================================
    # 4. DEFLECTION CHECK
    # ============================================================
    report.append("## 4. Deflection Check\n")
    report.append(f"- **Max Deflection:** `{abs(max_d)*1000:.2f} mm`")
    status = "PASS" if ratio >= 240 else "FAIL"
    report.append(f"- **Deflection Ratio (L/d):** `{ratio:.0f}` (Target > 240) {status}\n")

    # ============================================================
    # 5. OPTIMIZED MEMBER SELECTION
    # ============================================================
    report.append("## 5. Optimized Member Selection (Governing Forces)\n")
    report.append("| Group | Selected Shape (Standard / Comm.) | Weight | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |")
    report.append("| --- | --- | --- | --- | --- | --- | --- |")
    for group, shape in res.items():
        if shape is None:
            continue
        force = shape.get('Max_Force_kN', 0)
        klr = shape.get('KL/r', 0)
        cap = shape.get('Capacity_kN', 0)
        glc = shape.get('Governing_LC', 'N/A')
        glc_short = glc.split(": ")[-1] if ": " in glc else glc
        
        # Determine labels
        aisc_label = shape['Label']
        comm_label = aisc_db.get_commercial_label(shape)
        if aisc_label != comm_label:
            full_label = f"`{aisc_label}` / **{comm_label}**"
        else:
            full_label = f"`{aisc_label}`"
            
        w_str = f"{shape['Weight']:.1f} plf" if shape.get('Type') != 'RC' else f"{shape['Weight']:.1f} kg/m"
        report.append(f"| {group} | {full_label} | {w_str} | {klr:.1f} | {force:.2f} | {cap:.2f} | {glc_short} |")

    report.append(f"\n- **Total Steel Weight:** `{truss_data.get('total_weight_kg', 0):.1f} kg`")
    report.append(f"- **Total Concrete Weight (Cols):** `{truss_data.get('total_concrete_kg', 0):.1f} kg`")
    report.append(f"- **Estimated Steel Cost:** `PHP {truss_data.get('total_cost_php', 0):,.2f}` (@ PHP 60/kg)\n")

    # ============================================================
    # 6. SUBSTRUCTURE DESIGN
    # ============================================================
    report.append("## 6. Substructure Design\n")

    fc = 21    # MPa
    fy = 275   # MPa (Grade 40)
    qa = 100   # kPa allowable soil bearing

    report.append("Design assumptions:\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Concrete Strength ($f'_c$) | `{fc} MPa (3000 psi)` |")
    report.append(f"| Rebar Yield Strength ($f_y$) | `{fy} MPa (Grade 40)` |")
    report.append(f"| Allowable Soil Bearing ($q_a$) | `{qa} kPa` |\n")

    # --- Helper function for foundation section ---
    def _write_foundation(label, pu_kn, shape_dict, col_height_m):
        section = []
        section.append(f"\n### {label}\n")
        section.append(f"**Column:** `{shape_dict['Label']}`, Height: `{col_height_m:.2f} m`, $P_u$ = `{pu_kn:.2f} kN`\n")

        is_rc = (shape_dict.get('Type') == 'RC')

        if not is_rc:
            # Steel Base Plate logic...
            col_d_mm, col_bf_mm = 152, 152
            phi_bearing = 0.65
            Pu_N = pu_kn * 1000
            A_req_mm2 = Pu_N / (phi_bearing * 0.85 * fc) if Pu_N > 0 else 10000
            bp_B_mm = max(col_bf_mm + 100, math.ceil(math.sqrt(max(A_req_mm2, 1)) / 50) * 50)
            bp_N_mm = max(col_d_mm + 100, bp_B_mm)
            bp_area_mm2 = bp_B_mm * bp_N_mm
            fp_actual = Pu_N / bp_area_mm2 if bp_area_mm2 > 0 else 0
            fp_allow = phi_bearing * 0.85 * fc
            m_proj = max((bp_N_mm - 0.95 * col_d_mm) / 2, (bp_B_mm - 0.80 * col_bf_mm) / 2)
            Fy_bp = 248
            tp_mm = max(10, math.ceil(m_proj * math.sqrt(max(2 * fp_actual / Fy_bp, 0))))
            tp_mm = math.ceil(tp_mm / 2) * 2

            section.append("#### Steel Base Plate\n")
            section.append("| Parameter | Value |")
            section.append("| --- | --- |")
            section.append(f"| Base Plate (B × N) | `{bp_B_mm} mm × {bp_N_mm} mm` |")
            section.append(f"| Thickness ($t_p$) | `{tp_mm} mm` |")
            check = '✅' if fp_actual <= fp_allow else '❌'
            section.append(f"| Bearing Stress | `{fp_actual:.2f} MPa` ≤ `{fp_allow:.2f} MPa` ({check}) |")
            section.append(f"| Anchor Bolts | `4 — 16mm Ø` |\n")
        else:
            section.append("> [!NOTE]")
            section.append("> RC Columns are cast monolithically with the pedestal/footing. Steel base plates and anchor bolts are not required.\n")

        # Column / Pedestal Details
        col_size_mm = 400
        section.append("#### Column & Pedestal Details\n")
        section.append("| Parameter | Value |")
        section.append("| --- | --- |")
        section.append(f"| RC Column Section | `{col_size_mm} mm × {col_size_mm} mm` |")
        section.append(f"| Vertical Reinforcement | `8 — 16mm Ø bars` (Grade 40) |")
        section.append(f"| Lateral Ties | `10mm Ø @ 200mm O.C.` |")
        section.append(f"| Concrete Cover | `40 mm` |\n")

        # Footing
        p_service_kN = pu_kn / 1.5
        footing_area_m2 = p_service_kN / qa if p_service_kN > 0 else 1.0
        footing_size_m = max(1.0, math.ceil(math.sqrt(max(footing_area_m2, 0.01)) * 10) / 10)
        footing_thick_m = 0.40
        actual_q = p_service_kN / footing_size_m**2 if footing_size_m > 0 else 0

        section.append("#### Isolated Square Footing\n")
        section.append("| Parameter | Value |")
        section.append("| --- | --- |")
        section.append(f"| Dimensions | `{footing_size_m:.1f} m × {footing_size_m:.1f} m × {footing_thick_m:.2f} m` |")
        section.append(f"| Bearing Pressure | `{actual_q:.1f} kPa` ≤ `{qa} kPa` ✅ |")
        section.append("| Bottom Rebar | `12mm Ø @ 200mm O.C.` (Both Ways) |\n")

        return section

    # Exterior foundation
    report.extend(_write_foundation("Exterior Column Foundation (×2)", gov_react_y_ext, res.get("Exterior Columns", {}), 4.0))

    # Tie Beam note
    report.append("#### Tie Beam Details")
    report.append("- **Size:** `300mm x 400mm` RC Tie Beam")
    report.append("- **Reinforcement:** `4 - 16mm Ø` main bars with `10mm Ø @ 200mm` stirrups")
    report.append("- **Purpose:** Seismic connectivity between footings at ends\n")

    # Interior foundation
    if has_int_cols:
        report.extend(_write_foundation("Interior Column Foundation (×2)", gov_react_y_int, res.get("Interior Columns", {}), 4.0))

    # ============================================================
    # 7. STRUCTURAL PLOTS
    # ============================================================
    report.append("## 7. Structural Plots\n")

    # Plot gravity-only system
    plots = [
        ('show_structure',      'structure',    'Structure & Applied Loads (Gravity)'),
        ('show_axial_force',    'axial',        'Axial Forces (Gravity)'),
        ('show_displacement',   'displacement', 'Deflection (Gravity)'),
        ('show_reaction_force', 'reactions',    'Support Reactions (Gravity)'),
    ]
    for method_name, filename, title in plots:
        try:
            fig = getattr(ss, method_name)(show=False)
            fig.savefig(os.path.join(images_dir, f'bar_{filename}.png'), dpi=150, bbox_inches='tight')
            plt.close(fig)
            report.append(f"#### {title}")
            report.append(f"![{title}](images/bar_{filename}.png)\n")
        except Exception as e:
            report.append(f"*(Plot failed: {title} — {e})*\n")

    # Plot wind case (highest lateral)
    if lc_data:
        wind_sys = lc_data.get("LC3: Gravity + Wind", {}).get("system")
        if wind_sys:
            wind_plots = [
                ('show_structure',      'wind_structure',  'Structure & Loads (Wind Case)'),
                ('show_axial_force',    'wind_axial',      'Axial Forces (Wind Case)'),
                ('show_reaction_force', 'wind_reactions',  'Reactions (Wind Case)'),
            ]
            for method_name, filename, title in wind_plots:
                try:
                    fig = getattr(wind_sys, method_name)(show=False)
                    fig.savefig(os.path.join(images_dir, f'bar_{filename}.png'), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    report.append(f"#### {title}")
                    report.append(f"![{title}](images/bar_{filename}.png)\n")
                except Exception as e:
                    report.append(f"*(Plot failed: {title} — {e})*\n")

    # ── Write report ───────────────────────────────────────────────
    report_path = os.path.join(output_dir, 'structural_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\nOK: Bar report generated: output/{project_name}/structural_report.md")
