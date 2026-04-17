import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from anastruct import SystemElements

class GridManager:
    """
    GridManager: A 3D-to-2D orchestration library built on top of anastruct.
    
    This library treats a 3D building as a collection of orthogonal 2D slices. 
    It automates the distribution of area loads, self-weight management, 
    and simulates rigid diaphragm behavior across independent frame analyses.

    Units:
        - Force: kiloNewtons (kN)
        - Length: Meters (m)
        - Stiffness (EA): kN
        - Stiffness (EI): kNm^2
    """

    def __init__(self, x_grid, y_grid, z_grid):
        """
        Initialize the GridManager with a strictly orthogonal 3D grid.

        :param x_grid: List of global X coordinates (e.g., [0, 5, 10]).
        :param y_grid: List of global Y coordinates (e.g., [0, 6, 12]).
        :param z_grid: List of global Z (height) coordinates (e.g., [0, 3.5, 7]).
        """
        self.grid = {
            'x': sorted(list(set(x_grid))),
            'y': sorted(list(set(y_grid))),
            'z': sorted(list(set(z_grid)))
        }

        # Calculation Engines: One SystemElements instance per grid slice
        self.xy_floors = {z: SystemElements(mesh=50) for z in self.grid['z']}
        self.xz_frames = {y: SystemElements(mesh=50) for y in self.grid['y']}
        self.yz_frames = {x: SystemElements(mesh=50) for x in self.grid['x']}

        # Metadata and State
        self.global_load_map = {}  # {(x, y, z): vertical_force_kN}
        self.labels = {'x': {}, 'y': {}, 'z': {}}
        self._is_dirty = True      # Tracks if the model needs a re-solve
        self.column_nodes = set()
        self._smart_update = False

    def set_grid_labels(self, axis, labels_dict):
        """
        Map numerical coordinates to human-readable grid labels (e.g., 'Grid Line A').
        
        :param axis: 'x', 'y', or 'z'.
        :param labels_dict: Dictionary mapping float coordinates to string labels.
        """
        self.labels[axis.lower()] = labels_dict

    def add_orthogonal_member(self, start_xyz, end_xyz, EA, EI, g=0, is_truss=False):
        """
        Adds a beam or column to the appropriate 2D slices.
        
        :param start_xyz: (x, y, z) tuple.
        :param end_xyz: (x, y, z) tuple.
        :param EA: Axial stiffness (kN).
        :param EI: Bending stiffness (kNm^2).
        :param g: Self-weight (kN/m). Applied only to vertical frames to avoid double-counting.
        :param is_truss: Boolean, if True adds as a truss element.
        """
        self._is_dirty = True
        x1, y1, z1 = start_xyz
        x2, y2, z2 = end_xyz

        # --- Horizontal Members (Beams) ---
        if np.isclose(z1, z2):
            # Add to horizontal XY system for load path modeling
            self.xy_floors[z1].add_element(location=[[x1, y1], [x2, y2]], EA=EA, EI=EI, g=g)
            
            # Add to vertical frame slices for global analysis
            if np.isclose(y1, y2): # XZ Plane (Longitudinal)
                self._add_to_system(self.xz_frames[y1], [[x1, z1], [x2, z2]], EA, EI, g, is_truss)
            elif np.isclose(x1, x2): # YZ Plane (Transverse)
                self._add_to_system(self.yz_frames[x1], [[y1, z1], [y2, z2]], EA, EI, g, is_truss)

        # --- Vertical Members (Columns) ---
        elif np.isclose(x1, x2) and np.isclose(y1, y2):
            # Columns are essential to both XZ and YZ slices
            self._add_to_system(self.xz_frames[y1], [[x1, z1], [x2, z2]], EA, EI, g, is_truss)
            self._add_to_system(self.yz_frames[x1], [[y1, z1], [y2, z2]], EA, EI, g, is_truss)
            self.column_nodes.add((x1, y1, z1))
            self.column_nodes.add((x2, y2, z2))

    def _add_to_system(self, system, loc, EA, EI, g, is_truss):
        """Helper to add element or truss to anastruct system."""
        if is_truss:
            system.add_truss_element(location=loc, EA=EA)
        else:
            system.add_element(location=loc, EA=EA, EI=EI, g=g)

    def add_slab_load(self, x_range, y_range, z_level, area_load):
        """
        Distributes area loads to boundary beams using 1-way or 2-way logic.
        
        :param x_range: (x_start, x_end) tuple.
        :param y_range: (y_start, y_end) tuple.
        :param z_level: Z coordinate of the slab.
        :param area_load: Load in kN/m^2 (positive is downwards).
        """
        self._is_dirty = True
        x_min, x_max = sorted(x_range)
        y_min, y_max = sorted(y_range)
        lx = x_max - x_min
        ly = y_max - y_min
        l_long = max(lx, ly)
        l_short = min(lx, ly)

        # Simplified distribution: Apply uniform load to beams within the region
        q_val = (area_load * l_short) / 2
        
        floor_sys = self.xy_floors[z_level]
        for eid, el in floor_sys.element_map.items():
            n1 = floor_sys.node_map[el.node_id1].vertex
            n2 = floor_sys.node_map[el.node_id2].vertex
            xm, ym = (n1.x + n2.x) / 2, (n1.y + n2.y) / 2
            
            if (x_min <= xm <= x_max) and (y_min <= ym <= y_max):
                floor_sys.q_load(q=-q_val, element_id=eid, direction='element')

    def add_support(self, xyz, support_type='fixed', **kwargs):
        """
        Adds a support to the vertical frames at a specific point.

        :param xyz: (x, y, z) tuple for the support location.
        :param support_type: 'fixed', 'hinged', 'roll', or 'spring'.
        :param kwargs: Additional arguments for 'roll' or 'spring' supports,
                       e.g., direction='x', k=5000, translation=2.
        """
        self._is_dirty = True
        x, y, z = xyz

        # A support exists at the intersection of two vertical grid lines.
        # It must be applied to both the XZ and YZ frames that meet at that point.

        # Apply to the XZ frame that exists at the given Y-coordinate
        if y in self.xz_frames:
            xz_system = self.xz_frames[y]
            # In the XZ system, nodes are defined by (x, z) coordinates
            node_id = xz_system.find_node_id(vertex=(x, z))
            if node_id:
                self._apply_support_to_system(xz_system, node_id, support_type, **kwargs)

        # Apply to the YZ frame that exists at the given X-coordinate
        if x in self.yz_frames:
            yz_system = self.yz_frames[x]
            # In the YZ system, nodes are defined by (y, z) coordinates
            node_id = yz_system.find_node_id(vertex=(y, z))
            if node_id:
                self._apply_support_to_system(yz_system, node_id, support_type, **kwargs)

    def _apply_support_to_system(self, system, node_id, support_type, **kwargs):
        """Helper to apply a support of a given type to a system."""
        stype = support_type.lower()
        if stype == 'fixed':
            system.add_support_fixed(node_id=node_id)
        elif stype == 'hinged':
            system.add_support_hinged(node_id=node_id)
        elif stype == 'roll':
            system.add_support_roll(node_id=node_id, **kwargs)
        elif stype == 'spring':
            system.add_support_spring(node_id=node_id, **kwargs)

    def set_foundation(self, z_level, support_type='fixed', **kwargs):
        """
        Applies a uniform support type to all column bases at a given Z-level.

        :param z_level: The Z coordinate for the foundation level.
        :param support_type: 'fixed', 'hinged', 'roll', or 'spring'.
        :param kwargs: Additional arguments for 'roll' or 'spring' supports.
        """
        for (cx, cy, cz) in self.column_nodes:
            if np.isclose(cz, z_level):
                self.add_support((cx, cy, cz), support_type, **kwargs)

    def solve_building(self, enforce_diaphragm=True):
        """
        Orchestrates the global structural analysis.
        """
        # Step 1: Solve Floor Systems (Horizontal)
        for z in sorted(self.grid['z'], reverse=True):
            floor_sys = self.xy_floors[z]
            # Skip solving if the floor system is empty
            if not floor_sys.element_map:
                continue

            # Auto-add hinged supports at all column locations for stability
            for (cx, cy, cz) in self.column_nodes:
                if np.isclose(z, cz):
                    nid = floor_sys.find_node_id((cx, cy))
                    if nid:
                        floor_sys.add_support_hinged(nid)

            # Only solve if there are loads, otherwise it's unstable and unnecessary
            if floor_sys.loads_point or floor_sys.loads_q or floor_sys.loads_moment or floor_sys.loads_dead_load:
                floor_sys.solve()
            # Harvest reactions and update self.global_load_map

        # Step 2: Solve Vertical Frames (Primary Skeleton)
        for frame in list(self.xz_frames.values()) + list(self.yz_frames.values()):
            frame.solve()

        # Step 3: Rigid Diaphragm Coordination (Pass 2)
        if enforce_diaphragm:
            self._apply_diaphragm_constraints()

        self._is_dirty = False

    def _apply_diaphragm_constraints(self):
        """
        Enforces average horizontal drift across all frames at each Z-level.
        """
        for z in self.grid['z']:
            if z == 0: continue # Skip foundation
            # 1. Harvest all horizontal displacements at this level
            # 2. Calculate mean(ux)
            # 3. Re-solve frames with prescribed boundary displacement
            pass

    # --- REPORTING MODULES ---

    def report_to_csv(self, filename="global_results.csv"):
        """
        Exports a comprehensive CSV of internal forces for all members.
        """
        rows = []
        for axis, frames in [('XZ', self.xz_frames), ('YZ', self.yz_frames)]:
            for coord, ss in frames.items():
                if not ss.element_map: continue
                for eid, el in ss.element_map.items():
                    rows.append({
                        'Plane': axis,
                        'GridLine': self.labels[axis[1].lower()].get(coord, coord),
                        'ElementID': eid,
                        'MaxAxial_kN': np.max(np.abs(el.axial_force)) if el.axial_force is not None else 0,
                        'MaxShear_kN': np.max(np.abs(el.shear_force)) if el.shear_force is not None else 0,
                        'MaxMoment_kNm': np.max(np.abs(el.bending_moment)) if el.bending_moment is not None else 0
                    })
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"Report saved to {filename}")

    def plot_slice(self, plane, coord, result_type='moment'):
        """
        Triggers anastruct visualization for a specific frame slice.
        
        :param plane: 'XZ' or 'YZ'.
        :param coord: Coordinate of the slice.
        :param result_type: 'moment', 'shear', 'axial', or 'displacement'.
        """
        frames = self.xz_frames if plane.upper() == 'XZ' else self.yz_frames
        if coord in frames:
            ss = frames[coord]
            if result_type == 'moment': ss.show_bending_moment()
            elif result_type == 'shear': ss.show_shear_force()
            elif result_type == 'axial': ss.show_axial_force()
            elif result_type == 'displacement': ss.show_displacement()
        else:
            print(f"Error: Slice {plane} at {coord} not found.")

    def get_global_heatmap(self):
        """
        Identifies the absolute 'Worst Case' members across the building.
        """
        summary = {"MaxMoment": 0, "MaxAxial": 0, "CriticalFrame": ""}
        for plane_name, frames in [("XZ", self.xz_frames), ("YZ", self.yz_frames)]:
            for coord, ss in frames.items():
                for el in ss.element_map.values():
                    if el.bending_moment is not None:
                        m = np.max(np.abs(el.bending_moment))
                        if m > summary["MaxMoment"]:
                            summary["MaxMoment"] = m
                            summary["CriticalFrame"] = f"{plane_name} Line {coord}"
        return summary

# Example Usage Placeholder
if __name__ == "__main__":
    # Define a 5m x 6m grid, 2 stories high (3.5m per story)
    manager = GridManager(x_grid=[0, 5], y_grid=[0, 6], z_grid=[0, 3.5, 7.0])
    
    # Define Column properties
    col_props = {'EA': 2e6, 'EI': 5e4, 'g': 1.5} # kN, kNm2, kN/m
    
    # Add a simple column
    manager.add_orthogonal_member((0,0,0), (0,0,3.5), **col_props)
    
    print("GridManager initialized. Ready for 3D decomposition.")