import pandas as pd
import numpy as np
import math
from anastruct import SystemElements

def check_shape_si(Ag_mm2, r_min_mm, demand_tension_kn, demand_comp_kn, L_mm, Fy_mpa=250, E_mpa=200000):
    if r_min_mm == 0:
        return False, 0.0, 0.0, 0.0
        
    k_l_r = L_mm / r_min_mm
    
    if k_l_r > 200:
        return False, 0.0, 0.0, k_l_r
        
    phi_t = 0.9
    Pn_t_kn = (Fy_mpa * Ag_mm2) / 1000.0
    if phi_t * Pn_t_kn < demand_tension_kn:
        return False, phi_t * Pn_t_kn, 0.0, k_l_r
        
    Fe_mpa = (math.pi**2 * E_mpa) / (k_l_r**2)
    slenderness_limit = 4.71 * math.sqrt(E_mpa / Fy_mpa)
    
    if k_l_r <= slenderness_limit:
        Fcr_mpa = (0.658**(Fy_mpa / Fe_mpa)) * Fy_mpa
    else:
        Fcr_mpa = 0.877 * Fe_mpa
        
    phi_c = 0.9
    Pn_c_kn = (Fcr_mpa * Ag_mm2) / 1000.0
    
    if phi_c * Pn_c_kn < demand_comp_kn:
        return False, phi_t * Pn_t_kn, phi_c * Pn_c_kn, k_l_r
        
    return True, phi_t * Pn_t_kn, phi_c * Pn_c_kn, k_l_r

def load_database():
    db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
    # Extract Single Angles (L) and filter for Equal Angles (d == b)
    db_filtered = db[(db['Type'] == 'L') & (db['d'] == db['b'])].copy()

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
        fy = 250 # Yield strength for angles
            
        passes, cap_t, cap_c, klr = check_shape_si(Ag, r_min, max_tension_kn, max_comp_kn, L_mm, Fy_mpa=fy)
        if passes:
            valid_shapes.append({
                'Shape': label,
                'Weight (kg/m)': weight,
                'Area (mm²)': Ag,
                'r_min (mm)': r_min,
                'KL/r': round(klr, 2),
                'Tension Cap (kN)': round(cap_t, 1),
                'Comp Cap (kN)': round(cap_c, 1)
            })
            
    if not valid_shapes:
        return None
        
    valid_shapes.sort(key=lambda x: x['Weight (kg/m)'])
    return valid_shapes[0]

def analyze_truss(udl_load):
    N = 18
    depth = 0.6
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

    # Apply given uniform load on top chord (negative is downward, positive is uplift)
    for i in range(N + 1, 2 * N + 1):
        ss.q_load(q=udl_load, element_id=i, direction='y')

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
    
    total_chord_length = sum(chord_lengths)
    total_web_length = sum(web_lengths)
    
    return {
        'Chords': {
            'Max Tension (kN)': round(chord_max_tension, 1),
            'Max Comp (kN)': round(chord_max_comp, 1),
            'Max Length (m)': round(chord_max_length, 2),
            'Total Length (m)': total_chord_length
        },
        'Webs': {
            'Max Tension (kN)': round(web_max_tension, 1),
            'Max Comp (kN)': round(web_max_comp, 1),
            'Max Length (m)': round(web_max_length, 2),
            'Total Length (m)': total_web_length
        }
    }

def main():
    print("Loading database and analyzing truss load combinations...")
    db_filtered = load_database()
    
    # Run Load Combinations
    # Comb 1 (1.2D + 1.0W) = 2.296 kN/m downward
    # Comb 2 (0.9D + 1.0W uplift) = -1.036 kN/m (represented structurally as uplift -> positive Y direction in Anastruct)
    demands_down = analyze_truss(-2.296)
    demands_up = analyze_truss(1.036)
    
    # Merge enveloping demands
    chord_max_t = max(demands_down['Chords']['Max Tension (kN)'], demands_up['Chords']['Max Tension (kN)'])
    chord_max_c = max(demands_down['Chords']['Max Comp (kN)'], demands_up['Chords']['Max Comp (kN)'])
    web_max_t = max(demands_down['Webs']['Max Tension (kN)'], demands_up['Webs']['Max Tension (kN)'])
    web_max_c = max(demands_down['Webs']['Max Comp (kN)'], demands_up['Webs']['Max Comp (kN)'])
    
    # Lengths stay the same regardless of load
    chord_max_l = demands_down['Chords']['Max Length (m)']
    web_max_l = demands_down['Webs']['Max Length (m)']
    total_chord_length = demands_down['Chords']['Total Length (m)']
    total_web_length = demands_down['Webs']['Total Length (m)']

    chord_shape = find_lightest(db_filtered, chord_max_t, chord_max_c, chord_max_l)
    web_shape = find_lightest(db_filtered, web_max_t, web_max_c, web_max_l)
    
    table_data = []
    if chord_shape:
        wt_kn_m = chord_shape['Weight (kg/m)'] * 9.80665 / 1000.0
        tot_wt_kn = wt_kn_m * total_chord_length
        table_data.append({
            'Member Group': 'Chords',
            'Max T (kN)': chord_max_t,
            'Max C (kN)': chord_max_c,
            'Max L (m)': chord_max_l,
            'Selected Shape': chord_shape['Shape'],
            'KL/r': chord_shape['KL/r'],
            'Cap T (kN)': chord_shape['Tension Cap (kN)'],
            'Cap C (kN)': chord_shape['Comp Cap (kN)'],
            'Weight (kN/m)': round(wt_kn_m, 3),
            'Group Wt (kN)': round(tot_wt_kn, 2)
        })
        
    if web_shape:
        wt_kn_m = web_shape['Weight (kg/m)'] * 9.80665 / 1000.0
        tot_wt_kn = wt_kn_m * total_web_length
        table_data.append({
            'Member Group': 'Webs',
            'Max T (kN)': web_max_t,
            'Max C (kN)': web_max_c,
            'Max L (m)': web_max_l,
            'Selected Shape': web_shape['Shape'],
            'KL/r': web_shape['KL/r'],
            'Cap T (kN)': web_shape['Tension Cap (kN)'],
            'Cap C (kN)': web_shape['Comp Cap (kN)'],
            'Weight (kN/m)': round(wt_kn_m, 3),
            'Group Wt (kN)': round(tot_wt_kn, 2)
        })
        
    df = pd.DataFrame(table_data)
    
    print("\n" + "="*145)
    print(f"{'SINGLE ANGLE - NSCP ENVELOPE SELECTION SUMMARY (18 Panels, 0.6m Depth)':^145}")
    print("="*145)
    print(df.to_markdown(index=False))
    print("="*145 + "\n")

if __name__ == "__main__":
    main()
