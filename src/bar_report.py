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


def generate_bar_report(truss_data, warren_data=None, project_name="Bar_Project"):
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
    # Dynamically determine chord construction label from results
    top_chord_label = res.get("Top Chord", {}).get('Label', '2L')
    if top_chord_label.startswith('2L'):
        chord_desc = "**Double Angles (2L)** — back-to-back for gusset plates"
    elif top_chord_label.startswith('L'):
        chord_desc = "**Single Angles (L)** — welded to gusset plates"
    else:
        chord_desc = f"**{top_chord_label}**"
    report.append(f"| Chord Construction | {chord_desc} |")
    # Dynamically determine web construction label from results
    vert_web_label = res.get("Vertical Webs", {}).get('Label', 'HSS')
    if vert_web_label.startswith('HSS'):
        web_desc = "**Square or Rectangular Pipe (Cold Rolled Tubular Steel)**"
    elif vert_web_label.startswith('L'):
        web_desc = "**Single Angles (L)** — welded to gusset plates"
    else:
        web_desc = f"**{vert_web_label}**"
    report.append(f"| Web Construction | {web_desc} |")
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

    trib_w = truss_data.get('trib_width', 5.0)
    dl_kpa = truss_data.get('dl_kpa', 0.5)
    ll_kpa = truss_data.get('ll_kpa', 0.6)

    report.append("| Component | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dead Load (Roof + Ceiling) | `{abs(base_dl):.1f} kN/m` ({dl_kpa} kPa × {trib_w:.0f}m trib.) |")
    report.append(f"| Truss + RC Col Self-Weight | `{abs(self_w_q):.3f} kN/m` |")
    report.append(f"| **Total Dead Load (D)** | **`{abs(total_dl):.3f} kN/m`** |")
    report.append(f"| **Live Load (L)** | **`{abs(base_ll):.3f} kN/m`** ({ll_kpa} kPa × {trib_w:.0f}m trib.) |\n")

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

    wind_kpa = truss_data.get('wind_kpa', 0.8)
    wind_q = truss_data.get('wind_q_kn_m', wind_kpa * trib_w)
    report.append("### Wind Load\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Wind Pressure | `{int(wind_kpa*1000)} Pa` |")
    report.append(f"| Tributary Width | `{trib_w:.0f} m` |")
    report.append(f"| Lateral Load on Ext. Columns | **`{wind_q:.1f} kN/m`** ({int(wind_kpa*1000)} Pa × {trib_w:.0f}m) |\n")

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
        cap = shape.get('Capacity_kN') or shape.get('phi_Pn_kN', 0)
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
    report.append(f"- **Total Concrete Weight (Cols):** `{truss_data.get('total_concrete_kg', 0):.1f} kg`\n")

    # ============================================================
    # 6. SUBSTRUCTURE DESIGN
    # ============================================================
    report.append("## 6. Substructure Design\n")

    fc = 21    # MPa
    fy = 275   # MPa (Grade 40)
    qa = 144   # kPa allowable soil bearing (from soil test)
    foundation_depth = 1.0  # m below grade

    report.append("Design assumptions:\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Concrete Strength ($f'_c$) | `{fc} MPa (3000 psi)` |")
    report.append(f"| Rebar Yield Strength ($f_y$) | `{fy} MPa (Grade 40)` |")
    report.append(f"| Allowable Soil Bearing ($q_a$) | `{qa} kPa` (from soil test) |")
    report.append(f"| Foundation Depth | `{foundation_depth:.1f} m` below grade |\n")

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

        # Column / Pedestal Details — dynamic from optimizer
        col_size_mm = shape_dict.get('h_mm', 400)
        n_bars = shape_dict.get('n_bars', 8)
        bar_dia = shape_dict.get('bar_dia', 16)
        kLu_r = shape_dict.get('kLu_r', 0)
        phi_Pn = shape_dict.get('phi_Pn_kN', 0)
        delta_ns = shape_dict.get('delta_ns', 1.0)
        Mc_kNm = shape_dict.get('Mc_kNm', 0)

        slender_status = "Short" if kLu_r <= 34 else "Slender"
        klr_check = "✅" if kLu_r <= 60 else "❌"
        cap_check = "✅" if phi_Pn >= pu_kn else "❌"

        # Tie spacing: min of 16*bar_dia, 48*tie_dia (10mm), or col_size
        tie_spacing = min(16 * bar_dia, 48 * 10, col_size_mm)

        section.append("#### Column & Pedestal Details\n")
        section.append("| Parameter | Value |")
        section.append("| --- | --- |")
        section.append(f"| RC Column Section | `{col_size_mm} mm × {col_size_mm} mm` |")
        section.append(f"| Vertical Reinforcement | `{n_bars} — {bar_dia}mm Ø bars` (Grade 40) |")
        section.append(f"| Lateral Ties | `10mm Ø @ {tie_spacing}mm O.C.` |")
        section.append(f"| Concrete Cover | `40 mm` |")
        section.append(f"| Slenderness ($kL_u/r$) | `{kLu_r:.1f}` ({slender_status}) {klr_check} |")
        section.append(f"| Axial Capacity ($\\phi P_n$) | `{phi_Pn:.1f} kN` ≥ `{pu_kn:.1f} kN` {cap_check} |")
        if delta_ns > 1.0:
            section.append(f"| Moment Magnification ($\\delta_{{ns}}$) | `{delta_ns:.3f}` |")
            section.append(f"| Magnified Moment ($M_c$) | `{Mc_kNm:.2f} kN·m` |")
        section.append("")

        # Footing — optimized for qa
        p_service_kN = pu_kn / 1.5
        footing_area_m2 = p_service_kN / qa if p_service_kN > 0 else 0.36
        # Minimum footing = column width + 100mm overhang each side
        min_footing_m = (col_size_mm + 200) / 1000.0
        footing_size_m = max(min_footing_m, math.ceil(math.sqrt(max(footing_area_m2, 0.01)) * 10) / 10)
        # Footing thickness: minimum 200mm
        col_size_m = col_size_mm / 1000.0
        footing_thick_m = max(0.20, round((footing_size_m - col_size_m) / 2 * 0.5 + 0.15, 2))
        footing_thick_m = math.ceil(footing_thick_m / 0.05) * 0.05  # round up to 50mm
        actual_q = p_service_kN / footing_size_m**2 if footing_size_m > 0 else 0
        check = '✅' if actual_q <= qa else '❌'

        section.append("#### Isolated Square Footing\n")
        section.append("| Parameter | Value |")
        section.append("| --- | --- |")
        section.append(f"| Foundation Depth | `{foundation_depth:.1f} m` below grade |")
        section.append(f"| Dimensions | `{footing_size_m:.2f} m × {footing_size_m:.2f} m × {footing_thick_m:.2f} m` |")
        section.append(f"| Bearing Pressure | `{actual_q:.1f} kPa` ≤ `{qa} kPa` {check} |")
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

    # ============================================================
    # 8. TOP-SUPPORTED WARREN TRANSFER TRUSS
    # ============================================================
    if warren_data:
        report.append("## 8. Top-Supported Warren Transfer Truss\n")
        w_span = warren_data.get('span', 10.0)
        w_depth = warren_data.get('depth', 1.4)
        w_panels = warren_data.get('n_panels', 8)
        w_pl = warren_data.get('point_load_kN', 0)
        w_sl = warren_data.get('service_load_kN', 0)
        w_cfam = warren_data.get('chord_family', 'L')
        w_wfam = warren_data.get('web_family', 'L')

        def get_fam_desc(fam):
            if fam == 'L': return "Single Angles (L)"
            elif fam == '2L': return "Double Angles (2L)"
            elif fam == 'HSS': return "Square or Rectangular Pipe (HSS)"
            return fam

        w_cfam_desc = get_fam_desc(w_cfam)
        w_wfam_desc = get_fam_desc(w_wfam)
        if w_cfam == w_wfam:
            w_fam_desc = f"**{w_cfam_desc}**"
        else:
            w_fam_desc = f"**{w_cfam_desc}** Chords, **{w_wfam_desc}** Webs"

        report.append("### Configuration\n")
        report.append("| Parameter | Value |")
        report.append("| --- | --- |")
        report.append(f"| Truss Type | **Top-Supported Warren** (underslung, top chord extended) |")
        report.append(f"| Purpose | Transfer beam — carries interior column load to adjacent frames |")
        report.append(f"| Span | `{w_span:.1f} m` |")
        report.append(f"| Depth | `{w_depth:.1f} m` |")
        report.append(f"| Bays | `{w_panels // 2 if w_panels else 4}` @ `{w_span/(w_panels // 2 if w_panels else 4):.2f} m` |")
        report.append(f"| Member Construction | {w_fam_desc} |")
        report.append(f"| Point Load (Factored) | `{w_pl:.2f} kN` at midspan (from interior column reaction) |")
        report.append(f"| Point Load (Service) | `{w_sl:.2f} kN` (factored / 1.5) |")
        report.append(f"| Supports | Simply supported (pin + roller) at top chord |\n")

        # Deflection check
        w_ratio = warren_data.get('ratio', 0)
        w_max_uy = warren_data.get('max_deflection_m', 0)
        defl_status = "PASS" if w_ratio >= 360 else "FAIL"
        report.append("### Deflection Check\n")
        report.append(f"- **Max Deflection:** `{abs(w_max_uy)*1000:.2f} mm`")
        report.append(f"- **Deflection Ratio (L/d):** `{w_ratio:.0f}` (Target > 360) {defl_status}\n")

        # Member selection table
        w_res = warren_data.get('results', {})
        report.append("### Optimized Member Selection\n")
        report.append("| Group | Selected Shape | Weight | KL/r | Gov. Force (kN) | Capacity (kN) |")
        report.append("| --- | --- | --- | --- | --- | --- |")
        for group in ["Top Chord", "Bottom Chord", "Verticals", "Diagonals"]:
            shape = w_res.get(group)
            if not shape:
                continue
            force = shape.get('Max_Force_kN', 0)
            klr = shape.get('KL/r', 0)
            cap = shape.get('Capacity_kN', 0)
            aisc_label = shape['Label']
            comm_label = aisc_db.get_commercial_label(shape)
            if aisc_label != comm_label:
                full_label = f"`{aisc_label}` / **{comm_label}**"
            else:
                full_label = f"`{aisc_label}`"
            w_str = f"{shape['Weight']:.1f} plf"
            report.append(f"| {group} | {full_label} | {w_str} | {klr:.1f} | {force:.2f} | {cap:.2f} |")

        w_weight = warren_data.get('total_weight_kg', 0)
        report.append(f"\n- **Total Steel Weight:** `{w_weight:.1f} kg`")

        w_ry = warren_data.get('max_react_y', 0)
        report.append(f"- **Support Reactions:** `{w_ry:.2f} kN` per end (transferred to interior columns)\n")

        # Plots
        report.append("### Structural Plots\n")
        w_ss = warren_data.get('system')
        if w_ss:
            warren_plots = [
                ('show_structure',      'warren_top_structure',    'Top-Supported Warren -- Structure & Point Load'),
                ('show_axial_force',    'warren_top_axial',        'Top-Supported Warren -- Axial Forces'),
                ('show_displacement',   'warren_top_displacement', 'Top-Supported Warren -- Deflection'),
                ('show_reaction_force', 'warren_top_reactions',    'Top-Supported Warren -- Support Reactions'),
            ]
            for method_name, filename, title in warren_plots:
                try:
                    fig = getattr(w_ss, method_name)(show=False)
                    fig.savefig(os.path.join(images_dir, f'{filename}.png'), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    report.append(f"#### {title}")
                    report.append(f"![{title}](images/{filename}.png)\n")
                except Exception as e:
                    report.append(f"*(Plot failed: {title} -- {e})*\n")

    # -- Write report -------------------------------------------------
    report_path = os.path.join(output_dir, 'structural_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\nOK: Bar report generated: output/{project_name}/structural_report.md")
