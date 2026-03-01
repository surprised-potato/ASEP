import pandas as pd
import numpy as np
import math
from anastruct import SystemElements

def check_shape(Ag, rmin, dt, dc, L_mm):
    if rmin == 0: return False, 0.0, 0.0
    klr = L_mm / rmin
    if klr > 200: return False, 0.0, 0.0
    
    Fy = 250
    E = 200000
    pt = 0.9 * (Fy * Ag) / 1000.0
    if pt < dt: return False, pt, 0.0
    
    Fe = (math.pi**2 * E) / (klr**2)
    sl = 4.71 * math.sqrt(E / Fy)
    Fcr = (0.658**(Fy / Fe)) * Fy if klr <= sl else 0.877 * Fe
    pc = 0.9 * (Fcr * Ag) / 1000.0
    
    if pc < dc: return False, pt, pc
    return True, pt, pc

db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
# Get Equal Legs
db_f = db[(db['Type'] == 'L') & (db['d'] == db['b']) & (db['rx.1'].notna()) & (db['rx.1'] != '–')].copy()
db_f['A_m'] = pd.to_numeric(db_f['A.1'], errors='coerce')
db_f['W_m'] = pd.to_numeric(db_f['W.1'], errors='coerce')
db_f['rx_m'] = pd.to_numeric(db_f['rx.1'], errors='coerce')
db_f['ry_m'] = pd.to_numeric(db_f['ry.1'], errors='coerce')
db_f['rz_m'] = pd.to_numeric(db_f['rz.1'], errors='coerce')
db_f['r_m'] = db_f[['rx_m', 'ry_m', 'rz_m']].min(axis=1)
db_f = db_f.dropna(subset=['A_m', 'r_m', 'W_m'])

dt_chord, dc_chord, l_chord = 155.5, 155.5, 1000.0
dt_web, dc_web, l_web = 39.0, 39.0, 1200.0

print("Evaluating...")
vc = []
for i, r in db_f.iterrows():
    p, t, c = check_shape(r['A_m'], r['r_m'], dt_chord, dc_chord, l_chord)
    if p: vc.append({'Shape': r['AISC_Manual_Label.1'], 'W': r['W_m'], 'CapT': t, 'CapC': c})
    
vw = []
for i, r in db_f.iterrows():
    p, t, c = check_shape(r['A_m'], r['r_m'], dt_web, dc_web, l_web)
    if p: vw.append({'Shape': r['AISC_Manual_Label.1'], 'W': r['W_m'], 'CapT': t, 'CapC': c})
    
c_best = sorted(vc, key=lambda x: x['W'])[0] if vc else None
w_best = sorted(vw, key=lambda x: x['W'])[0] if vw else None

print("\nBest Equal Leg Chord:", c_best)
print("Best Equal Leg Web:", w_best)

