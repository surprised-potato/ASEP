from src.aisc_database import aisc_db
from src.bar_truss_builder import build_bar_truss, get_max_force

def debug():
    ss, ids = build_bar_truss()
    ss.solve()
    p_bc = get_max_force(ss, ids['bc_ids'])
    p_tc = get_max_force(ss, ids['tc_ids'])
    print(f"Chord force (kN): {max(p_bc, p_tc)}")
    shape = aisc_db.select_lightest(max(p_bc, p_tc), 1.5, family='WT')
    print("Selected Shape:", shape)

if __name__ == '__main__':
    debug()
