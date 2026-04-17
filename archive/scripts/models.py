from anastruct import SystemElements

class FrameModel:
    """Stores the blueprint of the structural model, insulated from anastruct's internal state."""
    def __init__(self):
        self.elements = []      # [{'loc': [[x1,y1],[x2,y2]], 'EA':..., 'EI':...}]
        self.supports = []      # [{'loc': [x,y], 'type': str, 'args': dict}]
        self.point_loads = []   # [{'loc': [x,y], 'Fx': float, 'Fz': float}]
        self.moment_loads = []  # [{'loc': [x,y], 'Ty': float}]
        self.q_loads = []       # [{'element_idx': int, 'q': val, 'dir': str, 'qp': val}]
        self.system = SystemElements()

    def clear(self):
        self.elements.clear()
        self.supports.clear()
        self.point_loads.clear()
        self.moment_loads.clear()
        self.q_loads.clear()
        self.system = SystemElements()

class BuildingModel:
    """Stores the global configuration of the building: grid, levels, and frame assignments."""
    def __init__(self):
        self.grid_x = []  # List of floats (spacings)
        self.grid_y = []  # List of floats (spacings)
        self.levels = []  # List of dicts: {'name': str, 'elevation': float}
        self.assignments = [] # List of dicts: {'line': str, 'frame': str, 'offset': float}
        self.slabs = {} # {name: {'points': [(x_idx, y_idx), ...], 'load': float, 'level_height': float}}
        self.consolidated_results = {} # {(x_idx, y_idx, level_idx): {'N': float, 'Mx': float, 'My': float, ...}}