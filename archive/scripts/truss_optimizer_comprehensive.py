import pandas as pd
import numpy as np
import math
from anastruct import SystemElements
try:
    from IPython.display import display # just in case they want to run it in a notebook later
except ImportError:
    pass

def check_shape_si(Ag_mm2, r_min_mm, demand_tension_kn, demand_comp_kn, L_mm, Fy_mpa=250, E_mpa=200000):
    if r_min_mm == 0:
        return False, 0.0, 0.0
        
    k_l_r = L_mm / r_min_mm
    
    # Slenderness check (compression elements KL/r <= 200)
    if k_l_r > 200:
        return False, 0.0, k_l_r
        
    # Tension capacity (phi = 0.9, Pn = Fy * Ag)
    phi_t = 0.9
    Pn_t_kn = (Fy_mpa * Ag_mm2) / 1000.0
    if phi_t * Pn_t_kn < demand_tension_kn:
        return False, 0.0, k_l_r
        
    # Compression capacity (AISC E3)
    Fe_mpa = (math.pi**2 * E_mpa) / (k_l_r**2)
    slenderness_limit = 4.71 * math.sqrt(E_mpa / Fy_mpa)
    
    if k_l_r <= slenderness_limit:
        Fcr_mpa = (0.658**(Fy_mpa / Fe_mpa)) * Fy_mpa
    else:
        Fcr_mpa = 0.877 * Fe_mpa
        
    phi_c = 0.9
    Pn_c_kn = (Fcr_mpa * Ag_mm2) / 1000.0
    
    if phi_c * Pn_c_kn < demand_comp_kn:
        return False, phi_c * Pn_c_kn, k_l_r
        
    # Return minimum of capacities just for reporting
    capacity = min(phi_t * Pn_t_kn, phi_c * Pn_c_kn)
    return True, capacity, k_l_r

def load_database():
    print("Loading AISC Database...")
    db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
    # Filter for 2L (Double Angles) with zero gusset spacing (2 'X's in label)
    db_filtered = db[(db['Type'] == '2L') & (db['AISC_Manual_Label.1'].str.count('X') == 2)].copy()

    db_filtered['A_metric'] = pd.to_numeric(db_filtered['A.1'], errors='coerce')
    db_filtered['W_metric'] = pd.to_numeric(db_filtered['W.1'], errors='coerce')
    db_filtered['rx_metric'] = pd.to_numeric(db_filtered['rx.1'], errors='coerce')
    db_filtered['ry_metric'] = pd.to_numeric(db_filtered['ry.1'], errors='coerce')
    db_filtered['rz_metric'] = pd.to_numeric(db_filtered['rz.1'], errors='coerce')

    db_filtered['r_min_metric'] = db_filtered[['rx_metric', 'ry_metric', 'rz_metric']].min(axis=1)
    db_filtered = db_filtered.dropna(subset=['A_metric', 'r_min_metric', 'W_metric'])
    db_filtered = db_filtered[db_filtered['r_min_metric'] > 0]
    return db_filtered

def find_lightest(db_filtered, max_tension_kn, max_comp_kn, L_m):
    L_mm = L_m * 1000.0
    valid_shapes = []
    
    for idx, row in db_filtered.iterrows():
        Ag = row['A_metric']
        r_min = row['r_min_metric']
        label = row['AISC_Manual_Label.1']
        weight = row['W_metric']
        fy = 250 # Yield strength for double angles
            
        passes, capacity, klr = check_shape_si(Ag, r_min, max_tension_kn, max_comp_kn, L_mm, Fy_mpa=fy)
        if passes:
            valid_shapes.append({
                'Label': label,
                'Weight (kg/m)': weight,
                'KL/r': round(klr, 2),
            })
            
    if not valid_shapes:
        return None
        
    valid_shapes.sort(key=lambda x: x['Weight (kg/m)'])
    return valid_shapes[0]

def analyze_truss(N, depth, db_filtered):
    L = 18.0
    dy = 1.0 # difference in y from x=0 to x=18
    dx = L / N
    dy_per_panel = dy / N
    
    ss = SystemElements()
    
    # Bottom chord
    for i in range(N):
        x1, y1 = i * dx, 4 + i * dy_per_panel
        x2, y2 = (i + 1) * dx, 4 + (i + 1) * dy_per_panel
        ss.add_truss_element(location=[[x1, y1], [x2, y2]])

    # Top chord
    for i in range(N):
        x1, y1 = i * dx, 4 + depth + i * dy_per_panel
        x2, y2 = (i + 1) * dx, 4 + depth + (i + 1) * dy_per_panel
        ss.add_truss_element(location=[[x1, y1], [x2, y2]])

    # Vertical web members
    for i in range(N + 1):
        x, y_bottom = i * dx, 4 + i * dy_per_panel
        y_top = y_bottom + depth
        ss.add_truss_element(location=[[x, y_bottom], [x, y_top]])

    # Diagonal web members
    for i in range(N):
        x1, y_bottom = i * dx, 4 + i * dy_per_panel
        x2, y_top2 = (i + 1) * dx, 4 + depth + (i + 1) * dy_per_panel
        ss.add_truss_element(location=[[x1, y_bottom], [x2, y_top2]])

    # Supports
    node_support_1 = ss.find_node_id([0, 4])
    node_support_2 = ss.find_node_id([18, 5])
    ss.add_support_hinged(node_id=node_support_1)
    ss.add_support_roll(node_id=node_support_2, direction=2)

    # Loads on top chord
    for i in range(N + 1, 2 * N + 1):
        ss.q_load(q=-2.4, element_id=i, direction='y')

    ss.solve()
    
    # Results extraction
    chord_forces = [ss.element_map[i].N_1 for i in range(1, 2 * N + 1)]
    web_forces = [ss.element_map[i].N_1 for i in range(2 * N + 1, 4 * N + 2)]
    chord_lengths = [ss.element_map[i].l for i in range(1, 2 * N + 1)]
    web_lengths = [ss.element_map[i].l for i in range(2 * N + 1, 4 * N + 2)]
    
    chord_max_tension = max(chord_forces) if any(f > 0 for f in chord_forces) else 0.0
    chord_max_comp = abs(min(chord_forces)) if any(f < 0 for f in chord_forces) else 0.0
    chord_max_length = max(chord_lengths) if chord_lengths else 0.0

    web_max_tension = max(web_forces) if any(f > 0 for f in web_forces) else 0.0
    web_max_comp = abs(min(web_forces)) if any(f < 0 for f in web_forces) else 0.0
    web_max_length = max(web_lengths) if web_lengths else 0.0
    
    # Shape Selection
    chord_shape = find_lightest(db_filtered, chord_max_tension, chord_max_comp, chord_max_length)
    web_shape = find_lightest(db_filtered, web_max_tension, web_max_comp, web_max_length)
    
    total_chord_length = sum(chord_lengths)
    total_web_length = sum(web_lengths)
    
    total_weight = 0.0
    
    chord_label = "None"
    chord_unit_weight = 0.0
    if chord_shape:
        chord_label = chord_shape['Label']
        chord_unit_weight = chord_shape['Weight (kg/m)']
        total_weight += chord_unit_weight * total_chord_length
        
    web_label = "None"
    web_unit_weight = 0.0
    if web_shape:
        web_label = web_shape['Label']
        web_unit_weight = web_shape['Weight (kg/m)']
        total_weight += web_unit_weight * total_web_length

    return {
        'Panels': N,
        'Depth (m)': depth,
        'Chord (T, C)': f"{round(chord_max_tension, 1)}kN, {round(chord_max_comp, 1)}kN",
        'Chord Shape (SI)': chord_label,
        'Web (T, C)': f"{round(web_max_tension, 1)}kN, {round(web_max_comp, 1)}kN",
        'Web Shape (SI)': web_label,
        'Total Mass (kg)': round(total_weight, 2)
    }

def main():
    db_filtered = load_database()
    print(f"Loaded {len(db_filtered)} double angle options with 0-spacing.\n")
    
    panel_options = [12, 14, 16, 18, 20]
    depth_options = [0.4, 0.5, 0.6, 0.7, 0.8]
    
    results = []
    print("Running optimizations...")
    for N in panel_options:
        for depth in depth_options:
            res = analyze_truss(N, depth, db_filtered)
            results.append(res)
            
    df = pd.DataFrame(results)
    df = df.sort_values(by='Total Mass (kg)')
    
    print("\n--- OPTIMIZATION RESULTS (Sorted by Minimum Total Mass) ---")
    print(df.to_string(index=False))
    
    df.to_csv("truss_optimization_results.csv", index=False)
    print("\nResults saved to truss_optimization_results.csv")

if __name__ == "__main__":
    main()
