import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from aisc_database import aisc_db

gov_force = -138.0
L_m = 2.77
cap_c = abs(gov_force)

# get top chord bf
WT4x9 = next((c for c in aisc_db.db_filtered.to_dict('records') if c['AISC_Manual_Label'] == 'WT4X9'), None)
print(f"WT4X9 bf: {WT4x9['bf']}")

# Check valid L family
res_L = aisc_db.select_candidates(gov_force, L_m, family='L', bf_max=WT4x9['bf'])
if res_L:
    print(f"Passed L: {res_L[0]['Label']} (cap={res_L[0]['Capacity_kN']}) width={res_L[0]['bf_in']}")
else:
    print("No L passed")

# Check valid HSS family
res_HSS = aisc_db.select_candidates(gov_force, L_m, family='HSS')
if res_HSS:
    print(f"Passed HSS: {res_HSS[0]['Label']} (cap={res_HSS[0]['Capacity_kN']})")
else:
    print("No HSS passed")

# Print all unique Types
print("Available Types:", aisc_db.db_filtered['Type'].unique())
