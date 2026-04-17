import os
import matplotlib.pyplot as plt
import math

# Resolve project root (one level up from src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_pickleball_report(truss_data, project_name="Pickleball_Court"):
    """Generates a markdown report for the pickleball court truss analysis."""
    
    output_dir = os.path.join(_PROJECT_ROOT, 'output', project_name)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    report = ["# Pickleball Court — Structural Optimization Report\n"]
    
    ss = truss_data['system']
    res = truss_data['results']
    ratio = truss_data['ratio']
    max_d = truss_data['max_deflection_m']
    gov_react_y = truss_data.get('gov_react_y', truss_data.get('end_reaction', 0))
    gov_react_x = truss_data.get('gov_react_x', 0)
    
    # ============================================================
    # 1. TRUSS CONFIGURATION
    # ============================================================
    report.append("## 1. Truss Configuration\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append("| Span | `24.0 m` |")
    report.append("| Depth | `2.0 m` (constant between chords) |")
    report.append("| Center Rise | `3.0 m` |")
    report.append("| Column Height | `6.0 m` (fixed base) |")
    report.append("| Panels | `16 @ 1.5 m` |")
    report.append("| Type | Two-Slope (Gable) Symmetrical Pratt Truss |")
    report.append("| Supports | Fixed-base steel columns (2 nos.) |")
    report.append(f"| Steel Grade | `A36 (Fy = 36 ksi)` |\n")
    
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
    report.append(f"| Truss Self-Weight | `{abs(self_w_q):.3f} kN/m` ({truss_data.get('total_weight_kg', 0):.1f} kg / 24m) |")
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
    report.append(f"| Lateral q on each column ($V / 2 / h$) | `{V_base / (2*6):.2f} kN/m` |\n")
    
    wind_q = truss_data.get('wind_q_kn_m', 4.8)
    report.append("### Wind Load\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append("| Wind Pressure | `800 Pa` |")
    report.append("| Tributary Width | `6.0 m` |")
    report.append(f"| Lateral Load on Columns | **`{wind_q:.1f} kN/m`** (800 Pa × 6m) |\n")
    
    # ============================================================
    # 3. LOAD CASE COMPARISON TABLE
    # ============================================================
    report.append("## 3. Load Case Summary\n")
    lc_data = truss_data.get('load_cases', {})
    gov_lc = truss_data.get('governing_lc', {})
    
    if lc_data:
        groups = ["Top Chord", "Bottom Chord", "Vertical Webs", "Diagonal Webs", "Columns"]
        
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
        
        fy_row = "| Vertical ($F_y$)"
        fx_row = "| Horizontal ($F_x$)"
        for lc_name, lcr in lc_data.items():
            fy_row += f" | {lcr['max_react_y']:.2f}"
            fx_row += f" | {lcr['max_react_x']:.2f}"
        fy_row += f" | **{gov_react_y:.2f}** |"
        fx_row += f" | **{gov_react_x:.2f}** |"
        report.append(fy_row)
        report.append(fx_row)
        
        report.append(f"\n> **Governing Vertical Reaction:** `{gov_react_y:.2f} kN` ({truss_data.get('gov_react_y_lc', '')})")
        report.append(f"> **Governing Horizontal Reaction:** `{gov_react_x:.2f} kN` ({truss_data.get('gov_react_x_lc', '')})\n")
    
    # ============================================================
    # 4. DEFLECTION CHECK
    # ============================================================
    report.append("## 4. Deflection Check\n")
    report.append(f"- **Max Deflection:** `{abs(max_d)*1000:.2f} mm`")
    status = "✅ PASS" if ratio >= 240 else "❌ FAIL"
    report.append(f"- **Deflection Ratio (L/d):** `{ratio:.0f}` (Target > 240) {status}\n")
    
    # ============================================================
    # 5. OPTIMIZED MEMBER SELECTION (Governing)
    # ============================================================
    report.append("## 5. Optimized Member Selection (Governing Forces)\n")
    report.append("| Group | Selected Shape | Weight (plf) | KL/r | Gov. Force (kN) | Capacity (kN) | Governing LC |")
    report.append("| --- | --- | --- | --- | --- | --- | --- |")
    for group, shape in res.items():
        if shape is None:
            continue
        force = shape.get('Max_Force_kN', 0)
        klr = shape.get('KL/r', 0)
        cap = shape.get('Capacity_kN', 0)
        glc = shape.get('Governing_LC', 'N/A')
        # Short LC label
        glc_short = glc.split(": ")[-1] if ": " in glc else glc
        report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {klr:.1f} | {force:.2f} | {cap:.2f} | {glc_short} |")
    
    report.append(f"\n- **Total Steel Weight:** `{truss_data.get('total_weight_kg', 0):.1f} kg`")
    report.append(f"- **Estimated Steel Cost:** `PHP {truss_data.get('total_cost_php', 0):,.2f}` (@ PHP 60/kg)\n")
    
    # ============================================================
    # 6. SUBSTRUCTURE
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
    report.append(f"| Allowable Soil Bearing ($q_a$) | `{qa} kPa` |")
    report.append(f"| Governing Vertical Reaction ($P_u$) | `{gov_react_y:.2f} kN` |")
    report.append(f"| Governing Horizontal Reaction ($H_u$) | `{gov_react_x:.2f} kN` |\n")
    
    # --- Steel Base Plate ---
    report.append("### Steel Base Plate\n")
    col_shape = res.get("Columns", {})
    col_label = col_shape.get('Label', 'W6X15') if col_shape else 'W6X15'
    col_d_mm = 152
    col_bf_mm = 152
    
    phi_bearing = 0.65
    Pu_N = gov_react_y * 1000
    A_req_mm2 = Pu_N / (phi_bearing * 0.85 * fc)
    bp_B_mm = max(col_bf_mm + 100, math.ceil(math.sqrt(A_req_mm2) / 50) * 50)
    bp_N_mm = max(col_d_mm + 100, bp_B_mm)
    bp_area_mm2 = bp_B_mm * bp_N_mm
    fp_actual = Pu_N / bp_area_mm2
    fp_allow = phi_bearing * 0.85 * fc
    m_proj = max((bp_N_mm - 0.95 * col_d_mm) / 2, (bp_B_mm - 0.80 * col_bf_mm) / 2)
    Fy_bp = 248
    tp_mm = max(10, math.ceil(m_proj * math.sqrt(2 * fp_actual / Fy_bp)))
    tp_mm = math.ceil(tp_mm / 2) * 2
    
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Column Shape | `{col_label}` (d ≈ {col_d_mm}mm, bf ≈ {col_bf_mm}mm) |")
    report.append(f"| Base Plate Dimensions (B × N) | `{bp_B_mm} mm × {bp_N_mm} mm` |")
    report.append(f"| Base Plate Thickness ($t_p$) | `{tp_mm} mm` |")
    report.append(f"| Actual Bearing Stress | `{fp_actual:.2f} MPa` ≤ `{fp_allow:.2f} MPa` ({'✅' if fp_actual <= fp_allow else '❌'}) |")
    report.append(f"| Anchor Bolts | `4 — 16mm Ø` |\n")
    
    # --- Concrete Pedestal ---
    ped_size_mm = 400
    ped_height_mm = 600
    report.append("### Concrete Pedestal\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dimensions | `{ped_size_mm} mm × {ped_size_mm} mm × {ped_height_mm} mm` |")
    report.append("| Main Reinforcement | `4 — 16mm Ø bars` |")
    report.append("| Lateral Ties | `10mm Ø @ 200mm O.C.` |")
    report.append(f"| Anchor Bolts | `4 — 16mm Ø` (embedded {ped_height_mm - 100}mm) |\n")
    
    # --- Isolated Footing ---
    p_service_kN = gov_react_y / 1.5
    footing_area_m2 = p_service_kN / qa
    footing_size_m = max(1.0, math.ceil(math.sqrt(footing_area_m2) * 10) / 10)
    footing_thick_m = 0.30
    
    report.append("### Isolated Square Footing\n")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dimensions | `{footing_size_m:.1f} m × {footing_size_m:.1f} m × {footing_thick_m:.2f} m` |")
    report.append(f"| Actual Bearing Pressure | `{p_service_kN / footing_size_m**2:.1f} kPa` ≤ `{qa} kPa` ✅ |")
    report.append("| Bottom Reinforcement | `12mm Ø @ 200mm O.C.` (Both Ways) |\n")
    
    # ============================================================
    # 7. STRUCTURAL PLOTS
    # ============================================================
    report.append("## 7. Structural Plots\n")
    
    # Plot gravity-only system
    plots = [
        ('show_structure',     'structure',    'Structure & Applied Loads (Gravity)'),
        ('show_axial_force',   'axial',        'Axial Forces (Gravity)'),
        ('show_displacement',  'displacement', 'Deflection (Gravity)'),
        ('show_reaction_force','reactions',     'Support Reactions (Gravity)'),
    ]
    for method_name, filename, title in plots:
        fig = getattr(ss, method_name)(show=False)
        fig.savefig(os.path.join(images_dir, f'pickleball_{filename}.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)
        report.append(f"#### {title}")
        report.append(f"![{title}](images/pickleball_{filename}.png)\n")
    
    # Plot wind case (highest lateral)
    if lc_data:
        wind_sys = lc_data.get("LC3: Gravity + Wind", {}).get("system")
        if wind_sys:
            wind_plots = [
                ('show_structure',     'wind_structure',  'Structure & Loads (Wind Case)'),
                ('show_axial_force',   'wind_axial',      'Axial Forces (Wind Case)'),
                ('show_reaction_force','wind_reactions',   'Reactions (Wind Case)'),
            ]
            for method_name, filename, title in wind_plots:
                fig = getattr(wind_sys, method_name)(show=False)
                fig.savefig(os.path.join(images_dir, f'pickleball_{filename}.png'), dpi=150, bbox_inches='tight')
                plt.close(fig)
                report.append(f"#### {title}")
                report.append(f"![{title}](images/pickleball_{filename}.png)\n")
    
    # Write
    report_path = os.path.join(output_dir, 'structural_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n✅ Pickleball report generated: output/{project_name}/structural_report.md")
