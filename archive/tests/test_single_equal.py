import pandas as pd
import numpy as np
import math
from anastruct import SystemElements

def check_shape_si(Ag, r_min, dt, dc, L_mm, Fy=250, E=200000):
    if r_min == 0: return False, 0.0, 0.0, 0.0
    klr = L_mm / r_min
    if klr > 200: return False, 0.0, 0.0, klr
    
    pt = 0.9 * (Fy * Ag) / 1000.0
    if pt < dt: return False, pt, 0.0, klr
    
    Fe = (math.pi**2 * E) / (klr**2)
    sl = 4.71 * math.sqrt(E / Fy)
    Fcr = (0.658**(Fy / Fe)) * Fy if klr <= sl else 0.877 * Fe
    pc = 0.9 * (Fcr * Ag) / 1000.0
    
    if pc < dc: return False, pt, pc, klr
    return True, pt, pc, klr

db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
# Get Single Angles AND Equal Legs ONLY (d == b)
db_filtered = db[(db['Type'] == 'L') & (db['d'] == db['b'])].copy()

db_filtered['A_m'] = pd.to_numeric(db_filtered['A.1'], errors='coerce')
db_filtered['W_m'] = pd.to_numeric(db_filtered['W.1'], errors='coerce')
db_filtered['rx_m'] = pd.to_numeric(db_filtered['rx.1'], errors='coerce')
db_filtered['ry_m'] = pd.to_numeric(db_filtered['ry.1'], errors='coerce')
db_filtered['rz_m'] = pd.to_numeric(db_filtered['rz.1'], errors='coerce')
db_filtered['r_m'] = db_filtered[['rx_m', 'ry_m', 'rz_m']].min(axis=1)
db_filtered = db_filtered.dropna(subset=['A_m', 'r_m', 'W_m'])
db_filtered = db_filtered[db_filtered['r_m'] > 0] 

def find_lightest(dt, dc, L_m):
    valid = []
    for idx, row in db_filtered.iterrows():
        p, ct, cc, klr = check_shape_si(row['A_m'], row['r_m'], dt, dc, L_m*1000, 250)
        if p:
            valid.append({
                'Shape': row['AISC_Manual_Label.1'], 'W': row['W_m'], 
                'klr': round(klr, 2), 'ct': round(ct, 1), 'cc': round(cc, 1)
            })
    if not valid: return None
    valid.sort(key=lambda x: x['W'])
    return valid[0]

def analyze(udl):
    N, depth, L = 18, 0.6, 18.0
    ss = SystemElements()
    dx, dy = L/N, 1.0/N
    for i in range(N): ss.add_truss_element([[i*dx, 4+i*dy], [(i+1)*dx, 4+(i+1)*dy]])
    for i in range(N): ss.add_truss_element([[i*dx, 4+depth+i*dy], [(i+1)*dx, 4+depth+(i+1)*dy]])
    for i in range(N+1): ss.add_truss_element([[i*dx, 4+i*dy], [i*dx, 4+depth+i*dy]])
    for i in range(N): ss.add_truss_element([[i*dx, 4+i*dy], [(i+1)*dx, 4+depth+(i+1)*dy]])
    ss.add_support_hinged(ss.find_node_id([0, 4]))
    ss.add_support_roll(ss.find_node_id([18, 5]), 2)
    for i in range(N+1, 2*N+1): ss.q_load(q=udl, element_id=i, direction='y')
    ss.solve()
    
    cf = [ss.element_map[i].N_1 for i in range(1, 2*N+1)]
    wf = [ss.element_map[i].N_1 for i in range(2*N+1, 4*N+2)]
    
    return {
        'ct': max(cf) if any(f>0 for f in cf) else 0,
        'cc': abs(min(cf)) if any(f<0 for f in cf) else 0,
        'wt': max(wf) if any(f>0 for f in wf) else 0,
        'wc': abs(min(wf)) if any(f<0 for f in wf) else 0,
        'cl': max([ss.element_map[i].l for i in range(1, 2*N+1)]),
        'wl': max([ss.element_map[i].l for i in range(2*N+1, 4*N+2)]),
        'ctl': sum([ss.element_map[i].l for i in range(1, 2*N+1)]),
        'wtl': sum([ss.element_map[i].l for i in range(2*N+1, 4*N+2)])
    }

down = analyze(-2.296)
up = analyze(1.036)

c_t = max(down['ct'], up['ct'])
c_c = max(down['cc'], up['cc'])
w_t = max(down['wt'], up['wt'])
w_c = max(down['wc'], up['wc'])

cs = find_lightest(c_t, c_c, down['cl'])
ws = find_lightest(w_t, w_c, down['wl'])

t = []
if cs:
    wkm = cs['W'] * 9.80665 / 1000.0
    t.append({'Group':'Chords', 'Max T':round(c_t,1), 'Max C':round(c_c,1), 'Max L':round(down['cl'],2), 
              'Shape':cs['Shape'], 'KL/r':cs['klr'], 'Cap T':cs['ct'], 'Cap C':cs['cc'], 
              'Wt(kN/m)':round(wkm,3), 'GrpWt(kN)':round(wkm*down['ctl'],2)})
else:
    print("WARNING: No valid chord shapes found.")
if ws:
    wkm = ws['W'] * 9.80665 / 1000.0
    t.append({'Group':'Webs', 'Max T':round(w_t,1), 'Max C':round(w_c,1), 'Max L':round(down['wl'],2), 
              'Shape':ws['Shape'], 'KL/r':ws['klr'], 'Cap T':ws['ct'], 'Cap C':ws['cc'], 
              'Wt(kN/m)':round(wkm,3), 'GrpWt(kN)':round(wkm*down['wtl'],2)})
else:
    print("WARNING: No valid web shapes found.")
    

print("\n" + "="*135)
print(f"{'EQUAL LEG SINGLE ANGLE - NSCP ENVELOPE SELECTION SUMMARY (18 Panels, 0.6m Depth)':^135}")
print("="*135)
print(pd.DataFrame(t).to_markdown(index=False))
print("="*135 + "\n")
