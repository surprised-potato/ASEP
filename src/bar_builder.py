"""
Bar Project — Standard Howe Truss with 2 Interior Columns.

Geometry:
  - 24m span, 16 panels (dx = 1.5m), 2.0m depth, 3.0m center rise
  - Two-slope (gable) chord profile
  - HOWE diagonal pattern: diagonals slope AWAY from center (compression)
  - 2 exterior columns (fixed base) at x = 0m, x = 24m
  - 2 interior columns (fixed base) at panel 5 (x = 7.5m) and panel 11 (x = 16.5m)
  - All columns originate from same ground level (y = -6.0m)
"""

from anastruct import SystemElements
import math


def build_bar_truss(results_map=None, lateral_q_kn_m=0.0, dl_q_kn_m=0.0, ll_q_kn_m=0.0, N=21, has_int_cols=True):
    """Builds a 21m isosceles triangle Howe truss with level bottom chord.

    Args:
        results_map: Dict of group_name -> AISC shape dict for injecting EA/EI.
        lateral_q_kn_m: Lateral distributed load on exterior columns (kN/m).
        dl_q_kn_m: Dead load line load on top chord (kN/m, negative = downward).
        ll_q_kn_m: Live load line load on top chord (kN/m, negative = downward).
        N: Number of truss panels (default 21 for 1m panels).
        has_int_cols: Whether to include the 2 interior columns.

    Returns:
        (SystemElements, mapping_dict) where mapping_dict maps group names to element IDs.
    """
    if results_map is None:
        results_map = {}

    ss = SystemElements()
    span = 21.0      # total span (m)
    depth_end = 0.0  # isosceles triangle (zero depth at supports)
    depth_mid = 2.0  # REDUCED truss depth at midspan (m)
    dx = span / N    # panel width
    mid = N // 2     # midspan panel index
    col_height = 4.0 # REDUCED column height from ground level

    # Interior column panel indices (at exact third-points if span=21, N=21)
    int_col_panel_left = int(N / 3)   # 7
    int_col_panel_right = int(2 * N / 3) # 14

    chord_bot_ids, chord_top_ids, web_vert_ids, web_diag_ids = [], [], [], []

    def get_props(group_name):
        r = results_map.get(group_name)
        if not r:
            return 0, 0
        
        # RC Column handling
        if "Column" in group_name and r.get('Type') == 'RC':
            E_conc = 21.5e9
            A_conc = r['Area']  # m^2
            I_eff = r['Ix']     # m^4 (already 0.70 Ig)
            return float(A_conc * E_conc), float(I_eff * E_conc)
            
        # Steel Member handling
        return float(r['Area'] * 0.00064516) * 200e9, float(r['Ix'] * 4.1623e-7) * 200e9

    def y_bot(panel_idx):
        return 0.0

    def y_top(panel_idx):
        mid_x = span / 2.0
        curr_x = panel_idx * dx
        if curr_x <= mid_x:
            return depth_end + (depth_mid - depth_end) * (curr_x / mid_x)
        else:
            return depth_mid - (depth_mid - depth_end) * ((curr_x - mid_x) / mid_x)

    # ── Bottom Chords ──────────────────────────────────────────────
    EA_val, EI_val = get_props("Bottom Chord")
    for i in range(N):
        x1, x2 = i * dx, (i + 1) * dx
        yb1, yb2 = y_bot(i), y_bot(i + 1)
        if EA_val:
            chord_bot_ids.append(ss.add_element(location=[[x1, yb1], [x2, yb2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            chord_bot_ids.append(ss.add_truss_element(location=[[x1, yb1], [x2, yb2]]))

    # ── Top Chords ─────────────────────────────────────────────────
    EA_val, EI_val = get_props("Top Chord")
    for i in range(N):
        x1, x2 = i * dx, (i + 1) * dx
        yt1, yt2 = y_top(i), y_top(i + 1)
        if EA_val:
            chord_top_ids.append(ss.add_element(location=[[x1, yt1], [x2, yt2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            chord_top_ids.append(ss.add_truss_element(location=[[x1, yt1], [x2, yt2]]))

    # ── Vertical Webs ──────────────────────────────────────────────
    EA_val, EI_val = get_props("Vertical Webs")
    for i in range(N + 1):
        x = i * dx
        yb = y_bot(i)
        yt = y_top(i)
        # Skip zero-length verticals at ends
        if abs(yt - yb) < 1e-6:
            continue
        if EA_val:
            web_vert_ids.append(ss.add_element(location=[[x, yb], [x, yt]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            web_vert_ids.append(ss.add_truss_element(location=[[x, yb], [x, yt]]))

    # ── Diagonal Webs — HOWE pattern ──────────────────────────────
    EA_val, EI_val = get_props("Diagonal Webs")
    mid_idx = N / 2.0
    for i in range(N):
        if i < mid_idx:
            # Left half: top-left to bottom-right
            x1, y1 = i * dx, y_top(i)
            x2, y2 = (i + 1) * dx, y_bot(i + 1)
        else:
            # Right half: top-right to bottom-left
            x1, y1 = (i + 1) * dx, y_top(i + 1)
            x2, y2 = i * dx, y_bot(i)
        
        # Skip diagonals that start/end at same node (can happen if depth_end=0)
        dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        if dist < 1e-6:
            continue

        if EA_val:
            web_diag_ids.append(ss.add_element(location=[[x1, y1], [x2, y2]], EA=EA_val, EI=EI_val, spring={1: 0, 2: 0}))
        else:
            web_diag_ids.append(ss.add_truss_element(location=[[x1, y1], [x2, y2]]))

    # ── Exterior Columns (fixed base) ─────────────────────────────
    ext_col_EA, ext_col_EI = get_props("Exterior Columns")
    if not ext_col_EA:
        ext_col_EA, ext_col_EI = 0.01 * 200e9, 0.0001 * 200e9
    
    ext_col_ids = []
    ext_col_ids.append(ss.add_element(location=[[0.0, -col_height], [0.0, 0.0]], EA=ext_col_EA, EI=ext_col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([0.0, -col_height]))
    ext_col_ids.append(ss.add_element(location=[[span, -col_height], [span, 0.0]], EA=ext_col_EA, EI=ext_col_EI))
    ss.add_support_fixed(node_id=ss.find_node_id([span, -col_height]))

    # ── Interior Columns (fixed base) ─────────────────────────────
    int_col_ids = []
    if has_int_cols:
        int_col_EA, int_col_EI = get_props("Interior Columns")
        if not int_col_EA:
            int_col_EA, int_col_EI = 0.01 * 200e9, 0.0001 * 200e9

        x_int_l = int_col_panel_left * dx
        int_col_ids.append(ss.add_element(location=[[x_int_l, -col_height], [x_int_l, 0.0]], EA=int_col_EA, EI=int_col_EI))
        ss.add_support_fixed(node_id=ss.find_node_id([x_int_l, -col_height]))
        x_int_r = int_col_panel_right * dx
        int_col_ids.append(ss.add_element(location=[[x_int_r, -col_height], [x_int_r, 0.0]], EA=int_col_EA, EI=int_col_EI))
        ss.add_support_fixed(node_id=ss.find_node_id([x_int_r, -col_height]))

    # ── Mapping ────────────────────────────────────────────────────
    mapping = {
        "Top Chord": chord_top_ids,
        "Bottom Chord": chord_bot_ids,
        "Vertical Webs": web_vert_ids,
        "Diagonal Webs": web_diag_ids,
        "Exterior Columns": ext_col_ids,
    }
    if has_int_cols:
        mapping["Interior Columns"] = int_col_ids

    # ── Apply Loads ────────────────────────────────────────────────
    # Gravity loads on top chord
    for eid in chord_top_ids:
        ss.q_load(q=(dl_q_kn_m + ll_q_kn_m), element_id=eid, direction='y')

    # Lateral load on exterior columns (wind or earthquake)
    if lateral_q_kn_m != 0:
        for eid in ext_col_ids:
            ss.q_load(q=lateral_q_kn_m, element_id=eid, direction='x')

    return ss, mapping
