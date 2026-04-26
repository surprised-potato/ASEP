from src.aisc_database import aisc_db
from gable_builder import build_gable_frame, get_max_axial_force, get_max_moment
import math

def run_gable_optimization(span=20.0, height_col=6.0, pitch_deg=10.0, spacing=4.2, target_ltod=240, max_iter=10):
    """
    Iteratively optimizes the gable frame members (W-shapes).
    Assumes Beam and Column use W-shapes.
    """
    results_map = {
        'Beam': {'Label': 'Initial', 'Area': 20.0, 'Ix': 500.0, 'Weight': 50.0},
        'Column': {'Label': 'Initial', 'Area': 20.0, 'Ix': 500.0, 'Weight': 50.0}
    }
    
    print(f"Starting Gable Optimization (Span={span}m)...")
    
    for i in range(max_iter):
        print(f"Iteration {i+1}...")
        ss, ids = build_gable_frame(span, height_col, pitch_deg, spacing, results_map)
        ss.solve()
        
        # 1. Extract Forces
        pu_col = get_max_axial_force(ss, ids['column_ids'])
        pu_beam = get_max_axial_force(ss, ids['beam_ids'])
        mu_col = get_max_moment(ss, ids['column_ids'])
        mu_beam = get_max_moment(ss, ids['beam_ids'])
        
        # Approximate combined stress for sizing: P/A + M/S <= 0.9Fy
        # For choosing lightest, we use capacity check from aisc_db
        # But we need to handle moment. Let's increase Pu for rough selection.
        # Equivalent Pu = Pu + (Mu * 12 / depth_approx)
        
        # Rigorous sizing using interaction checks
        new_col = aisc_db.select_lightest(pu_col, height_col, family='W', Mx_kN_m=mu_col)
        # Beam length is eave to apex
        pitch_rad = math.radians(pitch_deg)
        beam_len = (span / 2.0) / math.cos(pitch_rad)
        new_beam = aisc_db.select_lightest(pu_beam, beam_len, family='W', Mx_kN_m=mu_beam)
        
        if not new_col or not new_beam:
            print("Failed to find suitable I-beams.")
            break
            
        # 2. Check Deflection
        # Apex Vertical Deflection
        results = ss.get_node_results_system(ids['apex_node_id'])
        print(f"DEBUG: Node results for apex={ids['apex_node_id']}: {results}")
        # results can be dict {'ux':val, 'uy':val, 'phi_z':val} or list [ux, uy, phi_z]
        if isinstance(results, dict):
            dy_m = abs(results.get('uy', 0.0))
        elif isinstance(results, (list, np.ndarray)):
            dy_m = abs(results[1])
        else:
            dy_m = 0.0
            
        delta_max = span / target_ltod
        
        print(f"  Max Deflection: {dy_m*1000:.2f} mm (Limit: {delta_max*1000:.2f} mm)")
        
        if dy_m <= delta_max and i > 0:
            # Stability check: ensure we didn't just pick something too small
            # If current label is same as previous, we converged
            if new_col['Label'] == results_map['Column']['Label'] and new_beam['Label'] == results_map['Beam']['Label']:
                print("Converged.")
                break
        
        # Upgrade if deflection fails
        if dy_m > delta_max:
            # Step up Ix by 20% to find next candidates
            target_ix_beam = results_map['Beam']['Ix'] * 1.2
            candidates = aisc_db.select_candidates(pu_beam, beam_len, family='W', Mx_kN_m=mu_beam)
            passing_ix = [c for c in candidates if c['Ix'] > target_ix_beam]
            if passing_ix:
                new_beam = passing_ix[0]
            
        results_map['Beam'] = new_beam
        results_map['Column'] = new_col

    # Final Reactions for foundation
    results = ss.get_node_results_system(ids['base_node_id']) # Left base
    if isinstance(results, dict):
        rx = abs(results.get('Fx', 0.0))
        ry = abs(results.get('Fy', 0.0))
        rm = abs(results.get('Tz', 0.0))
    elif isinstance(results, (list, np.ndarray)):
        rx = abs(results[0])
        ry = abs(results[1])
        rm = abs(results[2])
    else:
        rx, ry, rm = 0.0, 0.0, 0.0
    
    return {
        'results_map': results_map,
        'max_deflection_m': dy_m,
        'span': span,
        'height_col': height_col,
        'spacing': spacing,
        'reactions': {'Rx': rx, 'Ry': ry, 'Rm': rm},
        'total_weight_kg': (new_col['Weight'] * 2 * height_col + new_beam['Weight'] * 2 * beam_len) * 1.488
    }

if __name__ == "__main__":
    res = run_gable_optimization(span=20.0, height_col=6.0, spacing=4.2)
    print(res)
