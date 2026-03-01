import pandas as pd
from anastruct import SystemElements

# 1. Get forces from the given truss: N=18, depth=0.6m
L = 18.0
dy = 1.0 # difference in y from x=0 to x=18
depth = 0.6
N = 18 # number of panels
dx = L / N
dy_per_panel = dy / N

ss = SystemElements()
        
# Create nodes and elements
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

node_support_1 = ss.find_node_id([0, 4])
node_support_2 = ss.find_node_id([18, 5])

ss.add_support_hinged(node_id=node_support_1)
ss.add_support_roll(node_id=node_support_2, direction=2)

for i in range(N + 1, 2 * N + 1):
    ss.q_load(q=-2.4, element_id=i, direction='y')

ss.solve()

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

print(f"Chord: Max Tension={chord_max_tension:.2f} kN, Max Comp={chord_max_comp:.2f} kN, Max L={chord_max_length:.2f} m")
print(f"Web: Max Tension={web_max_tension:.2f} kN, Max Comp={web_max_comp:.2f} kN, Max L={web_max_length:.2f} m")

# 2. Read AISC Database
# Load database, sheets can be "Database v16.0"
xls = pd.ExcelFile('aisc-shapes-database-v160-2.xlsx')
print("Sheet names:", xls.sheet_names)
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
print(db.columns.tolist()[:30])
