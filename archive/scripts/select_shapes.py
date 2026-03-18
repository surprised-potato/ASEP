import pandas as pd
import numpy as np
import math

# Force inputs
# Chords: P = 162.57 kN (~ 36.55 kips), L = 1.0 m (~ 39.37 in)
# Webs:   P = 40.72 kN  (~ 9.15 kips),  L = 1.2 m (~ 47.24 in)

def kn_to_kips(kn):
    return kn * 0.224809

def m_to_in(m):
    return m * 39.3701

def check_shape(Ag, r_min, Pu_kips, L_in, Fy=50, E=29000):
    k_l_r = L_in / r_min
    
    # Slenderness check
    if k_l_r > 200:
        return False, 0.0, k_l_r
        
    # Tension capacity
    phi_t = 0.9
    Pn_t = Fy * Ag
    if phi_t * Pn_t < Pu_kips:
        return False, 0.0, k_l_r
        
    # Compression capacity (AISC E3)
    Fe = (math.pi**2 * E) / (k_l_r**2)
    slenderness_limit = 4.71 * math.sqrt(E / Fy)
    
    if k_l_r <= slenderness_limit:
        Fcr = (0.658**(Fy / Fe)) * Fy
    else:
        Fcr = 0.877 * Fe
        
    phi_c = 0.9
    Pn_c = Fcr * Ag
    
    if phi_c * Pn_c < Pu_kips:
        return False, phi_c * Pn_c, k_l_r
        
    return True, phi_c * Pn_c, k_l_r

print("Loading Database...")
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')

# Filter for W shapes, HSS Rectangular, HSS Square, HSS Round, and Angles (L)
allowed_types = ['W', 'HSS_Rect', 'HSS_Sq', 'HSS_Rnd', 'L']
db_filtered = db[db['Type'].isin(allowed_types)].copy()

# Ensure we have valid A and r_min (minimum of rx, ry, rz if available)
db_filtered['A'] = pd.to_numeric(db_filtered['A'], errors='coerce')
db_filtered['W'] = pd.to_numeric(db_filtered['W'], errors='coerce')
db_filtered['rx'] = pd.to_numeric(db_filtered['rx'], errors='coerce')
db_filtered['ry'] = pd.to_numeric(db_filtered['ry'], errors='coerce')
db_filtered['rz'] = pd.to_numeric(db_filtered['rz'], errors='coerce')

# Calculate r_min
db_filtered['r_min'] = db_filtered[['rx', 'ry', 'rz']].min(axis=1)

# Drop rows without Area or r_min
db_filtered = db_filtered.dropna(subset=['A', 'r_min', 'W'])

def find_lightest(Pu_kn, L_m):
    Pu_kips = kn_to_kips(Pu_kn)
    L_in = m_to_in(L_m)
    
    valid_shapes = []
    
    for idx, row in db_filtered.iterrows():
        Ag = row['A']
        r_min = row['r_min']
        label = row['AISC_Manual_Label']
        weight = row['W']
        # Let's say Fy = 46 ksi for HSS and 50 ksi for W shapes, A36 for Angles
        fy = 50
        if row['Type'].startswith('HSS'):
            fy = 46
        elif row['Type'] == 'L':
            fy = 36
            
        passes, capacity, klr = check_shape(Ag, r_min, Pu_kips, L_in, Fy=fy)
        if passes:
            valid_shapes.append({
                'Label': label,
                'Weight': weight,
                'Type': row['Type'],
                'Area': Ag,
                'r_min': r_min,
                'KL/r': klr,
                'Capacity_kips': capacity,
                'Demand_kips': Pu_kips
            })
            
    if not valid_shapes:
        return None
        
    # Sort by weight ascending
    valid_shapes.sort(key=lambda x: x['Weight'])
    return valid_shapes[0]

chord_shape = find_lightest(162.57, 1.0)
web_shape = find_lightest(40.72, 1.2)

print("\n--- CHORD SHAPE SELECTION ---")
if chord_shape:
    for k, v in chord_shape.items():
        print(f"{k}: {v}")
else:
    print("No shape found.")

print("\n--- WEB SHAPE SELECTION ---")
if web_shape:
    for k, v in web_shape.items():
        print(f"{k}: {v}")
else:
    print("No shape found.")

