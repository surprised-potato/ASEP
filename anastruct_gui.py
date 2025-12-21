import sys
import numpy as np

# --- CRITICAL: Matplotlib Backend Configuration ---
import matplotlib
matplotlib.use('QtAgg')  # Force Matplotlib to use the QtAgg backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
# --------------------------------------------------

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox, QFormLayout, 
    QComboBox, QSlider, QScrollArea, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt

from anastruct import SystemElements

class StructuralApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnaStruct Desktop GUI - PyQt6 (Fixed Backend)")
        self.setGeometry(100, 100, 1200, 800)

        # Backend Management: Persistent SystemElements object
        self.ss = SystemElements()
        
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- SIDEBAR (Controls) ---
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setFixedWidth(350)
        sidebar_scroll.setWidgetResizable(True)
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Section: Global Defaults
        globals_group = QGroupBox("Global Material Properties")
        globals_form = QFormLayout()
        self.ea_input = QLineEdit("5000")
        self.ei_input = QLineEdit("10000")
        globals_form.addRow("EA (Axial Rigidity):", self.ea_input)
        globals_form.addRow("EI (Flexural Rigidity):", self.ei_input)
        globals_group.setLayout(globals_form)
        sidebar_layout.addWidget(globals_group)

        # Tabs for Construction Methods
        self.tabs = QTabWidget()
        
        # Tab 1: Manual Entry
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        self.x1, self.y1 = QLineEdit("0"), QLineEdit("0")
        self.x2, self.y2 = QLineEdit("0"), QLineEdit("5")
        manual_btn = QPushButton("Add Element")
        manual_btn.clicked.connect(self.add_manual_element)
        manual_layout.addWidget(QLabel("Start (X, Y)"))
        manual_layout.addWidget(self.x1); manual_layout.addWidget(self.y1)
        manual_layout.addWidget(QLabel("End (X, Y)"))
        manual_layout.addWidget(self.x2); manual_layout.addWidget(self.y2)
        manual_layout.addWidget(manual_btn)
        self.tabs.addTab(manual_tab, "Manual")

        # Tab 2: Truss Tower Builder (Ref: Example 4)
        tower_tab = QWidget()
        tower_form = QFormLayout(tower_tab)
        self.tower_width = QLineEdit("6")
        self.tower_span = QLineEdit("30")
        tower_btn = QPushButton("Generate Towers")
        tower_btn.clicked.connect(self.build_truss_towers)
        tower_form.addRow("Width:", self.tower_width)
        tower_form.addRow("Span:", self.tower_span)
        tower_form.addWidget(tower_btn)
        self.tabs.addTab(tower_tab, "Tower Grid")

        sidebar_layout.addWidget(self.tabs)

        # Section: Supports
        supports_group = QGroupBox("Supports")
        supports_form = QFormLayout()
        self.support_node_id = QLineEdit("1")
        self.support_type = QComboBox()
        self.support_type.addItems(["Hinged", "Fixed", "Roll", "Spring"])
        self.support_type.currentTextChanged.connect(self.update_support_ui)
        
        self.k_input = QLineEdit("5000")
        self.k_input.setEnabled(False)
        
        add_support_btn = QPushButton("Apply Support")
        add_support_btn.clicked.connect(self.apply_support)
        
        supports_form.addRow("Node ID:", self.support_node_id)
        supports_form.addRow("Type:", self.support_type)
        supports_form.addRow("Stiffness k:", self.k_input)
        supports_form.addRow(add_support_btn)
        supports_group.setLayout(supports_form)
        sidebar_layout.addWidget(supports_group)

        # Section: Loads
        loads_group = QGroupBox("Loads")
        loads_form = QFormLayout()
        
        self.load_type = QComboBox()
        self.load_type.addItems(["Point Load", "Moment", "q-Load"])
        self.load_type.currentTextChanged.connect(self.update_load_ui)
        
        self.load_id_input = QLineEdit("1")
        self.load_val1 = QLineEdit("10")
        self.load_val2 = QLineEdit("0")
        self.load_dir = QComboBox()
        self.load_dir.addItems(["y", "x", "perpendicular", "parallel"])
        
        add_load_btn = QPushButton("Apply Load")
        add_load_btn.clicked.connect(self.apply_load)
        
        self.lbl_load_id = QLabel("Node ID:")
        self.lbl_val1 = QLabel("Fx (kN):")
        self.lbl_val2 = QLabel("Fz (kN):")
        self.lbl_dir = QLabel("Direction:")
        
        loads_form.addRow("Load Type:", self.load_type)
        loads_form.addRow(self.lbl_load_id, self.load_id_input)
        loads_form.addRow(self.lbl_val1, self.load_val1)
        loads_form.addRow(self.lbl_val2, self.load_val2)
        loads_form.addRow(self.lbl_dir, self.load_dir)
        loads_form.addRow(add_load_btn)
        
        # Initial state
        self.lbl_dir.hide()
        self.load_dir.hide()
        
        loads_group.setLayout(loads_form)
        sidebar_layout.addWidget(loads_group)

        # Solver Controls
        solve_btn = QPushButton("SOLVE SYSTEM")
        solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        solve_btn.clicked.connect(self.solve_system)
        sidebar_layout.addWidget(solve_btn)

        reset_btn = QPushButton("Reset Structure")
        reset_btn.clicked.connect(self.reset_system)
        sidebar_layout.addWidget(reset_btn)

        sidebar_scroll.setWidget(sidebar_widget)
        layout.addWidget(sidebar_scroll)

        # --- CENTRAL CANVAS (Visualization) ---
        viz_layout = QVBoxLayout()
        # Create figure managed by pyplot
        self.figure, self.ax = plt.subplots()
        # Use the canvas that pyplot created to maintain the manager link
        self.canvas = self.figure.canvas
        viz_layout.addWidget(self.canvas)

        # Viz Toggles
        controls_hbox = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100)
        self.scale_slider.setValue(10)
        self.scale_slider.valueChanged.connect(self.update_plot)
        
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Structure", "Displacement", "Axial Force", "Bending Moment"])
        self.view_mode.currentTextChanged.connect(self.update_plot)
        
        controls_hbox.addWidget(QLabel("Viz Mode:"))
        controls_hbox.addWidget(self.view_mode)
        controls_hbox.addWidget(QLabel("Scale Factor:"))
        controls_hbox.addWidget(self.scale_slider)
        
        viz_layout.addLayout(controls_hbox)
        layout.addLayout(viz_layout, stretch=1)

    # --- LOGIC METHODS ---

    def get_material(self):
        return float(self.ea_input.text()), float(self.ei_input.text())

    def reset_system(self):
        self.ss = SystemElements()
        self.update_plot()

    def add_manual_element(self):
        try:
            ea, ei = self.get_material()
            p1 = [float(self.x1.text()), float(self.y1.text())]
            p2 = [float(self.x2.text()), float(self.y2.text())]
            self.ss.add_element(location=[p1, p2], EA=ea, EI=ei)
            self.update_plot()
            
            # Move end node to start node
            self.x1.setText(self.x2.text())
            self.y1.setText(self.y2.text())
            self.x2.setFocus()
            self.x2.selectAll()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_truss_towers(self):
        """Internalized logic for triangle-based towers"""
        try:
            self.ss = SystemElements() 
            width = float(self.tower_width.text())
            span = float(self.tower_span.text())
            ea, ei = self.get_material()
            
            y = np.arange(1, 6) * np.pi 
            x = np.cos(y) * width * 0.5
            x -= x.min()

            for length in [0, span]:
                self.ss.add_element_grid(x + length, y, element_type='truss', EA=ea)
                x_left = np.ones(y[::2].shape) * x.min() + length
                self.ss.add_element_grid(x_left, y[::2], element_type='truss', EA=ea)
            
            self.ss.add_element_grid([0, width, span, span + width], np.ones(4) * y.max(), EI=ei)
            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def apply_support(self):
        try:
            nid = int(self.support_node_id.text())
            stype = self.support_type.currentText()
            if stype == "Hinged":
                self.ss.add_support_hinged(node_id=nid)
            elif stype == "Fixed":
                self.ss.add_support_fixed(node_id=nid)
            elif stype == "Roll":
                self.ss.add_support_roll(node_id=nid, direction=2)
            elif stype == "Spring":
                self.ss.add_support_spring(node_id=nid, translation=2, k=float(self.k_input.text()))
            self.update_plot()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", "Ensure Node ID exists.")

    def update_support_ui(self, text):
        self.k_input.setEnabled(text == "Spring")

    def update_load_ui(self, text):
        if text == "Point Load":
            self.lbl_load_id.setText("Node ID:")
            self.lbl_val1.setText("Fx (kN):")
            self.lbl_val2.setText("Fz (kN):")
            self.lbl_val2.show()
            self.load_val2.show()
            self.lbl_dir.hide()
            self.load_dir.hide()
        elif text == "Moment":
            self.lbl_load_id.setText("Node ID:")
            self.lbl_val1.setText("Moment (kNm):")
            self.lbl_val2.hide()
            self.load_val2.hide()
            self.lbl_dir.hide()
            self.load_dir.hide()
        elif text == "q-Load":
            self.lbl_load_id.setText("Element ID:")
            self.lbl_val1.setText("q (kN/m):")
            self.lbl_val2.hide()
            self.load_val2.hide()
            self.lbl_dir.show()
            self.load_dir.show()

    def apply_load(self):
        try:
            ltype = self.load_type.currentText()
            oid = int(self.load_id_input.text())
            val1 = float(self.load_val1.text())
            
            if ltype == "Point Load":
                val2 = float(self.load_val2.text())
                self.ss.point_load(node_id=oid, Fx=val1, Fz=val2)
            elif ltype == "Moment":
                self.ss.moment_load(node_id=oid, Ty=val1)
            elif ltype == "q-Load":
                direction = self.load_dir.currentText()
                self.ss.q_load(q=val1, element_id=oid, direction=direction)
            
            self.update_plot()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def solve_system(self):
        if not self.ss.element_map:
            return
        try:
            self.ss.solve()
            QMessageBox.information(self, "Success", "Analysis Complete.")
            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Solver Error", str(e))

    def update_plot(self):
        # Clear the axes for the new plot
        self.ax.clear()
        
        # Check if there are elements to plot
        if not self.ss.element_map:
            self.canvas.draw()
            return

        # --- KEY FIX: Inject our axes into anastruct's plotter ---
        # anastruct's plotter expects a list of axes. 
        # We must use gridplot=True to prevent anastruct from creating a new figure.
        self.ss.plotter.axes = [self.ax]
        self.ss.plotter.fig = self.figure
        
        # Get current figure size to maintain aspect ratio logic in anastruct
        current_figsize = self.figure.get_size_inches()

        mode = self.view_mode.currentText()
        factor = self.scale_slider.value()

        try:
            if mode == "Structure":
                self.ss.plotter.plot_structure(
                    figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                )
            elif mode == "Displacement":
                self.ss.plotter.displacements(
                    factor=factor, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Axial Force":
                self.ss.plotter.axial_force(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Bending Moment":
                self.ss.plotter.bending_moment(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
        except Exception as e:
            # Fallback to structure view if results aren't available yet
            print(f"Plotting error: {e}")
            try:
                self.ss.plotter.plot_structure(
                    figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                )
            except Exception:
                pass
        
        # Refresh the canvas
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StructuralApp()
    window.show()
    sys.exit(app.exec())