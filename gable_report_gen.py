import os
import matplotlib.pyplot as plt
import math
from gable_builder import build_gable_frame
from gable_optimizer import run_gable_optimization

def generate_gable_report(gable_data):
    """Generates a structured markdown report for the Gable Roof Analysis."""
    
    os.makedirs('images', exist_ok=True)
    report = ["# Gable Roof Structural Analysis Report\n"]
    
    results = gable_data['results_map']
    reactions = gable_data['reactions']
    span = gable_data['span']
    max_d = gable_data['max_deflection_m']
    
    report.append(f"## 1. Frame Geometry & Loads")
    report.append(f"- **Span:** `{span:.1f} m`")
    report.append(f"- **Column Height:** `{gable_data['height_col']:.1f} m`")
    report.append(f"- **Max Vertical Deflection:** `{max_d*1000:.2f} mm` (Limit: {span/240*1000:.2f} mm)\n")
    
    report.append(f"## 2. Loading Data (NSCP 2015 Combinations)")
    spacing = gable_data.get('spacing', 4.7)
    q_dl_val = 0.9 * spacing
    q_lr_val = 0.6 * spacing
    q_ult = 1.2 * q_dl_val + 1.6 * q_lr_val
    
    report.append(f"- **Frame Spacing:** `{spacing:.1f} m` (Tributary Width)")
    report.append(f"- **Dead Load (DL):** `0.9 kPa \\times {spacing:.1f}m = {q_dl_val:.2f} kN/m`")
    report.append(f"- **Roof Live Load (LR):** `0.6 kPa \\times {spacing:.1f}m = {q_lr_val:.2f} kN/m`")
    report.append(f"- **Governing Combination ($1.2D + 1.6L$):** `{1.2:.1f}({q_dl_val:.2f}) + {1.6:.1f}({q_lr_val:.2f}) = {q_ult:.2f} kN/m` (Applied as UDL)\n")

    report.append("### Optimized Member Selection")
    report.append("| Group | Selected W-Shape | Weight (plf) | Area (in²) | Ix (in⁴) |")
    report.append("| --- | --- | --- | --- | --- |")
    for group in ['Beam', 'Column']:
        shape = results[group]
        report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {shape['Area']:.2f} | {shape['Ix']:.1f} |")
    
    report.append(f"\n- **Total Steel Weight (per frame):** `{gable_data['total_weight_kg']:.1f} kg`")
    report.append(f"- **Estimated Material Cost:** `PHP {gable_data['total_weight_kg'] * 65:,.2f}` (@ PHP 65/kg)\n")

    # --- Foundation Section ---
    report.append("## 2. Foundation Design (Base Plate, Pedestal & Footing)")

    # Reactions
    pu = abs(reactions['Ry']) # Vertical
    hu = abs(reactions['Rx']) # Horizontal
    mu = abs(reactions['Rm']) # Moment

    # --- 2.1 Base Plate Design (AISC Sizing) ---
    # Column is W6-shape, bf ~ 4-6 inches (100-150mm)
    # Assume 300x300mm base plate for W6 column
    bp_b = 300
    bp_n = 300
    bp_t = 16 # mm (Initial assumption)
    
    # Simple thickness check: t = l * sqrt(2*Pu / (0.9*Fy*B*N))
    # l = (300 - 150)/2 = 75mm
    fy_bolt_material = 248 # MPa (A36 equivalent)
    l_cant = (bp_b - 150) / 2.0
    if pu > 0:
        req_t = l_cant * math.sqrt((2 * pu * 1000) / (0.9 * fy_bolt_material * bp_b * bp_n))
        bp_t = max(16, math.ceil(req_t / 2) * 2)

    report.append("### Base Plate Details")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dimensions ($B \\times N$) | `{bp_b}mm x {bp_n}mm` |")
    report.append(f"| Thickness ($t$) | `{bp_t}mm` |")
    report.append(f"| Anchor Bolts | `4 nos. 20mm \\phi A325 Bolts` |")
    report.append(f"| Grout Thickness | `25 mm` |")

    # --- 2.2 Concrete Pedestal ---
    ped_size_mm = 500 # 500x500mm pedestal
    # Reinforcement: 8-16mm bars is standard for this load (~1% Ag)
    report.append(f"\n### Concrete Pedestal")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dimensions | `{ped_size_mm}mm x {ped_size_mm}mm` |")
    report.append(f"| Vertical Load ($P_u$) | `{pu:.2f} kN` |")
    report.append(f"| Vertical Reinforcement | `8 nos. 16mm \\phi Bars` |")
    report.append(f"| Lateral Ties | `10mm \\phi @ 200mm o.c.` |")
    report.append(f"| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |")
    
    # --- 2.3 Isolated Square Footing ---
    # Footing Sizing (Assumed soil bearing = 120 kPa)
    p_service = pu / 1.4 # Rough service load
    req_area = p_service / 120.0
    footing_dim = max(1.5, math.ceil(math.sqrt(req_area) * 10) / 10) # Min 1.5m
    
    # Reinforcement (Simplified: 12mm @ 150mm is common for 1.5m footing)
    report.append(f"\n### Isolated Square Footing")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Dimensions | `{footing_dim:.1f}m x {footing_dim:.1f}m` |")
    report.append(f"| Thickness | `0.40 m` |")
    report.append(f"| Depth of Bottom | `1.50 m below Ground Level` |")
    report.append(f"| Main Reinforcement | `12mm \\phi @ 150mm o.c. (Bottom BW)` |")
    report.append(f"| Soil Bearing Cap | `120 kPa (Assumed)` |")

    # --- Plots ---
    # Re-build for plotting with exact parameters
    ss, ids = build_gable_frame(span, gable_data['height_col'], spacing=gable_data.get('spacing', 4.7), results_map=results)
    ss.solve()
    
    plot_configs = [
        ('gable_structure.png', ss.show_structure, "Frame Structure & Loads"),
        ('axial_force.png', ss.show_axial_force, "Axial Force Diagram"),
        ('shear_force.png', ss.show_shear_force, "Shear Force Diagram"),
        ('bending_moment.png', ss.show_bending_moment, "Bending Moment Diagram"),
        ('displacement.png', ss.show_displacement, "Displacement Plot"),
        ('reactions.png', ss.show_reaction_force, "Reaction Forces")
    ]

    report.append("\n## 3. Visualizations")
    for filename, plot_func, title in plot_configs:
        try:
            fig = plot_func(show=False)
            fig.savefig(f'images/{filename}', dpi=150, bbox_inches='tight')
            plt.close(fig)
            report.append(f"### {title}")
            report.append(f"![{title}](images/{filename})\n")
        except Exception as e:
            report.append(f"*(Plot failed: {title})*\n")

    with open('gable_report.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print("\n✅ Report generated: `gable_report.md`")

if __name__ == "__main__":
    # Run the optimization with user inputs (21m span, 6m height, 4.7m spacing)
    data = run_gable_optimization(span=21.0, height_col=6.0, spacing=4.7)
    generate_gable_report(data)
