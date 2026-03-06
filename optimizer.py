from truss_builder import (
    build_longitudinal_truss, 
    build_transverse_stiffening_truss, 
    build_transverse_frame,
    get_max_group_forces
)
from aisc_database import aisc_db

def run_longitudinal_optimization(target_ltod=240, max_iter=15, chord_family="WT", web_family="L"):
    """Iteratively upscales chord members until the deflection limit is met."""
    
    # 1. Initial Pass (Default stiffness)
    ss_curr, mapping = build_longitudinal_truss()
    ss_curr.solve()
    
    truss_groups = {
        "Top Chord": {"ids": list(range(17, 33)), "L": 1.17, "family": chord_family},
        "Bottom Chord": {"ids": list(range(1, 17)), "L": 1.17, "family": chord_family},
        "Vertical Webs": {"ids": list(range(33, 50)), "L": 0.60, "family": web_family},
        "Diagonal Webs": {"ids": list(range(50, 66)), "L": 1.31, "family": web_family},
        "Columns": {"ids": [-2, -1], "L": 8.2, "family": "W"}  # Using W-shapes for columns, max unbraced length 8.2m
    }
    
    truss_results = {}
    
    # First: Size Top and Bottom Chords
    for g in ["Top Chord", "Bottom Chord"]:
        d = truss_groups[g]
        p = get_max_group_forces(ss_curr, d['ids'])
        truss_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])
        
    # Get the smallest flange width of the selected chords to constrain the webs
    bf_chord = min(truss_results["Top Chord"].get('bf_in', 999), 
                   truss_results["Bottom Chord"].get('bf_in', 999)) if "Top Chord" in truss_results else 999
    
    # Second: Size Webs, constraining them to be narrower than chords
    for g in ["Vertical Webs", "Diagonal Webs"]:
        d = truss_groups[g]
        p = get_max_group_forces(ss_curr, d['ids'])
        res = aisc_db.select_lightest(p, d['L'], family=d['family'], bf_max=bf_chord)
        
        # Fallback to double angle if single angle fails capacity/geometric width constraints
        if res is None and d['family'] == 'L':
            print(f"Fallback to 2L for {g} due to capacity or width (max bf={bf_chord:.1f} in).")
            res = aisc_db.select_lightest(p, d['L'], family='2L', bf_max=bf_chord)
            
        truss_results[g] = res
        
    print("\n--- DEFLECTION OPTIMIZATION LOOP ---")
    final_ratio = 0
    
    for i in range(max_iter):
        ss_curr, _ = build_longitudinal_truss(truss_results)
        ss_curr.solve()
        
        # Calculate max vertical deflection
        disp = ss_curr.system_displacement_vector
        max_uy = 0
        for nid in ss_curr.node_map:
            uy = disp[(nid-1)*3 + 1]
            if abs(uy) > abs(max_uy): max_uy = uy
                
        ratio = abs(18.7 / max_uy) if max_uy != 0 else 9999
        final_ratio = ratio
        
        print(f"Iter {i+1:2}: L/d = {ratio:4.0f} (Target > {target_ltod}) | {truss_results['Top Chord']['Label']}")
        
        if ratio >= target_ltod:
            print("Deflection check PASSED.")
            break
            
        # Upscale chords if deflection fails
        upscaled = False
        for g_name in ["Top Chord", "Bottom Chord"]:
            p_max = get_max_group_forces(ss_curr, truss_groups[g_name]['ids'])
            cands = aisc_db.select_candidates(p_max, truss_groups[g_name]['L'], family=truss_groups[g_name]['family'])
            
            # Find current selection index and pick the next heaviest
            cur_l = truss_results[g_name]['Label']
            idx = next((j for j, c in enumerate(cands) if c['Label'] == cur_l), -1)
            
            if idx != -1 and idx + 1 < len(cands):
                truss_results[g_name] = cands[idx+1]
                upscaled = True
                
        if not upscaled:
            print("Max database size reached. Cannot satisfy deflection.")
            break
            
    
    # Calculate Max vertical reaction for Column sizing
    max_react_y = 0
    react_nodes = ss_curr.supports_fixed
    for node in react_nodes:
        nid = node.id if hasattr(node, 'id') else node
        r = ss_curr.get_node_results_system(nid)
        if r and 'Fy' in r and abs(r['Fy']) > abs(max_react_y):
            max_react_y = abs(r['Fy'])
            
    # Sizing Columns based on the reaction force
    # Columns are in compression, pass load as negative
    truss_results["Columns"] = aisc_db.select_lightest(-max_react_y, truss_groups["Columns"]['L'], family=truss_groups["Columns"]['family'])
    
    # Ensure forces are captured for the report
    for g, d in truss_groups.items():
        if g == "Columns":
            truss_results[g]['Max_Force_kN'] = -max_react_y
        else:
            truss_results[g]['Max_Force_kN'] = get_max_group_forces(ss_curr, d['ids'])
    
    # Calculate Total Truss Cost
    total_weight_kg = 0
    for g, d in truss_groups.items():
        if g in truss_results and truss_results[g]:
            plf = truss_results[g]['Weight']
            L_m = d['L']
            # IDs correspond to unique members, count them. Columns list is length 2.
            count = len(d['ids'])
            weight_lbs = plf * (L_m * 3.28084) * count
            total_weight_kg += weight_lbs * 0.453592
            
    total_cost_php = total_weight_kg * 60
    avg_reaction_kn = max_react_y
    
    return {
        "system": ss_curr,
        "results": truss_results,
        "ratio": final_ratio,
        "max_deflection_m": max_uy,
        "end_reaction": avg_reaction_kn,
        "total_weight_kg": total_weight_kg,
        "total_cost_php": total_cost_php
    }

def run_transverse_stiffening(transfer_load_kn):
    """Sizes members for the stiffening truss carrying the longitudinal reactions."""
    ts, mapping = build_transverse_stiffening_truss(transfer_load_kn)
    ts.solve()
    
    dx_trans = 20.675 / 20
    depth_trans = 0.6
    
    ts_groups = {
        "TS Top Chord": {"ids": list(range(2, 41, 2)), "L": dx_trans, "family": "HSS"},
        "TS Bottom Chord": {"ids": list(range(1, 41, 2)), "L": dx_trans, "family": "HSS"},
        "TS Vertical Webs": {"ids": list(range(41, 62)), "L": depth_trans, "family": "L"},
        "TS Diagonal Webs": {"ids": list(range(62, 82)), "L": (dx_trans**2 + depth_trans**2)**0.5, "family": "L"}
    }
    
    ts_results = {}
    for g, d in ts_groups.items():
        p = get_max_group_forces(ts, d['ids'])
        ts_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])
        
    ts_final, _ = build_transverse_stiffening_truss(transfer_load_kn, ts_results)
    ts_final.solve()
    
    # Ensure forces are captured for the report
    for g, d in ts_groups.items():
        ts_results[g]['Max_Force_kN'] = get_max_group_forces(ts_final, d['ids'])
    
    return {
        "system": ts_final,
        "results": ts_results
    }

def run_transverse_frame():
    """Solves the final moment frame system."""
    tf = build_transverse_frame()
    tf.solve()
    return {"system": tf}
