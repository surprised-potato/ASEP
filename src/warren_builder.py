"""
Top-Supported Warren Transfer Truss Builder.

Geometry: Parallel-chord Warren truss, suspended from the top chord.
  - Bottom chord nodes at bay divisions (even spacing).
  - Top chord extended to supports (full span length).
  - End verticals connect bottom chord supports to top chord supports.
  - Supports are located at the TOP chord corners.
  - Diagonals zigzag between bottom and top inner nodes.

Groups: "Top Chord", "Bottom Chord", "Verticals", "Diagonals"
"""

from anastruct import SystemElements
import math


def build_warren_truss(results_map=None, point_load_kN=0.0, span=10.0, depth=1.4,
                       n_bays=4, dl_q_kn_m=0.0):
    """Builds a top-supported Warren truss with a midspan point load.

    Args:
        results_map: Dict of group_name -> AISC shape dict for injecting EA/EI.
        point_load_kN: Concentrated load at midspan bottom chord (kN, positive = downward).
        span: Total span (m).
        depth: Truss depth (m).
        n_bays: Number of bays (must be even for midspan symmetry).
        dl_q_kn_m: Distributed dead load on bottom chord (kN/m, negative = downward).

    Returns:
        (SystemElements, mapping_dict)
    """
    if results_map is None:
        results_map = {}

    ss = SystemElements()
    bay_width = span / n_bays

    # Node x-positions
    bot_x = [i * bay_width for i in range(n_bays + 1)]
    # Top chord has inner nodes (offset by half-bay) + end support nodes
    inner_top_x = [(i + 0.5) * bay_width for i in range(n_bays)]
    top_x = [0.0] + inner_top_x + [span]

    def get_props(group_name):
        r = results_map.get(group_name)
        if not r:
            return 0, 0
        A_m2 = float(r['Area']) * 0.00064516     # in² -> m²
        I_m4 = float(r['Ix']) * 4.1623e-7        # in⁴ -> m⁴
        E_steel = 200e6                           # kN/m² (anastruct uses kN)
        return float(A_m2 * E_steel), float(I_m4 * E_steel)

    bot_chord_ids = []
    top_chord_ids = []
    vert_ids = []
    diag_ids = []

    # --- Bottom chord elements (y=0) ---
    ea_bot, ei_bot = get_props("Bottom Chord")
    for i in range(n_bays):
        kwargs = {'location': [[bot_x[i], 0], [bot_x[i+1], 0]], 'spring': {1: 0, 2: 0}}
        if ea_bot > 0:
            kwargs['EA'] = ea_bot
            kwargs['EI'] = ei_bot
        eid = ss.add_element(**kwargs)
        bot_chord_ids.append(eid)

    # --- Top chord elements (y=depth) ---
    ea_top, ei_top = get_props("Top Chord")
    for i in range(len(top_x) - 1):
        kwargs = {'location': [[top_x[i], depth], [top_x[i+1], depth]], 'spring': {1: 0, 2: 0}}
        if ea_top > 0:
            kwargs['EA'] = ea_top
            kwargs['EI'] = ei_top
        eid = ss.add_element(**kwargs)
        top_chord_ids.append(eid)

    # --- End Vertical elements (at x=0 and x=span) ---
    ea_vert, ei_vert = get_props("Verticals")
    for x_pos in [0.0, span]:
        kwargs = {'location': [[x_pos, 0], [x_pos, depth]], 'spring': {1: 0, 2: 0}}
        if ea_vert > 0:
            kwargs['EA'] = ea_vert
            kwargs['EI'] = ei_vert
        eid = ss.add_element(**kwargs)
        vert_ids.append(eid)

    # --- Diagonal elements (Warren zigzag) ---
    ea_diag, ei_diag = get_props("Diagonals")
    for i in range(n_bays):
        # Left diagonal: bottom[i] -> inner_top[i] (/)
        kwargs = {'location': [[bot_x[i], 0], [inner_top_x[i], depth]], 'spring': {1: 0, 2: 0}}
        if ea_diag > 0:
            kwargs['EA'] = ea_diag
            kwargs['EI'] = ei_diag
        eid = ss.add_element(**kwargs)
        diag_ids.append(eid)

        # Right diagonal: inner_top[i] -> bottom[i+1] (\)
        kwargs = {'location': [[inner_top_x[i], depth], [bot_x[i+1], 0]], 'spring': {1: 0, 2: 0}}
        if ea_diag > 0:
            kwargs['EA'] = ea_diag
            kwargs['EI'] = ei_diag
        eid = ss.add_element(**kwargs)
        diag_ids.append(eid)

    # --- Supports (Moved to TOP chord) ---
    left_nid = None
    right_nid = None
    for nid, node in ss.node_map.items():
        nx = node.vertex.x if hasattr(node.vertex, 'x') else 0
        ny = node.vertex.y if hasattr(node.vertex, 'y') else 0
        if abs(ny - depth) < 0.01:  # Looking for TOP nodes
            if abs(nx) < 0.01:
                left_nid = nid
            elif abs(nx - span) < 0.01:
                right_nid = nid

    if left_nid:
        ss.add_support_hinged(left_nid)
    if right_nid:
        ss.add_support_roll(right_nid)

    # --- Point load at midspan bottom chord ---
    if point_load_kN != 0:
        mid_x = span / 2.0
        mid_nid = None
        for nid, node in ss.node_map.items():
            nx = node.vertex.x if hasattr(node.vertex, 'x') else 0
            ny = node.vertex.y if hasattr(node.vertex, 'y') else 0
            if abs(ny) < 0.01 and abs(nx - mid_x) < 0.01:
                mid_nid = nid
                break
        if mid_nid:
            ss.point_load(mid_nid, Fy=-abs(point_load_kN))

    # --- Distributed self-weight on bottom chord ---
    if dl_q_kn_m != 0:
        for eid in bot_chord_ids:
            ss.q_load(eid, dl_q_kn_m)

    mapping = {
        "Top Chord": top_chord_ids,
        "Bottom Chord": bot_chord_ids,
        "Verticals": vert_ids,
        "Diagonals": diag_ids,
    }

    return ss, mapping
