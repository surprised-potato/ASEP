import os
import matplotlib.pyplot as plt

def generate_markdown_report(longitudinal_data, longitudinal_data_2l, transverse_data, frame_data):
    """Generates a structured markdown report and saves plots."""
    
    # Ensure images directory exists
    os.makedirs('images', exist_ok=True)
    
    report = ["# Structural Optimization Report\n"]
    
    # --- 1. Longitudinal Truss ---
    ss = longitudinal_data['system']
    res = longitudinal_data['results']
    ratio = longitudinal_data['ratio']
    max_d = longitudinal_data['max_deflection_m']
    
    report.append("## 1. Longitudinal Truss (Optimized)\n")
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
        
    # --- 1. Longitudinal Truss Plots ---
    # Structure & Loads
    fig = ss.show_structure(show=False)
    fig.savefig('images/longitudinal_structure.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("\n#### Structure & Applied Loads")
    report.append("![Longitudinal Structure](images/longitudinal_structure.png)\n")
    
    # Axial Forces
    fig = ss.show_axial_force(show=False)
    fig.savefig('images/longitudinal_axial.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Internal Axial Forces")
    report.append("![Longitudinal Axial Forces](images/longitudinal_axial.png)\n")
    
    # Displacement
    fig = ss.show_displacement(show=False)
    fig.savefig('images/longitudinal_displacement.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Deflection Curve")
    report.append("![Longitudinal Displacement](images/longitudinal_displacement.png)\n")

    # Reactions
    fig = ss.show_reaction_force(show=False)
    fig.savefig('images/longitudinal_reactions.png', dpi=150, bbox_inches='tight')
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
    report.append(f"\n- **Max Support Reaction (Vertical):** `{max_react_y_2l:.2f} kN`\n")
    
    # --- 2. Transverse Stiffening Truss ---
    report.append("## 2. Transverse Stiffening Truss\n")
    ts = transverse_data['system']
    ts_res = transverse_data['results']
    
    # Calculate deflection for TS
    disp_ts = ts.system_displacement_vector
    max_ts_d = 0
    if disp_ts is not None:
        for nid in ts.node_map:
            uy = disp_ts[(nid-1)*3 + 1]
            if abs(uy) > abs(max_ts_d): max_ts_d = uy
            
    report.append(f"- **Transfer Load (from Longitudinal):** `{longitudinal_data['end_reaction']:.2f} kN` per node")
    report.append(f"- **Max Deflection:** `{max_ts_d*1000:.2f} mm`\n")
    
    report.append("### Member Selection\n")
    report.append("| Group | Selected Shape | Weight (plf) | KL/r | Max Axial Force (kN) | Capacity (kN) |")
    report.append("| --- | --- | --- | --- | --- | --- |")
    for group, shape in ts_res.items():
        force = shape.get('Max_Force_kN', 0)
        klr = shape.get('KL/r', 0)
        cap = shape.get('Capacity_kN', 0)
        report.append(f"| {group} | `{shape['Label']}` | {shape['Weight']:.1f} | {klr:.1f} | {force:.2f} | {cap:.2f} |")
        
    # TS Plots
    fig = ts.show_structure(show=False)
    fig.savefig('images/transverse_structure.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("\n#### Structure & Applied Loads")
    report.append("![Transverse Structure](images/transverse_structure.png)\n")
    
    fig = ts.show_axial_force(show=False)
    fig.savefig('images/transverse_axial.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Internal Axial Forces")
    report.append("![Transverse Axial Forces](images/transverse_axial.png)\n")
    
    fig = ts.show_displacement(show=False)
    fig.savefig('images/transverse_displacement.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Deflection Curve")
    report.append("![Transverse Displacement](images/transverse_displacement.png)\n")

    fig = ts.show_reaction_force(show=False)
    fig.savefig('images/transverse_reactions.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Support Reactions")
    report.append("![Transverse Reactions](images/transverse_reactions.png)\n")
    
    
    # --- 3. Transverse Momement Frame ---
    report.append("## 3. Transverse Moment Frame\n")
    tf = frame_data['system']
    
    # TF Plots
    fig = tf.show_structure(show=False)
    fig.savefig('images/frame_structure.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("\n#### Structure & Applied Loads")
    report.append("![Frame Structure](images/frame_structure.png)\n")
    
    fig = tf.show_axial_force(show=False)
    fig.savefig('images/frame_axial.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Internal Axial Forces")
    report.append("![Frame Axial Forces](images/frame_axial.png)\n")
    
    fig = tf.show_displacement(show=False)
    fig.savefig('images/frame_displacement.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Deflection Curve")
    report.append("![Frame Displacement](images/frame_displacement.png)\n")
    
    fig = tf.show_reaction_force(show=False)
    fig.savefig('images/frame_reactions.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    report.append("#### Support Reactions")
    report.append("![Frame Reactions](images/frame_reactions.png)\n")
    
    # Write to file
    with open('structural_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
        
    print("\n✅ Report generated successfully: `structural_report.md`")
