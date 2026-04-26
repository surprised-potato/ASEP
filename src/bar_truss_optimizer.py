from src.aisc_database import aisc_db
from src.bar_truss_builder import build_bar_truss, get_max_force
import math
import numpy as np

def run_bar_truss_optimization(spacing=4.2, span=20.0, target_ltod=240, max_iter=10):
    """
    Optimizes the Bar Project Truss (20m span).
    """
    results_map = {} # Initial
    
    # 1. Initial Pass
    ss, ids = build_bar_truss(spacing=spacing)
    ss.solve()
    
    # Define group lengths (rough)
    span = span
    N = 14
    dx = span / N
    pitch = 10.0
    rad = math.radians(pitch)
    cos_p = math.cos(rad)
    truss_depth = 0.8
    
    L_chord = dx / cos_p
    L_v_web = truss_depth / cos_p
    L_d_web = (dx**2 + (truss_depth/cos_p)**2)**0.5
    L_col = 5.2 # Fixed
    
    # 2. Iterative Sizing
    for i in range(max_iter):
        print(f"Iteration {i+1}...")
        ss, ids = build_bar_truss(results_map, spacing=spacing)
        ss.solve()
        
        # Max Vertical Deflection
        disp = ss.system_displacement_vector
        max_uy = 0
        for nid in ss.node_map:
            uy = disp[(nid-1)*3 + 1]
            if abs(uy) > abs(max_uy): max_uy = uy
        
        ratio = abs(span / max_uy) if max_uy != 0 else 9999
        print(f"  L/d = {ratio:.0f}")
        
        # Size Chords - adding local moment check (if any)
        p_bc = get_max_force(ss, ids['bc_ids'])
        p_tc = get_max_force(ss, ids['tc_ids'])
        # Chords are primarily axial, but add optional moment if needed
        new_chord = aisc_db.select_lightest(max(p_bc, p_tc), L_chord, family='WT', Mx_kN_m=0.0)
        
        # Size Webs
        p_v = get_max_force(ss, ids['v_ids'])
        p_d = get_max_force(ss, ids['d_ids'])
        bf_max = new_chord['bf_in'] if new_chord else None
        new_web = aisc_db.select_lightest(max(p_v, p_d), L_d_web, family='2L', bf_max=bf_max, Mx_kN_m=0.0)
            
        # Size Columns (incorporate moment Mu)
        r_y = 0
        m_z = 0
        for nid in ids['base_nodes']:
            res = ss.get_node_results_system(nid)
            if res and 'Fy' in res: r_y = max(r_y, abs(res['Fy']))
            if res and 'Tz' in res: m_z = max(m_z, abs(res['Tz']))
            
        new_col = aisc_db.select_lightest(-r_y, L_col, family='W', Mx_kN_m=m_z)
        
        if results_map.get('Chords') and results_map['Chords']['Label'] == new_chord['Label'] and ratio >= target_ltod:
            print("Converged.")
            break
            
        # If deflection fails, step up chords
        if ratio < target_ltod and i > 2:
            cands = aisc_db.select_candidates(max(p_bc, p_tc), L_chord, family='WT')
            idx = next((j for j, c in enumerate(cands) if c['Label'] == new_chord['Label']), -1)
            if idx != -1 and idx + 1 < len(cands):
                new_chord = cands[idx+1]
        
        results_map = {
            'Chords': new_chord,
            'Webs': new_web,
            'Columns (Ignored/Concrete)': new_col
        }
    
    # 3. Final Calculations (Steel Roof Truss Only)
    total_weight_kg = (new_chord['Weight'] * (2 * N * L_chord) + new_web['Weight'] * (N * L_v_web + N * L_d_web)) * 1.488
    total_cost_php = total_weight_kg * 65

    return {
        'system': ss,
        'results': results_map,
        'max_deflection_m': max_uy,
        'ratio': ratio,
        'spacing': spacing,
        'span': span,
        'total_weight_kg': total_weight_kg,
        'total_cost_php': total_cost_php,
        'geom': {
            'N': N,
            'L_chord': L_chord,
            'L_v_web': L_v_web,
            'L_d_web': L_d_web,
            'L_col': L_col,
            'truss_depth': truss_depth,
            'pitch_deg': pitch,
            'apex_height': L_col + (span / 2.0) * math.tan(rad)
        }
    }
