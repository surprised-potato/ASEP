from anastruct import SystemElements
import numpy as np
import math

def build_bar_truss(results_map=None, spacing=4.2, span=20.0, col_height=5.2, truss_depth=0.8, pitch_deg=10.0, N=14):
    """
    Builds a parallel-chord gable truss for the 'Bar' project.
    
    Geometry:
    - 21m Span, N panels.
    - Top chord at 10 deg pitch.
    - Bottom chord parallel (0.8m depth).
    - Eave total height = 6.0m (Column 5.2m + Truss 0.8m).
    """
    ss = SystemElements()
    dx = span / N
    pitch_rad = math.radians(pitch_deg)
    tan_p = math.tan(pitch_rad)
    cos_p = math.cos(pitch_rad)
    
    mid = N // 2
    
    # Load Constants
    q_dl = 0.9 * spacing
    q_lr = 0.6 * spacing
    q_wl = 0.9 * spacing  # Lateral on columns
    
    def get_props(group_name):
        if results_map and group_name in results_map:
            r = results_map[group_name]
            # Convert units: Area (in2 -> m2), Ix (in4 -> m4), E=200GPa
            ea = float(r['Area'] * 0.00064516) * 200e9
            ei = float(r['Ix'] * 4.1623e-7) * 200e9
            return ea, ei
        return 1e12, 1e12 # Default rigid

    ea_chord, ei_chord = get_props('Chords')
    ea_web, ei_web = get_props('Webs')
    ea_col, ei_col = get_props('Columns')

    # 1. Nodes & Elements
    # Bottom Chord Nodes: 0 to N
    # Top Chord Nodes: N+1 to 2N+1
    
    # Bottom Chord
    bc_nodes = []
    for i in range(N + 1):
        x = i * dx
        y_rise = (x if i <= mid else (span - x)) * tan_p
        y = col_height + y_rise
        bc_nodes.append([x, y])
        
    # Top Chord
    tc_nodes = []
    for i in range(N + 1):
        x, y_bc = bc_nodes[i]
        y = y_bc + truss_depth / cos_p
        tc_nodes.append([x, y])
        
    # Elements
    bc_ids = []
    for i in range(N):
        bc_ids.append(ss.add_element(location=[bc_nodes[i], bc_nodes[i+1]], EA=ea_chord, EI=ei_chord))
        
    tc_ids = []
    for i in range(N):
        tc_ids.append(ss.add_element(location=[tc_nodes[i], tc_nodes[i+1]], EA=ea_chord, EI=ei_chord))
        
    v_web_ids = []
    for i in range(N + 1):
        v_web_ids.append(ss.add_element(location=[bc_nodes[i], tc_nodes[i]], EA=ea_web, EI=ei_web))
        
    d_web_ids = []
    for i in range(N):
        # Pratt Truss: Diagonals point towards mid-span (tension under gravity)
        if i < mid:
            # Left side: bottom(i) to top(i+1)
            d_web_ids.append(ss.add_element(location=[bc_nodes[i], tc_nodes[i+1]], EA=ea_web, EI=ei_web))
        else:
            # Right side: top(i) to bottom(i+1)
            d_web_ids.append(ss.add_element(location=[tc_nodes[i], bc_nodes[i+1]], EA=ea_web, EI=ei_web))
            
    # Columns
    # We add columns last. The base nodes will be the new nodes created at (0,0) and (span,0).
    col_l = ss.add_element(location=[[0, 0], bc_nodes[0]], EA=ea_col, EI=ei_col)
    col_r = ss.add_element(location=[[span, 0], bc_nodes[-1]], EA=ea_col, EI=ei_col)
    
    # 2. Supports
    # Find nodes by coordinates to be absolutely sure
    base_l_node = None
    base_r_node = None
    for nid, node in ss.node_map.items():
        if math.isclose(node.vertex.x, 0, abs_tol=1e-3) and math.isclose(node.vertex.y, 0, abs_tol=1e-3):
            base_l_node = nid
        if math.isclose(node.vertex.x, span, abs_tol=1e-3) and math.isclose(node.vertex.y, 0, abs_tol=1e-3):
            base_r_node = nid
            
    if base_l_node: ss.add_support_hinged(node_id=base_l_node)
    if base_r_node: ss.add_support_hinged(node_id=base_r_node)
    
    # 2. Loading (Governing: 1.2D + 1.6L)
    q_comb = 1.2 * q_dl + 1.6 * q_lr
    for eid in tc_ids:
        ss.q_load(q=-q_comb, element_id=eid, direction='y')
        
    # Wind on column
    ss.q_load(q=q_wl, element_id=col_l, direction='x')
    
    return ss, {
        'bc_ids': bc_ids,
        'tc_ids': tc_ids,
        'v_ids': v_web_ids,
        'd_ids': d_web_ids,
        'col_ids': [col_l, col_r],
        'apex_node': mid + 1, # Approx
        'base_nodes': [base_l_node, base_r_node]
    }

def get_max_force(ss, ids):
    forces = [0.0]
    for eid in ids:
        try:
            el = ss.element_map[eid]
            forces.extend([abs(getattr(el, 'N_1', 0.0)), abs(getattr(el, 'N_2', 0.0))])
        except Exception:
            pass
    return max(forces)
