import sys

with open(r'c:\Users\Daniel\Downloads\ASEP\src\optimizer.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('def run_pickleball_optimization('):
        break
    new_lines.append(line)

new_func = """def run_pickleball_optimization(target_ltod=240, max_iter=15, chord_family="WT", web_family="L"):
    \"\"\"Optimizes the 24m pickleball truss.
    Implements a two-loop architecture:
    1. Outer Loop: Iteratively sizes members based on factored LC1 (1.2D + 1.6L) forces.
    2. Deflection Loop: Upscales members to meet L/d > 240 using service LC1 (D + L) forces.
    Finally, evaluates multi-load-case envelope.\"\"\"
    
    span = 24.0
    N = 16
    dx = span / N   # 1.5m
    depth = 2.0
    rise = 3.0
    mid = N // 2
    slope_per_panel = rise / mid  # 0.375m rise per panel
    col_height = 6.0
    
    # Gravity load breakdown (Service Loads)
    dl_q_kn_m = -3.0
    ll_q_kn_m = -3.6
    
    wind_q_kn_m = 4.8  # kN/m
    
    chord_L = (dx**2 + slope_per_panel**2)**0.5
    diag_L = (dx**2 + (depth + slope_per_panel)**2)**0.5
    
    truss_groups = {
        "Top Chord":     {"ids": list(range(17, 33)), "L": chord_L, "family": chord_family},
        "Bottom Chord":  {"ids": list(range(1, 17)),  "L": chord_L, "family": chord_family},
        "Vertical Webs": {"ids": list(range(33, 50)), "L": depth,   "family": web_family},
        "Diagonal Webs": {"ids": list(range(50, 66)), "L": diag_L,  "family": web_family},
        "Columns":       {"ids": [-2, -1],            "L": col_height, "family": "W"},
    }
    
    truss_results = {}
    
    print("  Phase 1: Iterative Member Sizing (1.2D + 1.6L)...")
    factored_dl = 1.2 * dl_q_kn_m
    factored_ll = 1.6 * ll_q_kn_m
    
    for iteration in range(5):
        print(f"\\n    --- Sizing Iteration {iteration+1} ---")
        ss_curr, _ = build_pickleball_truss(
            truss_results if iteration > 0 else None, 
            lateral_q_kn_m=0.0, 
            dl_q_kn_m=factored_dl, 
            ll_q_kn_m=factored_ll
        )
        ss_curr.solve()
        
        new_results = {}
        for g in ["Top Chord", "Bottom Chord"]:
            d = truss_groups[g]
            p = get_max_group_forces(ss_curr, d['ids'])
            new_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])
            
        bf_chord = min(
            new_results["Top Chord"].get('bf_in', 999) if new_results["Top Chord"] else 999,
            new_results["Bottom Chord"].get('bf_in', 999) if new_results["Bottom Chord"] else 999
        )
        tw_chord = max(
            new_results["Top Chord"].get('tw_in', 0) if new_results["Top Chord"] else 0,
            new_results["Bottom Chord"].get('tw_in', 0) if new_results["Bottom Chord"] else 0
        )
        bf_max_web = (bf_chord - tw_chord) / 2.0
        
        for g in ["Vertical Webs", "Diagonal Webs"]:
            d = truss_groups[g]
            p = get_max_group_forces(ss_curr, d['ids'])
            
            res = aisc_db.select_lightest(p, d['L'], family=d['family'], bf_max=bf_max_web)
            if res is None and d['family'] == 'L':
                res = aisc_db.select_lightest(p, d['L'], family='2L', bf_max=bf_max_web)
            if res is None:
                res = aisc_db.select_lightest(p, d['L'], family='HSS')  # fallback
            new_results[g] = res
            
        converged = True
        if iteration > 0:
            for g in ["Top Chord", "Bottom Chord", "Vertical Webs", "Diagonal Webs"]:
                if not new_results[g] or not truss_results.get(g):
                    converged = False; break
                if new_results[g]['Label'] != truss_results[g]['Label']:
                    converged = False; break
        else:
            converged = False
            
        truss_results.update(new_results)
        
        for g, res in truss_results.items():
            if res:
                print(f"      {g}: {res['Label']} (bf={res.get('bf_in', 0):.2f}\\")")
                
        if converged:
            print("    ✅ Member sizes converged.")
            break

    total_weight_kg = 0
    for g, d in truss_groups.items():
        if g in truss_results and truss_results[g]:
            plf = truss_results[g]['Weight']
            L_m = d['L']
            count = len(d['ids'])
            weight_lbs = plf * (L_m * 3.28084) * count
            total_weight_kg += weight_lbs * 0.453592
            
    self_weight_kN = total_weight_kg * 9.81 / 1000
    self_weight_q = -(self_weight_kN / span)
    total_dl_q = dl_q_kn_m + self_weight_q
    
    print(f"\\n  Dynamic self-weight: {self_weight_q:.3f} kN/m. Total DL = {total_dl_q:.3f} kN/m")

    print("\\n  Phase 2: Deflection Check (Service D + L)...")
    final_ratio = 0
    max_uy = 0
    for i in range(max_iter):
        ss_curr, _ = build_pickleball_truss(
            truss_results, dl_q_kn_m=total_dl_q, ll_q_kn_m=ll_q_kn_m
        )
        ss_curr.solve()
        
        disp = ss_curr.system_displacement_vector
        max_uy = 0
        for nid in ss_curr.node_map:
            uy = disp[(nid-1)*3 + 1]
            if abs(uy) > abs(max_uy): max_uy = uy
        ratio = abs(span / max_uy) if max_uy != 0 else 9999
        final_ratio = ratio
        print(f"    Iter {i+1:2}: L/d = {ratio:4.0f} (Target > {target_ltod}) | {truss_results['Top Chord']['Label']}")
        if ratio >= target_ltod:
            print("    ✅ Deflection check PASSED.")
            break
            
        upscaled = False
        for g_name in ["Top Chord", "Bottom Chord"]:
            p_max = get_max_group_forces(ss_curr, truss_groups[g_name]['ids'])
            cands = aisc_db.select_candidates(p_max, truss_groups[g_name]['L'], family=truss_groups[g_name]['family'])
            cur_l = truss_results[g_name]['Label']
            idx = next((j for j, c in enumerate(cands) if c['Label'] == cur_l), -1)
            if idx != -1 and idx + 1 < len(cands):
                truss_results[g_name] = cands[idx+1]
                upscaled = True
        if not upscaled:
            print("    ⚠ Max database size reached.")
            break

    bf_chord = min(truss_results["Top Chord"]['bf_in'], truss_results["Bottom Chord"]['bf_in'])
    tw_chord = max(truss_results["Top Chord"].get('tw_in',0), truss_results["Bottom Chord"].get('tw_in',0))
    bf_max_web = (bf_chord - tw_chord) / 2.0

    Cs = 0.20
    W_seismic = abs(total_dl_q) * span
    V_base_shear = Cs * W_seismic
    eq_lateral_q = V_base_shear / (2 * col_height)
    print(f"\\n  Phase 3: Multi-Load-Case Analysis")
    print(f"  Earthquake: W = {W_seismic:.2f} kN, V = {V_base_shear:.2f} kN -> dist={eq_lateral_q:.2f} kN/m")

    load_cases = {
        "LC1: Gravity Only": {
            "dl": 1.2 * total_dl_q, 
            "ll": 1.6 * ll_q_kn_m, 
            "lateral": 0.0
        },
        "LC2: Gravity + EQ": {
            "dl": 1.2 * total_dl_q, 
            "ll": 1.0 * ll_q_kn_m, 
            "lateral": eq_lateral_q
        },
        "LC3: Gravity + Wind": {
            "dl": 1.2 * total_dl_q, 
            "ll": 0.0, 
            "lateral": wind_q_kn_m
        },
    }
    
    lc_results = {}
    for lc_name, lc in load_cases.items():
        ss_lc, _ = build_pickleball_truss(
            truss_results, 
            lateral_q_kn_m=lc['lateral'],
            dl_q_kn_m=lc['dl'],
            ll_q_kn_m=lc['ll']
        )
        ss_lc.solve()
        
        forces = {}
        for g, d in truss_groups.items():
            if g == "Columns":
                max_fy = 0
                for node in ss_lc.supports_fixed:
                    nid = node.id if hasattr(node, 'id') else node
                    r = ss_lc.get_node_results_system(nid)
                    if r and 'Fy' in r and abs(r['Fy']) > abs(max_fy):
                        max_fy = r['Fy']
                forces[g] = abs(max_fy)
            else:
                forces[g] = get_max_group_forces(ss_lc, d['ids'])
                
        max_react_y = 0
        max_react_x = 0
        for node in ss_lc.supports_fixed:
            nid = node.id if hasattr(node, 'id') else node
            r = ss_lc.get_node_results_system(nid)
            if r:
                if 'Fy' in r and abs(r['Fy']) > abs(max_react_y): max_react_y = abs(r['Fy'])
                if 'Fx' in r and abs(r['Fx']) > abs(max_react_x): max_react_x = abs(r['Fx'])
                
        lc_results[lc_name] = {
            "system": ss_lc,
            "forces": forces,
            "max_react_y": max_react_y,
            "max_react_x": max_react_x,
        }

    print("  Computing governing envelope and re-checking capacities...")
    governing_forces = {}
    governing_lc = {}
    for g in truss_groups:
        max_f = 0
        max_lc = ""
        for lc_name, lcr in lc_results.items():
            f = lcr['forces'][g]
            if abs(f) > abs(max_f):
                max_f = f
                max_lc = lc_name
        governing_forces[g] = max_f
        governing_lc[g] = max_lc

    gov_react_y = max(lcr['max_react_y'] for lcr in lc_results.values())
    gov_react_x = max(lcr['max_react_x'] for lcr in lc_results.values())
    gov_react_y_lc = max(lc_results.keys(), key=lambda k: lc_results[k]['max_react_y'])
    gov_react_x_lc = max(lc_results.keys(), key=lambda k: lc_results[k]['max_react_x'])

    for g in ["Top Chord", "Bottom Chord"]:
        gov_force = governing_forces[g]
        cap = truss_results[g].get('Capacity_kN', 0)
        if abs(gov_force) > abs(cap):
            new_sel = aisc_db.select_lightest(gov_force, truss_groups[g]['L'], family=truss_groups[g]['family'])
            if new_sel: truss_results[g] = new_sel

    bf_chord = min(truss_results["Top Chord"]['bf_in'], truss_results["Bottom Chord"]['bf_in'])
    tw_chord = max(truss_results["Top Chord"].get('tw_in',0), truss_results["Bottom Chord"].get('tw_in',0))
    bf_max_web = (bf_chord - tw_chord) / 2.0

    for g in ["Vertical Webs", "Diagonal Webs"]:
        gov_force = governing_forces[g]
        cap = truss_results[g].get('Capacity_kN', 0)
        needs_resize = abs(gov_force) > abs(cap)
        bf_too_wide = truss_results[g].get('bf_in', 0) > bf_max_web
        
        if needs_resize or bf_too_wide:
            d = truss_groups[g]
            new_sel = aisc_db.select_lightest(gov_force, d['L'], family=d['family'], bf_max=bf_max_web)
            if new_sel is None and d['family'] == 'L':
                new_sel = aisc_db.select_lightest(gov_force, d['L'], family='2L', bf_max=bf_max_web)
            if new_sel is None:
                new_sel = aisc_db.select_lightest(gov_force, d['L'], family='HSS')
            if new_sel: truss_results[g] = new_sel

    truss_results["Columns"] = aisc_db.select_lightest(-gov_react_y, truss_groups["Columns"]['L'], family="W")

    total_weight_kg = 0
    for g, d in truss_groups.items():
        if g in truss_results and truss_results[g]:
            plf = truss_results[g]['Weight']
            L_m = d['L']
            count = len(d['ids'])
            weight_lbs = plf * (L_m * 3.28084) * count
            total_weight_kg += weight_lbs * 0.453592
    total_cost_php = total_weight_kg * 60

    for g in truss_groups:
        if truss_results.get(g):
            truss_results[g]['Max_Force_kN'] = governing_forces[g]
            truss_results[g]['Governing_LC'] = governing_lc[g]

    return {
        "system": lc_results["LC1: Gravity Only"]["system"],
        "results": truss_results,
        "ratio": final_ratio,
        "max_deflection_m": max_uy,
        "end_reaction": gov_react_y,
        "total_weight_kg": total_weight_kg,
        "total_cost_php": total_cost_php,
        "load_cases": lc_results,
        "governing_forces": governing_forces,
        "governing_lc": governing_lc,
        "gov_react_y": gov_react_y,
        "gov_react_x": gov_react_x,
        "gov_react_y_lc": gov_react_y_lc,
        "gov_react_x_lc": gov_react_x_lc,
        "Cs": Cs,
        "W_seismic": W_seismic,
        "V_base_shear": V_base_shear,
        "wind_q_kn_m": wind_q_kn_m,
        "self_weight_q": self_weight_q,
        "total_gravity": total_dl_q,
        "base_gravity": dl_q_kn_m,
        "live_gravity": ll_q_kn_m
    }
"""

with open(r'c:\Users\Daniel\Downloads\ASEP\src\optimizer.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    f.write(new_func)
    f.write('\n')
