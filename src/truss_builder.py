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
    y_base = 7.2
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
        x1, y1 = i * dx, y_base + i * dy_per_panel
        x2, y2 = (i + 1) * dx, y_base + (i + 1) * dy_per_panel
        if EA_val: chord_bot_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: chord_bot_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))
        
    # Top Chords
    EA_val, EI_val = get_props("Top Chord")
    for i in range(N):
        x1, y1 = i * dx, y_base + depth + i * dy_per_panel
        x2, y2 = (i + 1) * dx, y_base + depth + (i + 1) * dy_per_panel
        if EA_val: chord_top_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: chord_top_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))
        
    # Vertical Webs
    EA_val, EI_val = get_props("Vertical Webs")
    for i in range(N + 1):
        x, y_bot = i * dx, y_base + i * dy_per_panel
        if EA_val: web_vert_ids.append(ss.add_element(location=[[x, y_bot], [x, y_bot + depth]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: web_vert_ids.append(ss.add_truss_element(location=[[x, y_bot], [x, y_bot + depth]]))
        
    # Diagonal Webs
    EA_val, EI_val = get_props("Diagonal Webs")
    for i in range(N):
        x1, y_bot = i * dx, y_base + i * dy_per_panel
        x2, y_top2 = (i + 1) * dx, y_base + depth + (i + 1) * dy_per_panel
        if EA_val: web_diag_ids.append(ss.add_element(location=[[x1, y_bot], [x2, y_top2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else: web_diag_ids.append(ss.add_truss_element(location=[[x1, y_bot], [x2, y_top2]]))
        
    # Columns replacing hinged/roller supports
    col_EA, col_EI = get_props("Columns")
    if not col_EA:
        col_EA = 0.01 * 200e9
        col_EI = 0.0001 * 200e9
        
    col_ids = []
    
    # Left short column (7.2m)
    col_ids.append(ss.add_element(location=[[0.0, 0.0], [0.0, 7.2]], EA=col_EA, EI=col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([0.0, 0.0]))
    
    # Right tall column (8.2m) - truss goes to exactly 18.7 horizontally
    col_ids.append(ss.add_element(location=[[18.7, 0.0], [18.7, 8.2]], EA=col_EA, EI=col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([18.7, 0.0]))
    
    mapping = {
        "Top Chord": chord_top_ids, 
        "Bottom Chord": chord_bot_ids, 
        "Vertical Webs": web_vert_ids, 
        "Diagonal Webs": web_diag_ids,
        "Columns": col_ids
    }
    
    # Apply Loads
    for eid in chord_top_ids: 
        ss.q_load(q=-4.6, element_id=eid, direction='y') # Doubled from -2.3 due to doubled tributary width
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
    
    # Point Loads (Reactions from longitudinal trusses placed at columns only)
    for i in range(6):
        ts.point_load(Fy=-transfer_load_kn, node_id=ts.find_node_id([i * 4.135, 0]))
        
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
    for k in range(5):
        x1, x2 = k * col_spacing, (k+1) * col_spacing
        tf.add_element(location=[[x1, col_height], [x2, col_height]], E=200e9, A=0.01)
            
    # Supports
    for i in range(num_columns): 
        tf.add_support_fixed(node_id=tf.find_node_id([i * col_spacing, 0]))
        
    # Point Loads (Load doubled from -20.32 due to doubled tributary width)
    for k in range(num_columns): 
        tf.point_load(Fy=-40.64, node_id=tf.find_node_id([k * col_spacing, col_height]))
        
    return tf

def build_pickleball_truss(results_map=None, lateral_q_kn_m=0.0, dl_q_kn_m=0.0, ll_q_kn_m=0.0, N=16):
    """Builds a 24m two-slope (gable) Pratt truss for a pickleball court roof.
    
    Geometry: N panels (default 16) = 24m span, 2.0m depth (constant), 3.0m center rise.
    Supports: 6m fixed-base steel columns.
    Loading: dl_q_kn_m (Dead Load) and ll_q_kn_m (Live Load) applied to top chord.
    Optional: lateral_q_kn_m — lateral distributed load on columns (kN/m, +ve = rightward).
    """
    if results_map is None:
        results_map = {}
        
    ss = SystemElements()
    span = 24.0     # total span (m)
    depth = 2.0     # truss depth (m) — constant between chords
    rise = 3.0      # center rise (m) at midspan
    dx = span / N   # panel width
    mid = N // 2    # midspan panel index
    
    chord_bot_ids, chord_top_ids, web_vert_ids, web_diag_ids = [], [], [], []
    
    def get_props(group_name):
        r = results_map.get(group_name)
        if r:
            return float(r['Area'] * 0.00064516) * 200e9, float(r['Ix'] * 4.1623e-7) * 200e9
        return 0, 0
    
    def y_bot(panel_idx):
        """Bottom chord elevation at panel point i (two-slope: rises to center)."""
        if panel_idx <= mid:
            return rise * (panel_idx / mid)
        else:
            return rise * ((N - panel_idx) / mid)
    
    # Bottom Chords (two-slope)
    EA_val, EI_val = get_props("Bottom Chord")
    for i in range(N):
        x1, x2 = i * dx, (i + 1) * dx
        yb1, yb2 = y_bot(i), y_bot(i + 1)
        if EA_val:
            chord_bot_ids.append(ss.add_element(location=[[x1, yb1], [x2, yb2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            chord_bot_ids.append(ss.add_truss_element(location=[[x1, yb1], [x2, yb2]]))
    
    # Top Chords (two-slope, offset by depth above bottom)
    EA_val, EI_val = get_props("Top Chord")
    for i in range(N):
        x1, x2 = i * dx, (i + 1) * dx
        yt1, yt2 = y_bot(i) + depth, y_bot(i + 1) + depth
        if EA_val:
            chord_top_ids.append(ss.add_element(location=[[x1, yt1], [x2, yt2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            chord_top_ids.append(ss.add_truss_element(location=[[x1, yt1], [x2, yt2]]))
    
    # Vertical Webs (at every panel point, always 2.0m tall)
    EA_val, EI_val = get_props("Vertical Webs")
    for i in range(N + 1):
        x = i * dx
        yb = y_bot(i)
        if EA_val:
            web_vert_ids.append(ss.add_element(location=[[x, yb], [x, yb + depth]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            web_vert_ids.append(ss.add_truss_element(location=[[x, yb], [x, yb + depth]]))
    
    # Diagonal Webs (Pratt pattern — diagonals slope toward midspan)
    EA_val, EI_val = get_props("Diagonal Webs")
    for i in range(N):
        if i < mid:
            # Left half: bottom-left to top-right
            x1, y1 = i * dx, y_bot(i)
            x2, y2 = (i + 1) * dx, y_bot(i + 1) + depth
        else:
            # Right half: bottom-right to top-left
            x1, y1 = (i + 1) * dx, y_bot(i + 1)
            x2, y2 = i * dx, y_bot(i) + depth
        
        if EA_val:
            web_diag_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            web_diag_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))
    
    # --- 6m Steel Columns (fixed base at y=-6.0) ---
    col_height = 6.0
    col_EA, col_EI = get_props("Columns")
    if not col_EA:
        col_EA = 0.01 * 200e9    # default stiffness
        col_EI = 0.0001 * 200e9
    
    col_ids = []
    # Left column: from ground (0, -6) up to bottom chord start (0, 0)
    col_ids.append(ss.add_element(location=[[0.0, -col_height], [0.0, 0.0]], EA=col_EA, EI=col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([0.0, -col_height]))
    
    # Right column: from ground (24, -6) up to bottom chord end (24, 0)
    col_ids.append(ss.add_element(location=[[span, -col_height], [span, 0.0]], EA=col_EA, EI=col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([span, -col_height]))
    
    mapping = {
        "Top Chord": chord_top_ids,
        "Bottom Chord": chord_bot_ids,
        "Vertical Webs": web_vert_ids,
        "Diagonal Webs": web_diag_ids,
        "Columns": col_ids
    }
    
    # Apply gravity loads on top chord
    for eid in chord_top_ids:
        ss.q_load(q=(dl_q_kn_m + ll_q_kn_m), element_id=eid, direction='y')
    
    # Apply lateral load on columns (wind or earthquake)
    if lateral_q_kn_m != 0:
        for eid in col_ids:
            ss.q_load(q=lateral_q_kn_m, element_id=eid, direction='x')
    
    return ss, mapping
