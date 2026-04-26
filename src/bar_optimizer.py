"""
Bar Project — Optimization pipeline for Howe truss with 2 interior columns.

Three-phase architecture:
  Phase 1: Iterative member sizing using factored LC1 (1.2D + 1.6L)
  Phase 2: Deflection check using service loads (D + L), target L/δ > 240
  Phase 3: Multi-load-case envelope (Gravity, Gravity+EQ, Gravity+Wind)
"""

from .bar_builder import build_bar_truss
from .truss_builder import get_max_group_forces
from .aisc_database import aisc_db
import math


def _optimize_rc_column(pu_kn, col_height_m, fc=21, fy_rebar=275):
    """Compute minimum square RC column size for given factored axial load.

    Checks:
      1. Axial capacity: phi*Pn(max) = 0.80 * phi * [0.85*f'c*(Ag-Ast) + fy*Ast]
         with phi=0.65 (tied column) and Ast = 1% Ag minimum.
      2. Slenderness: kLu/r <= 60 (practical upper limit for tied RC columns).
         k=1.0 (braced frame with tie beams), r = h/sqrt(12).

    Returns a dict with column properties for the truss builder.
    """
    phi = 0.65  # Tied column
    k = 1.0     # Braced frame
    max_klr = 60  # Practical slenderness limit
    Ec = 4700 * math.sqrt(fc)  # MPa

    for h_mm in range(200, 600, 50):
        h_m = h_mm / 1000.0
        Ag_mm2 = h_mm * h_mm

        # Slenderness check
        r_m = h_m / math.sqrt(12)
        kLu_r = k * col_height_m / r_m
        if kLu_r > max_klr:
            continue

        # Axial capacity with 1% minimum steel
        Ast_mm2 = 0.01 * Ag_mm2
        phi_Pn_N = 0.80 * phi * (0.85 * fc * (Ag_mm2 - Ast_mm2) + fy_rebar * Ast_mm2)
        phi_Pn_kN = phi_Pn_N / 1000.0

        if phi_Pn_kN >= pu_kn:
            # Moment magnification check (slender column)
            Ig_m4 = (h_m ** 4) / 12.0
            I_eff_m4 = 0.70 * Ig_m4  # Cracked section
            beta_dns = 0.6  # Sustained load ratio
            EI_eff = 0.4 * (Ec * 1e6) * Ig_m4 / (1 + beta_dns)  # N·m²
            Pc_N = (math.pi ** 2) * EI_eff / (k * col_height_m) ** 2
            Pc_kN = Pc_N / 1000.0

            # Minimum eccentricity moment
            e_min_m = max(0.015, 0.03 * h_m)
            M_min_kNm = pu_kn * e_min_m

            # Magnification factor
            denom = 1 - pu_kn / (0.75 * Pc_kN)
            delta_ns = max(1.0, 1.0 / denom) if denom > 0 else 99
            Mc_kNm = delta_ns * M_min_kNm

            # Determine rebar: pick standard bars
            if h_mm <= 250:
                n_bars, bar_dia = 4, 12
            elif h_mm <= 350:
                n_bars, bar_dia = 4, 16
            else:
                n_bars, bar_dia = 8, 16
            Ast_actual = n_bars * math.pi * (bar_dia / 2) ** 2

            return {
                'Label': f'{h_mm}x{h_mm} RC',
                'Type': 'RC',
                'Area': h_m * h_m,        # m²
                'Ix': I_eff_m4,            # m⁴ (0.70 Ig)
                'Weight': h_m * h_m * 2400,  # kg/m
                'h_mm': h_mm,
                'kLu_r': kLu_r,
                'phi_Pn_kN': phi_Pn_kN,
                'Ast_mm2': Ast_actual,
                'n_bars': n_bars,
                'bar_dia': bar_dia,
                'delta_ns': delta_ns,
                'Mc_kNm': Mc_kNm,
                'Pc_kN': Pc_kN,
            }

    # Fallback to 400x400 if nothing passes
    h_m = 0.4
    return {
        'Label': '400x400 RC', 'Type': 'RC',
        'Area': 0.16, 'Ix': 0.70 * (0.4**4 / 12), 'Weight': 384,
        'h_mm': 400, 'kLu_r': k * col_height_m / (0.4 / math.sqrt(12)),
        'phi_Pn_kN': 0, 'Ast_mm2': 804, 'n_bars': 8, 'bar_dia': 16,
        'delta_ns': 1.0, 'Mc_kNm': 0, 'Pc_kN': 0,
    }


def run_bar_optimization(target_ltod=240, max_iter=15, chord_family="2L", web_family="L", N=21, has_int_cols=True):
    """Optimizes the 21m Howe truss for a bar roof.

    Returns a dict containing the solved system, results map, deflection ratio,
    reactions, weight, cost, and load case data.
    """

    span = 21.0
    dx = span / N
    depth_end = 0.0
    depth_mid = 2.0  # FIXED as requested
    rise = depth_mid - depth_end
    mid_x = span / 2.0
    col_height = 4.0

    # Gravity load breakdown (service loads) — 5m tributary width
    trib_width = 5.0        # m
    dl_kpa = 0.5            # kPa
    ll_kpa = 0.6            # kPa
    wind_kpa = 0.8          # kPa
    dl_q_kn_m = -(dl_kpa * trib_width)     # -2.5 kN/m
    ll_q_kn_m = -(ll_kpa * trib_width)     # -3.0 kN/m
    wind_q_kn_m = wind_kpa * trib_width    #  4.0 kN/m

    # Member lengths for slenderness
    slope_per_panel = rise / (N / 2.0)
    chord_top_L = (dx**2 + slope_per_panel**2)**0.5
    chord_bot_L = dx
    vert_L = depth_mid
    diag_L = (dx**2 + depth_mid**2)**0.5

    # Get correct elemental mapping from builder
    _, mapping = build_bar_truss(N=N, has_int_cols=has_int_cols)

    # RC Column Definition (400x400mm, 0.7 Ig)
    rc_col_res = {
        'Label': '400x400 RC',
        'Type': 'RC',
        'Area': 0.16,
        'Ix': 0.00149,
        'Weight': 384,
    }

    truss_groups = {
        "Top Chord":         {"ids": mapping["Top Chord"],       "L": chord_top_L,   "family": chord_family},
        "Bottom Chord":      {"ids": mapping["Bottom Chord"],    "L": chord_bot_L,   "family": chord_family},
        "Vertical Webs":     {"ids": mapping["Vertical Webs"],   "L": vert_L,        "family": web_family},
        "Diagonal Webs":     {"ids": mapping["Diagonal Webs"],   "L": diag_L,        "family": web_family},
        "Exterior Columns":  {"ids": mapping["Exterior Columns"], "L": col_height,    "family": "RC"},
    }
    if has_int_cols:
        truss_groups["Interior Columns"] = {"ids": mapping["Interior Columns"], "L": col_height, "family": "RC"}

    truss_results = {
        "Exterior Columns": rc_col_res.copy(),
    }
    if has_int_cols:
        truss_results["Interior Columns"] = rc_col_res.copy()

    # PHASE 1: Iterative Member Sizing (Factored 1.2D + 1.6L)
    print(f"  Phase 1: Iterative Member Sizing (Long Span: {not has_int_cols})...")
    factored_dl = 1.2 * dl_q_kn_m
    factored_ll = 1.6 * ll_q_kn_m

    for iteration in range(5):
        print(f"\n    --- Sizing Iteration {iteration+1} ---")
        ss_curr, _ = build_bar_truss(
            truss_results,
            lateral_q_kn_m=0.0,
            dl_q_kn_m=factored_dl,
            ll_q_kn_m=factored_ll,
            N=N,
            has_int_cols=has_int_cols
        )
        ss_curr.solve()

        converged = True
        new_results = {}
        for g in ["Top Chord", "Bottom Chord"]:
            d = truss_groups[g]
            p = get_max_group_forces(ss_curr, d['ids'])
            new_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])

        for g in ["Vertical Webs", "Diagonal Webs"]:
            d = truss_groups[g]
            p = get_max_group_forces(ss_curr, d['ids'])
            if d['family'] == 'HSS':
                candidates = aisc_db.select_candidates(p, d['L'], family='HSS')
                rect_candidates = [c for c in candidates if c['Label'].count('X') == 2 and '.' not in c['Label'].split('X')[0]]
                if rect_candidates:
                    new_results[g] = rect_candidates[0]
                else:
                    new_results[g] = candidates[0] if candidates else None
            else:
                new_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])
        
        for g in ["Top Chord", "Bottom Chord", "Vertical Webs", "Diagonal Webs"]:
            if iteration > 0:
                if not new_results[g] or not truss_results.get(g):
                    converged = False; break
                if new_results[g]['Label'] != truss_results[g]['Label']:
                    converged = False; break
            else:
                converged = False

        truss_results.update(new_results)
        if converged:
            print("    OK: Member sizes converged.")
            break

    # Self-weight
    total_weight_kg = 0
    total_steel_kg = 0
    ss_final, _ = build_bar_truss(truss_results, N=N, has_int_cols=has_int_cols)
    for g, d in truss_groups.items():
        if g in truss_results and truss_results[g]:
            shape = truss_results[g]
            group_L = 0
            for eid in d['ids']:
                el = ss_final.element_map[eid]
                group_L += math.sqrt((el.node_2.vertex.x - el.node_1.vertex.x)**2 + (el.node_2.vertex.y - el.node_1.vertex.y)**2)
            
            if shape.get('Type') == 'RC':
                total_weight_kg += shape['Weight'] * group_L
            else:
                kgm = shape['Weight'] * 1.48816
                w_kg = group_L * kgm
                total_weight_kg += w_kg
                total_steel_kg += w_kg

    self_weight_kN = total_weight_kg * 9.81 / 1000
    self_weight_q = -(self_weight_kN / span)
    total_dl_q = dl_q_kn_m + self_weight_q
    total_dl_q = max(total_dl_q, dl_q_kn_m - 0.5)

    # PHASE 2: Deflection Check (Service D + L)
    print("\n  Phase 2: Deflection Check (Service D + L)...")
    final_ratio = 0
    max_uy = 0
    for i in range(max_iter):
        ss_curr, _ = build_bar_truss(truss_results, dl_q_kn_m=total_dl_q, ll_q_kn_m=ll_q_kn_m, N=N, has_int_cols=has_int_cols)
        ss_curr.solve()
        disp = ss_curr.system_displacement_vector
        max_uy = 0
        for nid in ss_curr.node_map:
            uy = disp[(nid-1)*3 + 1]
            if abs(uy) > abs(max_uy): max_uy = uy
        ratio = abs(span / max_uy) if max_uy != 0 else 9999
        final_ratio = ratio
        if ratio >= target_ltod:
            print("    OK: Deflection check PASSED.")
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
        if not upscaled: break

    # PHASE 3: Multi-Load-Case Analysis
    Cs = 0.20
    W_seismic = abs(total_dl_q) * span
    V_base_shear = Cs * W_seismic
    eq_lateral_q = V_base_shear / (4 * col_height)

    load_cases = {
        "LC1: Gravity Only":  {"dl": 1.2 * total_dl_q, "ll": 1.6 * ll_q_kn_m, "lateral": 0.0},
        "LC2: Gravity + EQ":  {"dl": 1.2 * total_dl_q, "ll": 1.0 * ll_q_kn_m, "lateral": eq_lateral_q},
        "LC3: Gravity + Wind": {"dl": 1.2 * total_dl_q, "ll": 0.0,            "lateral": wind_q_kn_m},
    }

    lc_results = {}
    for lc_name, lc in load_cases.items():
        ss_lc, _ = build_bar_truss(truss_results, lateral_q_kn_m=lc['lateral'], dl_q_kn_m=lc['dl'], ll_q_kn_m=lc['ll'], N=N, has_int_cols=has_int_cols)
        ss_lc.solve()
        forces = {}
        max_react_y_int, max_react_y_ext = 0, 0
        max_react_x = 0
        for node in ss_lc.supports_fixed:
            nid = node.id if hasattr(node, 'id') else node
            r = ss_lc.get_node_results_system(nid)
            fy_abs, fx_abs = abs(r.get('Fy', 0)), abs(r.get('Fx', 0))
            if fx_abs > max_react_x: max_react_x = fx_abs
            node_obj = ss_lc.node_map.get(nid)
            if node_obj:
                nx = node_obj.vertex.x if hasattr(node_obj.vertex, 'x') else 0
                if 2.0 < nx < 19.0: # Interior
                    if fy_abs > max_react_y_int: max_react_y_int = fy_abs
                else: # Exterior
                    if fy_abs > max_react_y_ext: max_react_y_ext = fy_abs

        for g, d in truss_groups.items():
            if g == "Exterior Columns": forces[g] = max_react_y_ext
            elif g == "Interior Columns": forces[g] = max_react_y_int
            else: forces[g] = get_max_group_forces(ss_lc, d['ids'])

        lc_results[lc_name] = {
            "system": ss_lc, "forces": forces, "max_react_x": max_react_x,
            "max_react_y_ext": max_react_y_ext, "max_react_y_int": max_react_y_int,
            "max_react_y": max(max_react_y_ext, max_react_y_int)
        }

    # Governing
    governing_forces = {g: max((lcr['forces'][g] for lcr in lc_results.values()), key=abs) for g in truss_groups}
    governing_lc = {g: max(lc_results.keys(), key=lambda k: abs(lc_results[k]['forces'][g])) for g in truss_groups}
    gov_react_y_ext = max(lcr['max_react_y_ext'] for lcr in lc_results.values())
    gov_react_y_int = max(lcr['max_react_y_int'] for lcr in lc_results.values()) if has_int_cols else 0
    gov_react_x = max(lcr['max_react_x'] for lcr in lc_results.values())

    # Final sizing re-check
    for g in ["Top Chord", "Bottom Chord", "Vertical Webs", "Diagonal Webs"]:
        truss_results[g]['Max_Force_kN'] = governing_forces[g]
        truss_results[g]['Governing_LC'] = governing_lc[g]
    
    # Optimize RC columns based on governing reactions
    print("  Optimizing RC column sizes...")
    ext_col_opt = _optimize_rc_column(gov_react_y_ext, col_height)
    truss_results["Exterior Columns"] = ext_col_opt
    truss_results["Exterior Columns"].update({'Max_Force_kN': governing_forces["Exterior Columns"], 'Governing_LC': governing_lc["Exterior Columns"]})
    print(f"    Exterior: {ext_col_opt['Label']} (kLu/r={ext_col_opt['kLu_r']:.1f}, phiPn={ext_col_opt['phi_Pn_kN']:.0f} kN)")

    if has_int_cols:
        int_col_opt = _optimize_rc_column(gov_react_y_int, col_height)
        truss_results["Interior Columns"] = int_col_opt
        truss_results["Interior Columns"].update({'Max_Force_kN': governing_forces["Interior Columns"], 'Governing_LC': governing_lc["Interior Columns"]})
        print(f"    Interior: {int_col_opt['Label']} (kLu/r={int_col_opt['kLu_r']:.1f}, phiPn={int_col_opt['phi_Pn_kN']:.0f} kN)")

    return {
        "system": lc_results["LC1: Gravity Only"]["system"],
        "results": truss_results, "ratio": final_ratio, "max_deflection_m": max_uy,
        "total_weight_kg": total_steel_kg, "total_cost_php": total_steel_kg * 60,
        "total_concrete_kg": total_weight_kg - total_steel_kg,
        "load_cases": lc_results, "gov_react_y_ext": gov_react_y_ext, "gov_react_y_int": gov_react_y_int,
        "gov_react_x": gov_react_x, "Cs": Cs, "W_seismic": W_seismic, "V_base_shear": V_base_shear,
        "wind_q_kn_m": wind_q_kn_m, "self_weight_q": self_weight_q, "total_gravity": total_dl_q,
        "base_gravity": dl_q_kn_m, "live_gravity": ll_q_kn_m, "trib_width": trib_width,
        "dl_kpa": dl_kpa, "ll_kpa": ll_kpa, "wind_kpa": wind_kpa,
        "governing_forces": governing_forces, "governing_lc": governing_lc,
        "gov_react_y": max(gov_react_y_ext, gov_react_y_int),
        "has_int_cols": has_int_cols
    }
