from anastruct import SystemElements
import math

def get_max_group_forces(system, ids):
    """Safely extracts axial forces from element objects after solve."""
    forces = []
    for eid in ids:
        el = system.element_map.get(eid)
        if el and hasattr(el, 'axial_force') and el.axial_force is not None:
            forces.extend([el.axial_force[0], el.axial_force[1]])
        else:
            forces.append(0)
    return max(forces, key=abs) if forces else 0

def build_longitudinal_truss(results_map=None):
    """Builds the 18.7m longitudinal truss with provided member properties."""
    if results_map is None:
        results_map = {}
        
    ss = SystemElements()
    N, depth, dx, dy = 16, 0.6, 1.16875, 1.0
    dy_per_panel = dy / N
    
    chord_bot_ids, chord_top_ids, web_vert_ids, web_diag_ids = [], [], [], []
    
    def get_props(group_name):
        r = results_map.get(group_name)
        if r:
            return float(r['Area'] * 0.00064516) * 200e9, float(r['Ix'] * 4.1623e-7) * 200e9
        return 0, 0 # anastruct will use defaults if EA=0

    # Bottom Chords
    EA_val, EI_val = get_props("Bottom Chord")
    for i in range(N):
        x1, y1 = i * dx, 4 + i * dy_per_panel
        x2, y2 = (i + 1) * dx, 4 + (i + 1) * dy_per_panel
        if EA_val: chord_bot_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: chord_bot_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))
        
    # Top Chords
    EA_val, EI_val = get_props("Top Chord")
    for i in range(N):
        x1, y1 = i * dx, 4 + depth + i * dy_per_panel
        x2, y2 = (i + 1) * dx, 4 + depth + (i + 1) * dy_per_panel
        if EA_val: chord_top_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: chord_top_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))
        
    # Vertical Webs
    EA_val, EI_val = get_props("Vertical Webs")
    for i in range(N + 1):
        x, y_bot = i * dx, 4 + i * dy_per_panel
        if EA_val: web_vert_ids.append(ss.add_element(location=[[x, y_bot], [x, y_bot + depth]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: web_vert_ids.append(ss.add_truss_element(location=[[x, y_bot], [x, y_bot + depth]]))
        
    # Diagonal Webs
    EA_val, EI_val = get_props("Diagonal Webs")
    for i in range(N):
        x1, y_bot = i * dx, 4 + i * dy_per_panel
        x2, y_top2 = (i + 1) * dx, 4 + depth + (i + 1) * dy_per_panel
        if EA_val: web_diag_ids.append(ss.add_element(location=[[x1, y_bot], [x2, y_top2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: web_diag_ids.append(ss.add_truss_element(location=[[x1, y_bot], [x2, y_top2]]))
        
    # Supports
    # Node at x=0 is hinged
    y_support = 4 + (0.0 / dx) * dy_per_panel
    ss.add_support_hinged(node_id=ss.find_node_id([0.0, y_support]))
    
    # Node at x=18.7 is a roller (allows x expansion)
    y_support = 4 + (18.7 / dx) * dy_per_panel
    ss.add_support_roll(node_id=ss.find_node_id([18.7, y_support]))
    
    mapping = {
        "Top Chord": chord_top_ids, 
        "Bottom Chord": chord_bot_ids, 
        "Vertical Webs": web_vert_ids, 
        "Diagonal Webs": web_diag_ids
    }
    
    # Apply Loads
    for eid in chord_top_ids: 
        ss.q_load(q=-2.3, element_id=eid, direction='y')
    ss.q_load(q=3.2, element_id=chord_bot_ids[0], direction='x')
    
    return ss, mapping

def build_transverse_stiffening_truss(transfer_load_kn=21.5, results_map=None):
    """Builds the transverse stiffening truss and applies reactions from longitudinal trusses."""
    if results_map is None:
        results_map = {}
        
    ts = SystemElements()
    L_trans, N_trans, depth_trans = 20.675, 20, 0.6
    dx_trans = L_trans / N_trans
    
    chord_bot_ids, chord_top_ids, web_vert_ids, web_diag_ids = [], [], [], []
    
    # Elements
    for i in range(N_trans):
        chord_bot_ids.append(ts.add_truss_element(location=[[i*dx_trans, 0], [(i+1)*dx_trans, 0]]))
        chord_top_ids.append(ts.add_truss_element(location=[[i*dx_trans, depth_trans], [(i+1)*dx_trans, depth_trans]]))
    for i in range(N_trans + 1):
        web_vert_ids.append(ts.add_truss_element(location=[[i*dx_trans, 0], [i*dx_trans, depth_trans]]))
    for i in range(N_trans):
        web_diag_ids.append(ts.add_truss_element(location=[[i*dx_trans, 0], [(i+1)*dx_trans, depth_trans]]))
        
    # Supports
    ts.add_support_hinged(node_id=ts.find_node_id([0, 0]))
    ts.add_support_roll(node_id=ts.find_node_id([L_trans, 0]))
    
    # Point Loads (Reactions from longitudinal)
    for i in range(11):
        ts.point_load(Fy=-transfer_load_kn, node_id=ts.find_node_id([i * 2.0675, 0]))
        
    # Apply Member Properties
    mapping = {
        "TS Top Chord": chord_top_ids, 
        "TS Bottom Chord": chord_bot_ids, 
        "TS Vertical Webs": web_vert_ids, 
        "TS Diagonal Webs": web_diag_ids
    }
    
    for g, r in results_map.items():
        if not r: continue
        a, i, e = float(r['Area']*0.00064516), float(r['Ix']*4.1623e-7), 200e9
        for eid in mapping.get(g, []):
            ts.element_map[eid].EA, ts.element_map[eid].EI = a*e, i*e
            
    return ts, mapping

def build_transverse_frame():
    """Builds the simple transverse moment frame."""
    tf = SystemElements()
    num_columns, col_spacing, col_height = 6, 4.135, 5.6
    
    # Columns
    for i in range(num_columns):
        tf.add_element(location=[[i * col_spacing, 0], [i * col_spacing, col_height]], E=200e9, A=0.01)
        
    # Beams
    for k in range(11):
        x1, x2 = k * 2.0675, (k+1) * 2.0675
        if x2 <= 20.675:
            tf.add_element(location=[[x1, col_height], [x2, col_height]], E=200e9, A=0.01)
            
    # Supports
    for i in range(num_columns): 
        tf.add_support_fixed(node_id=tf.find_node_id([i * col_spacing, 0]))
        
    # Point Loads
    for k in range(11): 
        tf.point_load(Fy=-20.32, node_id=tf.find_node_id([k * 2.0675, col_height]))
        
    return tf
