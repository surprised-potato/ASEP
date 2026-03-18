import os
import matplotlib.pyplot as plt
import math

# Resolve project root (one level up from src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generate_markdown_report(longitudinal_data, longitudinal_data_2l, frame_data, project_name="default"):
    """Generates a structured markdown report and saves plots into output/<project_name>/."""
    
    # Per-project output directories
    output_dir = os.path.join(_PROJECT_ROOT, 'output', project_name)
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    report = ["# Structural Optimization Report\n"]
    
    # --- 1. Longitudinal Truss ---
    ss = longitudinal_data['system']
    res = longitudinal_data['results']
    ratio = longitudinal_data['ratio']
    max_d = longitudinal_data['max_deflection_m']
    
    report.append("## 1. Longitudinal Truss (WT Chords, Single Angle Webs)\n")
    report.append(f"- **Max Deflection:** `{max_d*1000:.2f} mm`")
    
    status = "✅ PASS" if ratio >= 240 else "❌ FAIL"
    report.append(f"- **Deflection Ratio (L/d):** `{ratio:.0f}` (Target > 240) {status}\n")
    
    report.append("### Optimized Member Selection\n")
    report.append("| Group | Selected Shape | Weight (plf) | KL/r | Max Axial Force (kN) | Capacity (kN) |")
    report.append("| --- | --- | --- | --- | --- | --- |")
    for group, shape in res.items():
        force = shape.get('Max_Force_kN', 0)
        klr = shape.get('KL/r', 0)
        cap = shape.get('Capacity_kN', 0)
        report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {klr:.1f} | {force:.2f} | {cap:.2f} |")
        
    # Extract longitudinal reactions
    react_nodes = ss.supports_roll + ss.supports_fixed + ss.supports_hinged + ss.supports_spring_y
    max_react_y = 0
    for node in react_nodes:
        # Some versions of anastruct return Node objects, some return IDs. Handle both safely.
        nid = node.id if hasattr(node, 'id') else node
        r = ss.get_node_results_system(nid)
        if r and 'Fy' in r and abs(r['Fy']) > abs(max_react_y):
            max_react_y = r['Fy']
    report.append(f"\n- **Max Support Reaction (Vertical):** `{max_react_y:.2f} kN`")
    report.append(f"- **Total Truss Weight:** `{longitudinal_data.get('total_weight_kg', 0):.1f} kg`")
    report.append(f"- **Estimated Material Cost:** `PHP {longitudinal_data.get('total_cost_php', 0):,.2f}` (@ PHP 60/kg)")
        
    # --- 1. Longitudinal Truss Plots ---
    # Structure & Loads
    fig = ss.show_structure(show=False)
    fig.savefig(os.path.join(images_dir, 'longitudinal_structure.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("\n#### Structure & Applied Loads")
    report.append("![Longitudinal Structure](images/longitudinal_structure.png)\n")
    
    # Axial Forces
    fig = ss.show_axial_force(show=False)
    fig.savefig(os.path.join(images_dir, 'longitudinal_axial.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Internal Axial Forces")
    report.append("![Longitudinal Axial Forces](images/longitudinal_axial.png)\n")
    
    # Displacement
    fig = ss.show_displacement(show=False)
    fig.savefig(os.path.join(images_dir, 'longitudinal_displacement.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Deflection Curve")
    report.append("![Longitudinal Displacement](images/longitudinal_displacement.png)\n")

    # Reactions
    fig = ss.show_reaction_force(show=False)
    fig.savefig(os.path.join(images_dir, 'longitudinal_reactions.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Support Reactions")
    report.append("![Longitudinal Reactions](images/longitudinal_reactions.png)\n")
    
    # --- 1B. Longitudinal Truss (Double Angle Alternative) ---
    ss_2l = longitudinal_data_2l['system']
    res_2l = longitudinal_data_2l['results']
    ratio_2l = longitudinal_data_2l['ratio']
    max_d_2l = longitudinal_data_2l['max_deflection_m']
    
    report.append("## 1B. Longitudinal Truss (Alternative Double Angle Chords)\n")
    report.append(f"- **Max Deflection:** `{max_d_2l*1000:.2f} mm`")
    
    status_2l = "✅ PASS" if ratio_2l >= 240 else "❌ FAIL"
    report.append(f"- **Deflection Ratio (L/d):** `{ratio_2l:.0f}` (Target > 240) {status_2l}\n")
    
    report.append("### Alternative Member Selection (Double Angles)\n")
    report.append("| Group | Selected Shape | Weight (plf) | KL/r | Max Axial Force (kN) | Capacity (kN) |")
    report.append("| --- | --- | --- | --- | --- | --- |")
    for group, shape in res_2l.items():
        force = shape.get('Max_Force_kN', 0)
        klr = shape.get('KL/r', 0)
        cap = shape.get('Capacity_kN', 0)
        report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {klr:.1f} | {force:.2f} | {cap:.2f} |")
        
    # Extract longitudinal reactions for 2L
    react_nodes_2l = ss_2l.supports_roll + ss_2l.supports_fixed + ss_2l.supports_hinged + ss_2l.supports_spring_y
    max_react_y_2l = 0
    for node in react_nodes_2l:
        nid = node.id if hasattr(node, 'id') else node
        r = ss_2l.get_node_results_system(nid)
        if r and 'Fy' in r and abs(r['Fy']) > abs(max_react_y_2l):
            max_react_y_2l = r['Fy']
    report.append(f"\n- **Max Support Reaction (Vertical):** `{max_react_y_2l:.2f} kN`")
    report.append(f"- **Total Truss Weight:** `{longitudinal_data_2l.get('total_weight_kg', 0):.1f} kg`")
    report.append(f"- **Estimated Material Cost:** `PHP {longitudinal_data_2l.get('total_cost_php', 0):,.2f}` (@ PHP 60/kg)\n")
    # --- 1C. Alternative Substructure (Concrete Square Column & Footing) ---
    report.append("## 1C. Alternative Substructure (Concrete Square Column & Isolated Footing)\n")
    
    # Concrete Column sizing
    col_height_m = 8.2
    # Rule of thumb for unbraced concrete column slenderness (L/h <= 30) -> minimum h = 8.2 / 30 = 273mm -> Round up to 300mm
    conc_col_size_mm = 300
    
    # Eccentricity moment calculation
    # Assume the truss sits on the inner half of the column or bracket
    # Minimum eccentricity e = 15mm + 0.03h ~ 24mm or physical half width (150mm)
    eccentricity_m = (conc_col_size_mm / 2.0) / 1000.0  # Assumes load is applied at the face/edge of the column
    moment_kNm = abs(max_react_y_2l) * eccentricity_m
    
    # Footing sizing (Assumed allowable soil bearing = 100 kPa)
    # P_service ~ max_react_y_2l / 1.5 (approximate unfactored load)
    p_service_kN = abs(max_react_y_2l) / 1.5
    footing_area_req_m2 = p_service_kN / 100.0
    footing_size_m = max(1.0, math.ceil(math.sqrt(footing_area_req_m2) * 10) / 10) # Minimum 1.0m x 1.0m
    footing_thick_m = 0.3 # Typical minimum
    
    report.append("Based on the maximum vertical support reaction and an 8.2m unbraced column height, the following alternative concrete substructure is proposed:\n")
    
    report.append("### Concrete Square Column Option")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |")
    report.append(f"| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |")
    report.append(f"| Target Axial Load ($P_u$) | `{abs(max_react_y_2l):.2f} kN` |")
    report.append(f"| Target Moment ($M_u$) | `{moment_kNm:.2f} kN-m` (Assumed $e={eccentricity_m*1000:.0f}mm$) |")
    report.append(f"| Dimensions | `{conc_col_size_mm} mm x {conc_col_size_mm} mm` |")
    report.append("| Main Reinforcement | `4 - 20mm Ø bars` (To meet minimum 1% $A_s$) |")
    report.append("| Lateral Ties | `10mm Ø @ 300mm O.C.` |\n")
    
    report.append("### Isolated Square Footing Option")
    report.append("| Parameter | Value |")
    report.append("| --- | --- |")
    report.append(f"| Concrete Strength ($f'_c$) | `21 MPa (3000 psi)` |")
    report.append(f"| Rebar Yield Strength ($f_y$) | `275 MPa (Grade 40)` |")
    report.append("| Assumed Allowable Soil Bearing | `100 kPa` |")
    report.append(f"| Dimensions (L x W x T) | `{footing_size_m:.1f}m x {footing_size_m:.1f}m x {footing_thick_m:.2f}m` |")
    report.append("| Bottom Reinforcement | `12mm Ø @ 200mm O.C.` (Both Ways) |\n")



    # --- 2. Transverse Momement Frame ---
    report.append("## 2. Transverse Moment Frame\n")
    tf = frame_data['system']
    
    # TF Plots
    fig = tf.show_structure(show=False)
    fig.savefig(os.path.join(images_dir, 'frame_structure.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("\n#### Structure & Applied Loads")
    report.append("![Frame Structure](images/frame_structure.png)\n")
    
    fig = tf.show_axial_force(show=False)
    fig.savefig(os.path.join(images_dir, 'frame_axial.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Internal Axial Forces")
    report.append("![Frame Axial Forces](images/frame_axial.png)\n")
    
    fig = tf.show_displacement(show=False)
    fig.savefig(os.path.join(images_dir, 'frame_displacement.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Deflection Curve")
    report.append("![Frame Displacement](images/frame_displacement.png)\n")
    
    fig = tf.show_reaction_force(show=False)
    fig.savefig(os.path.join(images_dir, 'frame_reactions.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Support Reactions")
    report.append("![Frame Reactions](images/frame_reactions.png)\n")
    
    # Write to file
    report_path = os.path.join(output_dir, 'structural_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
        
    print("\n✅ Report generated successfully: `structural_report.md`")
