import pandas as pd
import numpy as np
import math

# Force inputs
# Chords: P = 162.57 kN, L = 1.0 m = 1000 mm
# Webs:   P = 40.72 kN,  L = 1.2 m = 1200 mm

def check_shape_si(Ag_mm2, r_min_mm, Pu_kn, L_mm, Fy_mpa=345, E_mpa=200000):
    if r_min_mm == 0:
        return False, 0.0, 0.0
        
    k_l_r = L_mm / r_min_mm
    
    # Slenderness check (compression elements KL/r <= 200)
    if k_l_r > 200:
        return False, 0.0, k_l_r
        
    # Tension capacity (phi = 0.9, Pn = Fy * Ag)
    # Output in kN => (MPa * mm2) / 1000
    phi_t = 0.9
    Pn_t_kn = (Fy_mpa * Ag_mm2) / 1000.0
    if phi_t * Pn_t_kn < Pu_kn:
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
    
    if phi_c * Pn_c_kn < Pu_kn:
        return False, phi_c * Pn_c_kn, k_l_r
        
    return True, phi_c * Pn_c_kn, k_l_r

print("Loading Database...")
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')

# Filter for 2L (Double Angles) with zero gusset spacing
# Zero spacing means there are exactly 2 'x' characters in the label (e.g. 2L102X102X15.9)
db_filtered = db[(db['Type'] == '2L') & (db['AISC_Manual_Label.1'].str.count('X') == 2)].copy()

# A.1 is Area in mm^2
# W.1 is nominal weight in kg/m
# rx.1, ry.1, rz.1 are radius of gyration elements in mm
db_filtered['A_metric'] = pd.to_numeric(db_filtered['A.1'], errors='coerce')
db_filtered['W_metric'] = pd.to_numeric(db_filtered['W.1'], errors='coerce')
db_filtered['rx_metric'] = pd.to_numeric(db_filtered['rx.1'], errors='coerce')
db_filtered['ry_metric'] = pd.to_numeric(db_filtered['ry.1'], errors='coerce')
db_filtered['rz_metric'] = pd.to_numeric(db_filtered['rz.1'], errors='coerce')

# Calculate r_min in mm
db_filtered['r_min_metric'] = db_filtered[['rx_metric', 'ry_metric', 'rz_metric']].min(axis=1)

# Drop rows without Area or r_min
db_filtered = db_filtered.dropna(subset=['A_metric', 'r_min_metric', 'W_metric'])

# Filter out rows with zero r_min to avoid division by zero
db_filtered = db_filtered[db_filtered['r_min_metric'] > 0]

def find_lightest(Pu_kn, L_mm):
    valid_shapes = []
    
    for idx, row in db_filtered.iterrows():
        Ag = row['A_metric']
        r_min = row['r_min_metric']
        label = row['AISC_Manual_Label.1']
        weight = row['W_metric']
        
        # Fy equivalence
        # A36 angle -> approx 250 MPa
        # W shapes (A992) -> 345 MPa
        # HSS (A500) -> approx 317 MPa (Grade B) or 345 MPa (Grade C)
        fy = 345
        if row['Type'].startswith('HSS'):
            fy = 317
        elif row['Type'] in ['L', '2L']:
            fy = 250
            
        passes, capacity, klr = check_shape_si(Ag, r_min, Pu_kn, L_mm, Fy_mpa=fy)
        if passes:
            valid_shapes.append({
                'Label (SI)': label,
                'Weight (kg/m)': weight,
                'Type': row['Type'],
                'Area (mm^2)': Ag,
                'r_min (mm)': r_min,
                'KL/r': round(klr, 2),
                'Capacity (kN)': round(capacity, 2),
                'Demand (kN)': Pu_kn,
                'Yield_Strength (MPa)': fy
            })
            
    if not valid_shapes:
        return None
        
    # Sort by metric weight ascending
    valid_shapes.sort(key=lambda x: x['Weight (kg/m)'])
    return valid_shapes[0]

# Analysis values
# Max Chord Force=162.57 kN, Max L=1.00 m (1000 mm)
# Max Web Force=40.72 kN, Max L=1.20 m (1200 mm)
chord_shape = find_lightest(162.57, 1000.0)
web_shape = find_lightest(40.72, 1200.0)

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
