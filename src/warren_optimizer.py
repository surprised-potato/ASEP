"""
Warren Transfer Truss Optimizer.

Iteratively sizes members for a parallel-chord Warren truss carrying a midspan
point load, then checks deflection against L/360.
"""

from .warren_builder import build_warren_truss
from .truss_builder import get_max_group_forces
from .aisc_database import aisc_db
import math


def run_warren_optimization(point_load_kN, span=10.0, depth=1.4, n_bays=4,
                            chord_family='2L', web_family='L', target_ltod=360, max_iter=10):
    """Optimizes a Warren transfer truss for a midspan point load.

    Args:
        point_load_kN: Factored point load at midspan (kN). Already factored from
                       the main truss analysis (1.2D + 1.6L envelope).
        span: Truss span (m).
        depth: Truss depth (m).
        n_bays: Number of bottom chord bays (even number). Triangular panels = 2*n_bays.
        chord_family: AISC shape family for top and bottom chords ('2L', 'L', etc.).
        web_family: AISC shape family for verticals and diagonals ('L', 'HSS', etc.).
        target_ltod: Deflection limit (L/target_ltod). Default 360 for transfer beam.
        max_iter: Max deflection iterations.

    Returns:
        Dict with results, forces, deflection, and system.
    """
    bay_width = span / n_bays
    half_bay = bay_width / 2.0
    diag_L = math.sqrt(half_bay**2 + depth**2)  # diagonal length for Warren
    chord_L = bay_width
    vert_L = depth

    truss_groups = {
        "Top Chord":     {"L": chord_L, "family": chord_family},
        "Bottom Chord":  {"L": chord_L, "family": chord_family},
        "Verticals":     {"L": vert_L,  "family": web_family},
        "Diagonals":     {"L": diag_L,  "family": web_family},
    }

    all_groups = ["Top Chord", "Bottom Chord", "Verticals", "Diagonals"]
    truss_results = {}

    # ---------------------------------------------------------------
    # PHASE 1: Iterative Member Sizing (using factored point load)
    # ---------------------------------------------------------------
    print(f"\n  Top-Supported Warren Phase 1: Iterative Member Sizing...")
    print(f"    Span={span}m | Depth={depth}m | {n_bays} bays | P={point_load_kN:.1f} kN (factored)")

    for iteration in range(5):
        print(f"\n    --- Sizing Iteration {iteration+1} ---")
        ss_curr, mapping = build_warren_truss(
            results_map=truss_results,
            point_load_kN=point_load_kN,
            span=span, depth=depth, n_bays=n_bays
        )
        ss_curr.solve()

        converged = True
        new_results = {}
        for g in all_groups:
            d = truss_groups[g]
            p = get_max_group_forces(ss_curr, mapping[g])
            new_results[g] = aisc_db.select_lightest(p, d['L'], family=d['family'])

        for g in all_groups:
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

    # ---------------------------------------------------------------
    # PHASE 2: Deflection Check (service load = P / 1.5)
    # ---------------------------------------------------------------
    service_load = point_load_kN / 1.5
    print(f"\n  Top-Supported Warren Phase 2: Deflection Check (P_service={service_load:.1f} kN, target L/{target_ltod})...")

    final_ratio = 0
    max_uy = 0
    for i in range(max_iter):
        ss_curr, mapping = build_warren_truss(
            results_map=truss_results,
            point_load_kN=service_load,
            span=span, depth=depth, n_bays=n_bays
        )
        ss_curr.solve()

        disp = ss_curr.system_displacement_vector
        max_uy = 0
        for nid in ss_curr.node_map:
            uy = disp[(nid - 1) * 3 + 1]
            if abs(uy) > abs(max_uy):
                max_uy = uy

        ratio = abs(span / max_uy) if max_uy != 0 else 9999
        final_ratio = ratio

        if ratio >= target_ltod:
            print(f"    OK: Deflection check PASSED (L/{ratio:.0f}).")
            break

        # Upscale chords
        print(f"    L/{ratio:.0f} < L/{target_ltod} — upsizing chords...")
        upscaled = False
        for g_name in ["Top Chord", "Bottom Chord"]:
            p_max = get_max_group_forces(ss_curr, mapping[g_name])
            cands = aisc_db.select_candidates(p_max, truss_groups[g_name]['L'],
                                              family=truss_groups[g_name]['family'])
            cur_l = truss_results[g_name]['Label']
            idx = next((j for j, c in enumerate(cands) if c['Label'] == cur_l), -1)
            if idx != -1 and idx + 1 < len(cands):
                truss_results[g_name] = cands[idx + 1]
                upscaled = True
        if not upscaled:
            print("    WARN: Cannot upsize further.")
            break

    # ---------------------------------------------------------------
    # Compute final forces and weight
    # ---------------------------------------------------------------
    ss_final, mapping = build_warren_truss(
        results_map=truss_results,
        point_load_kN=point_load_kN,
        span=span, depth=depth, n_bays=n_bays
    )
    ss_final.solve()

    # Extract governing forces
    governing_forces = {}
    for g in truss_groups:
        governing_forces[g] = get_max_group_forces(ss_final, mapping[g])
        truss_results[g]['Max_Force_kN'] = governing_forces[g]
        truss_results[g]['Governing_LC'] = "Transfer Load"

    # Support reactions
    max_react_y = 0
    max_react_x = 0
    for node in ss_final.supports_fixed + ss_final.supports_hinged + ss_final.supports_roll:
        nid = node.id if hasattr(node, 'id') else node
        r = ss_final.get_node_results_system(nid)
        fy_abs = abs(r.get('Fy', 0))
        fx_abs = abs(r.get('Fx', 0))
        if fy_abs > max_react_y:
            max_react_y = fy_abs
        if fx_abs > max_react_x:
            max_react_x = fx_abs

    # Total weight
    total_steel_kg = 0
    for g, d in truss_groups.items():
        shape = truss_results.get(g)
        if shape:
            group_L = 0
            for eid in mapping[g]:
                el = ss_final.element_map[eid]
                group_L += el.l  # use anastruct's stored element length
            kgm = shape['Weight'] * 1.48816  # plf -> kg/m
            total_steel_kg += group_L * kgm

    return {
        "system": ss_final,
        "results": truss_results,
        "mapping": mapping,
        "ratio": final_ratio,
        "max_deflection_m": max_uy,
        "total_weight_kg": total_steel_kg,
        "governing_forces": governing_forces,
        "point_load_kN": point_load_kN,
        "service_load_kN": service_load,
        "max_react_y": max_react_y,
        "max_react_x": max_react_x,
        "span": span,
        "depth": depth,
        "n_panels": n_bays * 2,
        "chord_family": chord_family,
        "web_family": web_family,
    }
