from anastruct import SystemElements
import numpy as np
import math

def build_gable_frame(span=21.0, height_col=6.0, pitch_deg=10.0, spacing=4.7, results_map=None):
    """
    Builds a gable frame using anastruct.
    
    Nodes:
    1: (0, 0) - Left Column Base (Support)
    2: (0, height_col) - Left Eave
    3: (span, 0) - Right Column Base (Support)
    4: (span, height_col) - Right Eave
    5: (span/2, apex_height) - Apex
    """
    ss = SystemElements()
    pitch_rad = math.radians(pitch_deg)
    apex_height = height_col + (span / 2.0) * math.tan(pitch_rad)
    
    # Load Constants
    q_dl = 0.9 * spacing # 0.9 kPa * spacing
    q_lr = 0.6 * spacing # 0.6 kPa * spacing (Roof Live Load)
    q_wl = 0.9 * spacing # 0.9 kPa * spacing
    e_seismic = 0.1 * q_dl # 0.423 kN lateral point load proxy or similar
    
    # Stiffness calculation helper
    def get_props(group_name):
        if results_map and group_name in results_map:
            r = results_map[group_name]
            ea = float(r['Area'] * 0.00064516) * 200e9
            ei = float(r['Ix'] * 4.1623e-7) * 200e9
            return ea, ei
        return 1e12, 1e12 # High default stiffness

    ea_col, ei_col = get_props('Column')
    ea_beam, ei_beam = get_props('Beam')

    # Columns (Fixed-Pinned connection logic)
    # n1 (base), n2 (top)
    e_col_l = ss.add_element(location=[[0, 0], [0, height_col]], EA=ea_col, EI=ei_col)
    e_col_r = ss.add_element(location=[[span, 0], [span, height_col]], EA=ea_col, EI=ei_col)

    # Rafters (Gable Beams)
    # n2 (eave_l) to n5 (apex), n5 to n4 (eave_r)
    # Rigid eaves + Pinned Apex (Three-Hinged Arch)
    # spring={2: 0} on e_beam_l means the end (node 5) is pivoted
    # spring={1: 0} on e_beam_r means the start (node 5) is pivoted
    e_beam_l = ss.add_element(location=[[0, height_col], [span/2.0, apex_height]], 
                             EA=ea_beam, EI=ei_beam, spring={2: 0})
    e_beam_r = ss.add_element(location=[[span/2.0, apex_height], [span, height_col]], 
                             EA=ea_beam, EI=ei_beam, spring={1: 0})

    # Supports (Pinned base)
    ss.add_support_hinged(node_id=1) 
    ss.add_support_hinged(node_id=3) 

    # NSCP 2015 Combinations (Governing Gravity case: 1.2D + 1.6Lr)
    q_comb_gravity = 1.2 * q_dl + 1.6 * q_lr
    q_comb_lateral = 1.0 * q_wl # Standard wind factor in LRFD is 1.0
    
    # Loads (kN/m)
    # Apply single governing UDL to rafters
    ss.q_load(q=-q_comb_gravity, element_id=e_beam_l, direction='y')
    ss.q_load(q=-q_comb_gravity, element_id=e_beam_r, direction='y')
    
    # Apply lateral load to column
    ss.q_load(q=q_comb_lateral, element_id=e_col_l, direction='x')
    
    # Note: If wind suction on roof is included, it would be a separate load case or subtracted.
    # To "show only one UDL" as requested, we present the governing downward combination.
    
    # Seismic Load (Point load at eave for simplicity)
    ss.point_load(node_id=2, Fx=e_seismic * (height_col/2.0)) # Crude approximation

    return ss, {
        'column_ids': [e_col_l, e_col_r],
        'beam_ids': [e_beam_l, e_beam_r],
        'apex_node_id': 5,
        'base_node_id': 1
    }

def get_max_axial_force(ss, element_ids):
    """Returns the maximum absolute axial force in the given elements."""
    forces = [0.0]
    for eid in element_ids:
        try:
            res = ss.get_element_results(eid)
            # res can be None or a dict
            if res and isinstance(res, dict) and 'N' in res:
                # N is usually a list/array of 2 values (start, end)
                forces.extend([abs(res['N'][0]), abs(res['N'][1])])
            elif hasattr(ss, 'element_results') and ss.element_results:
                # Fallback to direct attribute access if exist
                er = ss.element_results.get(eid)
                if er and 'N' in er:
                    forces.extend([abs(er['N'][0]), abs(er['N'][1])])
        except Exception as e:
            pass # Silent failure to avoid crashing the loop
    return max(forces)

def get_max_moment(ss, element_ids):
    """Returns the maximum absolute moment in the given elements."""
    moments = [0.0]
    for eid in element_ids:
        try:
            res = ss.get_element_results(eid)
            if res and isinstance(res, dict) and 'M' in res:
                moments.extend([abs(res['M'][0]), abs(res['M'][1])])
            elif hasattr(ss, 'element_results') and ss.element_results:
                er = ss.element_results.get(eid)
                if er and 'M' in er:
                    moments.extend([abs(er['M'][0]), abs(er['M'][1])])
        except Exception as e:
            pass
    return max(moments)
