import os
import matplotlib.pyplot as plt
from src.bar_truss_optimizer import run_bar_truss_optimization

def generate_building_truss_report(data_int, project_name="bar"):
    output_dir = f"output/{project_name}"
    images_dir = f"{output_dir}/images"
    os.makedirs(images_dir, exist_ok=True)
    
    geom = data_int['geom']
    N = geom['N']
    
    report = [f"# Modified Truss & CHB Gable Structure - Project: {project_name}\n"]
    
    report.append(f"## 1. Global Building Parameters")
    report.append(f"- **Building Span:** `{data_int['span']:.1f} m`")
    report.append(f"- **Total Bays:** `6 bays` @ `{data_int['spacing']:.1f} m` spacing")
    report.append(f"- **Main Steel Frames:** `5 Interior Trusses` (4.2m Tributary Width)")
    report.append(f"- **Gable Ends:** `2 Reinforced CHB Walls` (Bearing 2.1m Tributary Width)")
    report.append(f"- **Roof Pitch:** `{geom['pitch_deg']:.1f} degrees`")
    report.append(f"- **Truss Depth (Parallel):** `{geom['truss_depth']:.2f} m`")
    report.append(f"- **Apex Height (Total):** `{geom['apex_height']:.2f} m`")
    report.append(f"- **Column/Eave Height:** `{geom['L_col']:.2f} m`")
    report.append(f"- **Number of Panels:** `{geom['N']}` (Per Top/Bottom Chord)\n")
    
    report.append("## 2. Interior Roof Truss Member Selection (AISC Chapter H)")
    report.append(f"- **Max Deflection:** `{abs(data_int['max_deflection_m'])*1000:.2f} mm`")
    report.append("| Group | Selected Shape | Weight (plf) | Area (in²) | Interaction Ratio |")
    report.append("| --- | --- | --- | --- | --- |")
    for group, shape in data_int['results'].items():
        if "Columns" not in group:
            report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {shape['Area']:.2f} | {shape['Capacity_Ratio']:.2f} |")
        
    num_int = 5
    total_building_weight = num_int * data_int['total_weight_kg']
    total_building_cost = total_building_weight * 65

    report.append(f"\n- **Total Building Steel Weight (5 Trusses):** `{total_building_weight:,.1f} kg`")
    report.append(f"- **Estimated Steel Material Cost:** `PHP {total_building_cost:,.2f}` (@ PHP 65/kg)")
    report.append("*(Note: Cost excludes the front & rear concrete gable walls)*\n")
    
    report.append("## 3. Global Steel Truss Cutting List (5 Trusses)")
    report.append("| Component | Shape | L per Piece (m) | Qty per Truss | Total Building Qty | Total Length (m) |")
    report.append("| --- | --- | --- | --- | --- | --- |")
    
    l_c = geom['L_chord']
    l_v = geom['L_v_web']
    l_d = geom['L_d_web']
    l_col = geom['L_col']
    t_res = data_int['results']
    
    qty_c = 2 * N
    report.append(f"| Top/Bot Chords | `{t_res['Chords']['Label']}` | {l_c:.3f} | {qty_c} | {qty_c * num_int} | {l_c * qty_c * num_int:.2f} |")
    qty_v = N + 1
    report.append(f"| Vertical Webs | `{t_res['Webs']['Label']}` | {l_v:.3f} | {qty_v} | {qty_v * num_int} | {l_v * qty_v * num_int:.2f} |")
    qty_d = N
    report.append(f"| Diagonal Webs | `{t_res['Webs']['Label']}` | {l_d:.3f} | {qty_d} | {qty_d * num_int} | {l_d * qty_d * num_int:.2f} |")

    report.append("\n## 4. Front & Rear CHB Gable Wall Specification")
    report.append("The 2 end steel trusses have been omitted in favor of structural Concrete Hollow Block (CHB) walls that directly carry the roof purlins and resist lateral wind loads across the 20m span.\n")
    report.append("### RC Column Layout (Vertical Supports)")
    report.append("- **Quantity:** `6 structural concrete columns` per gable wall.")
    report.append("- **Spacing:** Maximum `4.0 m` horizontal spacing between columns.")
    report.append("- **Column Sizing:** All gable wall columns to be `200mm x 350mm` reinforced with `8 pcs 16mm \phi` vertical rebars.")
    report.append("\n### RC Beam Layout (Horizontal Supports)")
    report.append("- **Mid-Height Tie Beam:** Continuous `150mm x 300mm` beam at approx `2.8m - 3.0m` height to break the unbraced CHB vertical span.")
    report.append("- **Sloped Gable Roof Beam:** Continuous `200mm x 400mm` boundary beam tracing the 10-degree roof slope (from 5.2m eave up to 6.96m apex).")
    report.append("  - **Main Reinforcement:** `6 pcs 16mm \phi` continuous long bars (3 top, 3 bottom).")
    report.append("  - **Stirrups:** `10mm \phi` ties spaced at `100mm` near columns and `200mm` at midspan.")
    report.append("  - **Embedment:** Purlin cleats/plates must be embedded here at `0.60m` max spacing.\n")
    
    report.append("## 5. Visualizations (Interior Truss)")
    
    plots = [
        ('truss_structure.png', data_int['system'].show_structure, "Truss Structure & Loads"),
        ('truss_axial.png', data_int['system'].show_axial_force, "Axial Force Diagram"),
        ('truss_bending.png', data_int['system'].show_bending_moment, "Bending Moment Diagram"),
        ('truss_displacement.png', data_int['system'].show_displacement, "Displacement Plot"),
        ('truss_reactions.png', data_int['system'].show_reaction_force, "Reaction Forces")
    ]
    
    for filename, func, title in plots:
        fig = func(show=False)
        fig.savefig(f"{images_dir}/{filename}", dpi=150, bbox_inches='tight')
        plt.close(fig)
        report.append(f"### {title}")
        report.append(f"![{title}](images/{filename})\n")
        
    report.append("\n## 6. 3D Bracing Requirements (5-Truss System)")
    report.append("To ensure global stability out-of-plane for the 6-bay building, the following bracing is required:")
    report.append("- **Roof Purlins (Top Chord Bracing):** `LC 150x50x20x1.5mm` spaced at max `0.60m` attached to truss chords and the CHB Gable Beam.")
    report.append("- **Bottom Chord Kickers (Uplift Bracing):** `L2X2X1/4` angle kickers installed every `3.0m` along the internal truss bottom chords.")
    report.append("- **Longitudinal Roof X-Bracing:** `16mm \phi` sag rods spanning across the roof plane in the 2nd and 5th bays (adjacent to the stiff CHB gable walls).")
    report.append("- **Sidewall Vertical X-Bracing:** `20mm \phi` rods or `L2X2X1/4` angles in the 2nd and 5th wall bays to transfer longitudinal shear.")
    report.append("- **Eave Struts:** Continuous longitudinal members connecting the RC columns to the rigid CHB corner columns.\n")

    with open(f"{output_dir}/truss_report.md", 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
    
    print(f"✅ Modified building truss report generated: {output_dir}/truss_report.md")

if __name__ == "__main__":
    print("Running Bar Project Truss Analysis (5 Interior Trusses)...")
    data_int = run_bar_truss_optimization(spacing=4.2, span=20.0)
    generate_building_truss_report(data_int)
