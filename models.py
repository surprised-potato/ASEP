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