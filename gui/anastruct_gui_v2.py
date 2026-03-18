import sys
import copy
import string
import numpy as np
import json
import warnings
import traceback

# Suppress Matplotlib aspect ratio warnings
warnings.filterwarnings("ignore", message=".*Ignoring fixed y limits.*")

# --- Matplotlib Backend ---
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox, QFormLayout, 
    QComboBox, QSlider, QScrollArea, QMessageBox, QTabWidget, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QInputDialog, QGridLayout, QStackedWidget, QSizePolicy,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt

from anastruct import SystemElements
from models import FrameModel, BuildingModel
from widgets import ElementManagerWidget
from plotter import StructuralPlotter

class StructuralAppV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnaStruct Desktop GUI v2 - Building Workflow")
        self.setGeometry(100, 100, 1280, 850)

        # --- Data Model ---
        # 1. Frame Templates: The geometric blueprints (nodes, elements, supports)
        self.frames = {"Portal Frame": FrameModel()} # Aliased as templates
        self.current_frame_name = "Portal Frame"
        
        # 2. Building Definition
        self.building = BuildingModel()
        
        # 3. Analysis Results: Map grid_line_label -> SystemElements (solved)
        self.analysis_results = {} 
        self.current_analysis_label = None

        # 4. Current System (for Plotter/Editor compatibility)
        # This switches between a Template (editing) and a Result (viewing)
        self.ss = self.frames[self.current_frame_name].system

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        # --- Visualization (Right Panel) ---
        viz_container = QWidget()
        viz_layout = QVBoxLayout(viz_container)
        
        # Plotter Canvas
        self.figure, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.canvas = self.figure.canvas
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        viz_layout.addWidget(self.canvas)

        # Visualization Controls
        controls_layout = QHBoxLayout()
        
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Structure", "Displacement", "Axial Force", "Shear Force", "Bending Moment", "Grid Plan", "3D Wireframe", "Member Analysis"])
        self.view_mode.currentTextChanged.connect(self.on_view_mode_changed)
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100)
        self.scale_slider.setValue(10)
        self.scale_slider.setFixedWidth(100)
        
        self.floor_selector = QComboBox() # For Grid Plan
        self.member_selector = QComboBox() # For Member Analysis
        self.member_selector.setVisible(False)

        # Toggles
        self.show_grid = QCheckBox("Grid"); self.show_grid.setChecked(True)
        self.show_ticks = QCheckBox("Ticks"); self.show_ticks.setChecked(True)
        self.show_grid_labels = QCheckBox("Labels"); self.show_grid_labels.setChecked(True)
        self.show_beam_marks = QCheckBox("Marks")
        self.lock_3d_rotation = QCheckBox("Lock 3D")

        controls_layout.addWidget(QLabel("View:"))
        controls_layout.addWidget(self.view_mode)
        controls_layout.addWidget(self.member_selector)
        controls_layout.addWidget(self.floor_selector)
        controls_layout.addWidget(QLabel("Scale:"))
        controls_layout.addWidget(self.scale_slider)
        controls_layout.addWidget(self.show_grid)
        controls_layout.addWidget(self.show_ticks)
        controls_layout.addWidget(self.show_grid_labels)
        controls_layout.addWidget(self.show_beam_marks)
        controls_layout.addWidget(self.lock_3d_rotation)
        controls_layout.addStretch()
        
        viz_layout.addLayout(controls_layout)

        # --- Initialize Plotter ---
        self.plotter = StructuralPlotter(self)
        
        # --- Workflow Tabs (Left Panel) ---
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(450)
        
        self.init_tab_grid()
        self.init_tab_frames()
        self.init_tab_slabs()
        self.init_tab_analysis()
        self.init_tab_results()

        main_layout.addWidget(self.tabs)
        main_layout.addWidget(viz_container)
        
        # Connect Plotter Signals
        self.scale_slider.valueChanged.connect(self.plotter.update_plot)
        self.show_grid.stateChanged.connect(self.plotter.update_plot)
        self.show_ticks.stateChanged.connect(self.plotter.update_plot)
        self.show_grid_labels.stateChanged.connect(self.plotter.update_plot)
        self.show_beam_marks.stateChanged.connect(self.plotter.update_plot)
        self.lock_3d_rotation.stateChanged.connect(self.plotter.update_plot)
        self.floor_selector.currentTextChanged.connect(self.plotter.update_plot)
        self.member_selector.currentTextChanged.connect(self.plotter.update_plot)

        # Initial State
        self.update_floor_levels()
        self.tabs.setCurrentIndex(0)

    # ----------------------------------------------------------------------
    # TAB 1: GRID DEFINITION
    # ----------------------------------------------------------------------
    def init_tab_grid(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # X/Y Grid
        grp_xy = QGroupBox("Plan Grid")
        form_xy = QFormLayout()
        self.grid_x_input = QLineEdit("6, 6")
        self.grid_y_input = QLineEdit("5, 5, 5")
        self.grid_x_input.textChanged.connect(self.plotter.update_plot)
        self.grid_y_input.textChanged.connect(self.plotter.update_plot)
        form_xy.addRow("X Spacings (m):", self.grid_x_input)
        form_xy.addRow("Y Spacings (m):", self.grid_y_input)
        grp_xy.setLayout(form_xy)
        layout.addWidget(grp_xy)

        # Z Levels
        grp_z = QGroupBox("Levels (Z)")
        vbox_z = QVBoxLayout()
        self.grid_z_table = QTableWidget(3, 2)
        self.grid_z_table.setHorizontalHeaderLabels(["Name", "Elevation (m)"])
        self.grid_z_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid_z_table.setItem(0, 0, QTableWidgetItem("Foundation")); self.grid_z_table.setItem(0, 1, QTableWidgetItem("-1.5"))
        self.grid_z_table.setItem(1, 0, QTableWidgetItem("Ground")); self.grid_z_table.setItem(1, 1, QTableWidgetItem("0.0"))
        self.grid_z_table.setItem(2, 0, QTableWidgetItem("Roof")); self.grid_z_table.setItem(2, 1, QTableWidgetItem("3.5"))
        self.grid_z_table.itemChanged.connect(self.update_floor_levels)
        
        btn_z_add = QPushButton("Add Level")
        btn_z_add.clicked.connect(self.add_level)
        btn_z_del = QPushButton("Remove Level")
        btn_z_del.clicked.connect(self.remove_level)
        
        hbox_z = QHBoxLayout()
        hbox_z.addWidget(btn_z_add)
        hbox_z.addWidget(btn_z_del)
        
        vbox_z.addWidget(self.grid_z_table)
        vbox_z.addLayout(hbox_z)
        grp_z.setLayout(vbox_z)
        layout.addWidget(grp_z)
        
        layout.addStretch()
        self.tabs.addTab(tab, "1. Grid")

    def add_level(self):
        row = self.grid_z_table.rowCount()
        self.grid_z_table.insertRow(row)
        prev_h = float(self.grid_z_table.item(row-1, 1).text()) if row > 0 else 0.0
        self.grid_z_table.setItem(row, 0, QTableWidgetItem(f"Level {row}"))
        self.grid_z_table.setItem(row, 1, QTableWidgetItem(str(prev_h + 3.0)))
        self.update_floor_levels()

    def remove_level(self):
        if self.grid_z_table.rowCount() > 0:
            self.grid_z_table.removeRow(self.grid_z_table.rowCount()-1)
            self.update_floor_levels()

    def update_floor_levels(self):
        self.floor_selector.blockSignals(True)
        self.floor_selector.clear()
        levels = []
        for r in range(self.grid_z_table.rowCount()):
            try:
                name = self.grid_z_table.item(r, 0).text()
                elev = float(self.grid_z_table.item(r, 1).text())
                levels.append((elev, name))
            except: pass
        levels.sort()
        for elev, name in levels:
            self.floor_selector.addItem(f"{name} ({elev}m)")
        self.floor_selector.blockSignals(False)
        self.plotter.update_plot()

    # ----------------------------------------------------------------------
    # TAB 2: FRAME TEMPLATES
    # ----------------------------------------------------------------------
    def init_tab_frames(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Template Management
        hbox_mng = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItems(list(self.frames.keys()))
        self.template_combo.currentTextChanged.connect(self.switch_frame_template)
        
        btn_new = QPushButton("New")
        btn_new.clicked.connect(self.add_frame_template)
        btn_del = QPushButton("Delete")
        btn_del.clicked.connect(self.delete_frame_template)
        
        hbox_mng.addWidget(QLabel("Template:"))
        hbox_mng.addWidget(self.template_combo)
        hbox_mng.addWidget(btn_new)
        hbox_mng.addWidget(btn_del)
        layout.addLayout(hbox_mng)
        
        # --- NEW: Frame Generators ---
        gen_group = QGroupBox("Frame Generators")
        gen_layout = QVBoxLayout(gen_group)
        
        self.gen_selector = QComboBox()
        self.gen_selector.addItems(["Portal Frame", "Multi-bay Grid", "Pitched Truss"])
        gen_layout.addWidget(self.gen_selector)
        
        self.gen_stack = QStackedWidget()
        gen_layout.addWidget(self.gen_stack)
        self.gen_selector.currentIndexChanged.connect(self.gen_stack.setCurrentIndex)
        
        # Generator 1: Portal Frame
        portal_tab = QWidget()
        portal_form = QFormLayout(portal_tab)
        self.portal_w = QLineEdit("12.0")
        self.portal_h1 = QLineEdit("4.0")
        self.portal_h2 = QLineEdit("5.5")
        self.portal_sups = QComboBox(); self.portal_sups.addItems(["Fixed", "Hinged"])
        btn_gen_portal = QPushButton("Generate Portal Frame")
        btn_gen_portal.clicked.connect(self.generate_portal_frame)
        portal_form.addRow("Width (m):", self.portal_w)
        portal_form.addRow("Eave Height (m):", self.portal_h1)
        portal_form.addRow("Ridge Height (m):", self.portal_h2)
        portal_form.addRow("Supports:", self.portal_sups)
        portal_form.addRow(btn_gen_portal)
        self.gen_stack.addWidget(portal_tab)

        # Generator 2: Multi-bay Grid
        grid_tab = QWidget()
        grid_form = QFormLayout(grid_tab)
        self.grid_bays = QLineEdit("6, 6, 6")
        self.grid_stories = QLineEdit("4, 3.5")
        self.grid_sups = QComboBox(); self.grid_sups.addItems(["Fixed", "Hinged"])
        btn_gen_grid = QPushButton("Generate Multi-bay Frame")
        btn_gen_grid.clicked.connect(self.generate_grid_frame)
        grid_form.addRow("Bay Widths (m):", self.grid_bays)
        grid_form.addRow("Story Heights (m):", self.grid_stories)
        grid_form.addRow("Supports:", self.grid_sups)
        grid_form.addRow(btn_gen_grid)
        self.gen_stack.addWidget(grid_tab)

        # Generator 3: Pitched Truss
        truss_tab = QWidget()
        truss_form = QFormLayout(truss_tab)
        self.truss_span = QLineEdit("20.0")
        self.truss_height = QLineEdit("2.5")
        self.truss_panels = QLineEdit("10")
        btn_gen_truss = QPushButton("Generate Pitched Truss")
        btn_gen_truss.clicked.connect(self.generate_pitched_truss)
        truss_form.addRow("Span (m):", self.truss_span)
        truss_form.addRow("Height at Center (m):", self.truss_height)
        truss_form.addRow("No. of Panels (even):", self.truss_panels)
        truss_form.addRow(btn_gen_truss)
        self.gen_stack.addWidget(truss_tab)

        layout.addWidget(gen_group)
        
        # Element Manager (Reused from V1)
        # We need to ensure ElementManagerWidget points to the current template's system
        self.element_mgr = ElementManagerWidget(self)
        layout.addWidget(self.element_mgr)
        
        self.tabs.addTab(tab, "2. Frames")

    # ----------------------------------------------------------------------
    # FRAME GENERATORS
    # ----------------------------------------------------------------------
    def generate_portal_frame(self):
        try:
            w = float(self.portal_w.text())
            h1 = float(self.portal_h1.text())
            h2 = float(self.portal_h2.text())
            sup_type = self.portal_sups.currentText().lower()
            
            model = self.frames[self.current_frame_name]
            model.clear()
            
            EA, EI = 2.1e11 * 0.05, 2.1e11 * 4e-5 # Some reasonable defaults
            
            # Nodes
            n1, n2, n3, n4, n5 = [0, 0], [0, h1], [w/2, h2], [w, h1], [w, 0]
            
            # Elements
            model.elements.append({'loc': [n1, n2], 'EA': EA, 'EI': EI}) # Column 1
            model.elements.append({'loc': [n2, n3], 'EA': EA, 'EI': EI}) # Rafter 1
            model.elements.append({'loc': [n3, n4], 'EA': EA, 'EI': EI}) # Rafter 2
            model.elements.append({'loc': [n4, n5], 'EA': EA, 'EI': EI}) # Column 2
            
            # Supports
            model.supports.append({'loc': n1, 'type': sup_type, 'args': {}})
            model.supports.append({'loc': n5, 'type': sup_type, 'args': {}})
            
            self.rebuild_system()
            self.element_mgr.refresh_data()
            QMessageBox.information(self, "Success", "Portal frame generated.")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input value: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate frame: {e}")

    def generate_grid_frame(self):
        try:
            bays_str = self.grid_bays.text()
            stories_str = self.grid_stories.text()
            sup_type = self.grid_sups.currentText().lower()
            
            bay_widths = [float(b.strip()) for b in bays_str.split(',') if b.strip()]
            story_heights = [float(h.strip()) for h in stories_str.split(',') if h.strip()]
            
            if not bay_widths or not story_heights:
                raise ValueError("Bay widths and story heights cannot be empty.")
                
            model = self.frames[self.current_frame_name]
            model.clear()
            
            EA, EI = 2.1e11 * 0.05, 2.1e11 * 4e-5 # Defaults
            
            x_coords = [0] + list(np.cumsum(bay_widths))
            y_coords = [0] + list(np.cumsum(story_heights))
            
            # Columns
            for x in x_coords:
                for i in range(len(y_coords) - 1):
                    n1, n2 = [x, y_coords[i]], [x, y_coords[i+1]]
                    model.elements.append({'loc': [n1, n2], 'EA': EA, 'EI': EI})
            
            # Beams
            for y in y_coords[1:]: # Skip ground level
                for i in range(len(x_coords) - 1):
                    n1, n2 = [x_coords[i], y], [x_coords[i+1], y]
                    model.elements.append({'loc': [n1, n2], 'EA': EA, 'EI': EI})
                    
            # Supports
            for x in x_coords:
                model.supports.append({'loc': [x, 0], 'type': sup_type, 'args': {}})
                
            self.rebuild_system()
            self.element_mgr.refresh_data()
            QMessageBox.information(self, "Success", "Multi-bay frame generated.")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input value: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate frame: {e}")

    def generate_pitched_truss(self):
        try:
            span = float(self.truss_span.text())
            height = float(self.truss_height.text())
            panels = int(self.truss_panels.text())
            
            if panels % 2 != 0 or panels < 2:
                raise ValueError("Number of panels must be an even number >= 2.")
                
            model = self.frames[self.current_frame_name]
            model.clear()
            
            EA, EI = 2.1e11 * 0.01, 0 # Truss elements have EI=0
            
            panel_width = span / panels
            nodes = {}
            # Bottom chord nodes
            for i in range(panels + 1): nodes[i] = [i * panel_width, 0]
            # Top chord nodes
            for i in range(panels + 1):
                x = i * panel_width
                y = height * (1 - abs(x - span/2) / (span/2)) # Linear slope to peak
                nodes[i + (panels + 1)] = [x, y]
            
            # Bottom chord elements
            for i in range(panels): model.elements.append({'loc': [nodes[i], nodes[i+1]], 'EA': EA, 'EI': EI})
            # Top chord elements
            for i in range(panels): model.elements.append({'loc': [nodes[i + panels + 1], nodes[i + panels + 2]], 'EA': EA, 'EI': EI})
            # Verticals (excluding ends)
            for i in range(1, panels): model.elements.append({'loc': [nodes[i], nodes[i + panels + 1]], 'EA': EA, 'EI': EI})
            # Diagonals (Pratt-style for gravity)
            for i in range(panels):
                if i < panels / 2: model.elements.append({'loc': [nodes[i], nodes[i + panels + 2]], 'EA': EA, 'EI': EI})
                else: model.elements.append({'loc': [nodes[i+1], nodes[i + panels + 1]], 'EA': EA, 'EI': EI})
                
            # Supports
            model.supports.append({'loc': nodes[0], 'type': 'hinged', 'args': {}})
            model.supports.append({'loc': nodes[panels], 'type': 'roll', 'args': {'direction': 2}})
            
            self.rebuild_system()
            self.element_mgr.refresh_data()
            QMessageBox.information(self, "Success", "Pitched truss generated.")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid input value: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate truss: {e}")

    def add_frame_template(self):
        name, ok = QInputDialog.getText(self, "New Frame", "Frame Name:")
        if ok and name and name not in self.frames:
            self.frames[name] = FrameModel()
            self.template_combo.addItem(name)
            self.template_combo.setCurrentText(name)

    def delete_frame_template(self):
        name = self.template_combo.currentText()
        if len(self.frames) > 1:
            del self.frames[name]
            self.template_combo.removeItem(self.template_combo.currentIndex())
            self.switch_frame_template(self.template_combo.currentText())

    def switch_frame_template(self, name):
        if name not in self.frames: return
        self.current_frame_name = name
        
        # Set current system to the template's system for editing
        self.ss = self.frames[name].system
        
        # Refresh UI
        self.element_mgr.refresh_data()
        self.view_mode.setCurrentText("Structure")
        self.plotter.update_plot()

    # ----------------------------------------------------------------------
    # TAB 3: ASSIGNMENTS & SLABS
    # ----------------------------------------------------------------------
    def init_tab_slabs(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 1. Frame Assignments
        grp_assign = QGroupBox("Assign Frames to Grid Lines")
        vbox_assign = QVBoxLayout()
        self.grid_table = QTableWidget(0, 3)
        self.grid_table.setHorizontalHeaderLabels(["Grid Line", "Frame Template", "Offset"])
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        hbox_assign_btns = QHBoxLayout()
        btn_add_assign = QPushButton("Add Assignment")
        btn_add_assign.clicked.connect(self.add_assignment)
        btn_del_assign = QPushButton("Remove")
        btn_del_assign.clicked.connect(lambda: self.grid_table.removeRow(self.grid_table.currentRow()))
        hbox_assign_btns.addWidget(btn_add_assign)
        hbox_assign_btns.addWidget(btn_del_assign)
        
        vbox_assign.addWidget(self.grid_table)
        vbox_assign.addLayout(hbox_assign_btns)
        grp_assign.setLayout(vbox_assign)
        layout.addWidget(grp_assign)
        
        # 2. Slabs
        grp_slabs = QGroupBox("Slabs & Loads")
        vbox_slabs = QVBoxLayout()
        self.slabs_table = QTableWidget(0, 4)
        self.slabs_table.setHorizontalHeaderLabels(["Name", "Points (e.g. A1,B2)", "Load (kN/m2)", "Level (m)"])
        self.slabs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.slabs_table.itemChanged.connect(self.on_slab_changed)
        
        hbox_slab_btns = QHBoxLayout()
        btn_add_slab = QPushButton("Add Slab")
        btn_add_slab.clicked.connect(self.add_slab)
        btn_del_slab = QPushButton("Remove")
        btn_del_slab.clicked.connect(lambda: self.slabs_table.removeRow(self.slabs_table.currentRow()))
        hbox_slab_btns.addWidget(btn_add_slab)
        hbox_slab_btns.addWidget(btn_del_slab)
        
        vbox_slabs.addWidget(self.slabs_table)
        vbox_slabs.addLayout(hbox_slab_btns)
        grp_slabs.setLayout(vbox_slabs)
        layout.addWidget(grp_slabs)
        
        self.tabs.addTab(tab, "3. Slabs")

    def add_assignment(self):
        row = self.grid_table.rowCount()
        self.grid_table.insertRow(row)
        self.grid_table.setItem(row, 0, QTableWidgetItem("A"))
        
        combo = QComboBox()
        combo.addItems(list(self.frames.keys()))
        self.grid_table.setCellWidget(row, 1, combo)
        self.grid_table.setItem(row, 2, QTableWidgetItem("0.0"))

    def add_slab(self):
        row = self.slabs_table.rowCount()
        self.slabs_table.insertRow(row)
        self.slabs_table.setItem(row, 0, QTableWidgetItem(f"Slab {row+1}"))
        self.slabs_table.setItem(row, 1, QTableWidgetItem("A1, B1, B2, A2"))
        self.slabs_table.setItem(row, 2, QTableWidgetItem("5.0"))
        self.slabs_table.setItem(row, 3, QTableWidgetItem("3.5"))

    # ----------------------------------------------------------------------
    # TAB 4: ANALYSIS
    # ----------------------------------------------------------------------
    def init_tab_analysis(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        lbl_info = QLabel("Analysis Process:\n1. Extract unique frames per grid line.\n2. Calculate tributary loads from slabs.\n3. Solve each frame instance.")
        layout.addWidget(lbl_info)
        
        self.btn_run = QPushButton("RUN ANALYSIS")
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_run.clicked.connect(self.run_analysis)
        layout.addWidget(self.btn_run)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        
        self.tabs.addTab(tab, "4. Analysis")

    def run_analysis(self):
        self.log_list.clear()
        self.analysis_results.clear()
        self.progress.setValue(0)
        
        # 1. Parse Grid
        try:
            sx = [float(s) for s in self.grid_x_input.text().split(',') if s.strip()]
            sy = [float(s) for s in self.grid_y_input.text().split(',') if s.strip()]
            gx = [0.0] + list(np.cumsum(sx))
            gy = [0.0] + list(np.cumsum(sy))
        except ValueError:
            self.log_list.addItem("Error: Invalid grid spacing.")
            return

        # 2. Parse Slabs
        slabs_data = self.parse_slabs()
        
        # 3. Process Assignments
        row_count = self.grid_table.rowCount()
        if row_count == 0:
            self.log_list.addItem("No frames assigned.")
            return

        for i in range(row_count):
            line_label = self.grid_table.item(i, 0).text().upper()
            template_name = self.grid_table.cellWidget(i, 1).currentText()
            try: offset = float(self.grid_table.item(i, 2).text())
            except: offset = 0.0
            
            self.log_list.addItem(f"Processing {line_label} using {template_name}...")
            QApplication.processEvents()
            
            # Create Instance
            if template_name not in self.frames: continue
            template_model = self.frames[template_name]
            
            # Rebuild a fresh system for this instance
            ss_instance = SystemElements()
            for el in template_model.elements:
                ss_instance.add_element(location=el['loc'], EA=el['EA'], EI=el['EI'])
            for sup in template_model.supports:
                nid = ss_instance.find_node_id(vertex=sup['loc'])
                if nid:
                    if sup['type'] == 'fixed': ss_instance.add_support_fixed(nid)
                    elif sup['type'] == 'hinged': ss_instance.add_support_hinged(nid)
                    elif sup['type'] == 'roll': ss_instance.add_support_roll(nid, direction=sup['args'].get('direction', 2))
            
            # Apply Template Loads (Self-weight, etc defined in template)
            # Note: In V1 loads were in the model. Here we assume template loads are intrinsic.
            # If we want to copy loads from template:
            for q in template_model.q_loads:
                ss_instance.q_load(q=q['q'], element_id=q['element_idx']+1, direction=q['dir'])
            
            # Calculate & Apply Slab Loads
            self.apply_slab_loads(ss_instance, line_label, offset, slabs_data, gx, gy)
            
            # Solve
            try:
                ss_instance.solve()
                self.analysis_results[line_label] = ss_instance
                self.log_list.addItem(f"  -> Solved {line_label}.")
            except Exception as e:
                self.log_list.addItem(f"  -> Failed {line_label}: {e}")
            
            self.progress.setValue(int((i + 1) / row_count * 100))

        self.log_list.addItem("Analysis Complete.")
        self.tabs.setCurrentIndex(4) # Go to Results
        self.refresh_results_tab()

    def parse_slabs(self):
        slabs = []
        for r in range(self.slabs_table.rowCount()):
            try:
                pts_str = self.slabs_table.item(r, 1).text()
                load = float(self.slabs_table.item(r, 2).text())
                level = float(self.slabs_table.item(r, 3).text())
                
                # Parse points A1, B2 etc.
                pts = []
                for p in pts_str.split(','):
                    p = p.strip().upper()
                    if not p: continue
                    # Simple parser: Letter is Y index, Number is X index
                    # Find split between letter and number
                    idx = 0
                    while idx < len(p) and p[idx].isalpha(): idx += 1
                    y_char = p[:idx]
                    x_char = p[idx:]
                    
                    y_idx = string.ascii_uppercase.find(y_char)
                    x_idx = int(x_char) - 1
                    pts.append((x_idx, y_idx))
                
                if pts: slabs.append({'points': pts, 'load': load, 'level': level})
            except: pass
        return slabs

    def apply_slab_loads(self, ss, line_label, offset, slabs, gx, gy):
        # Determine geometry of this line
        is_vert = line_label.isdigit()
        if is_vert:
            line_idx = int(line_label) - 1
            if line_idx >= len(gx): return
            line_pos = gx[line_idx]
        else:
            line_idx = string.ascii_uppercase.find(line_label)
            if line_idx == -1 or line_idx >= len(gy): return
            line_pos = gy[line_idx]

        for slab in slabs:
            # Check if slab is relevant to this line (simple rectangular check)
            # Find slab bounds
            xs = [p[0] for p in slab['points']]
            ys = [p[1] for p in slab['points']]
            
            # Check if line is one of the edges of the slab
            relevant = False
            tributary_width = 0.0
            
            if is_vert:
                if line_idx in xs:
                    # It's a vertical edge. Find adjacent spans.
                    # Simplified: assume rectangular slab between x_min and x_max
                    x_min, x_max = min(xs), max(xs)
                    if line_idx == x_min: tributary_width += (gx[x_min+1] - gx[x_min]) / 2
                    if line_idx == x_max: tributary_width += (gx[x_max] - gx[x_max-1]) / 2
                    # If strictly inside (not edge), it supports both sides
                    if x_min < line_idx < x_max: 
                        tributary_width += (gx[line_idx+1] - gx[line_idx])/2 + (gx[line_idx] - gx[line_idx-1])/2
                    relevant = True
                    span_start = gy[min(ys)]
                    span_end = gy[max(ys)]
            else:
                if line_idx in ys:
                    y_min, y_max = min(ys), max(ys)
                    if line_idx == y_min: tributary_width += (gy[y_min+1] - gy[y_min]) / 2
                    if line_idx == y_max: tributary_width += (gy[y_max] - gy[y_max-1]) / 2
                    if y_min < line_idx < y_max:
                        tributary_width += (gy[line_idx+1] - gy[line_idx])/2 + (gy[line_idx] - gy[line_idx-1])/2
                    relevant = True
                    span_start = gx[min(xs)]
                    span_end = gx[max(xs)]

            if relevant and tributary_width > 0:
                # Apply load to elements at slab level within span
                w = slab['load'] * tributary_width
                # Find elements at slab['level']
                for el in ss.element_map.values():
                    n1 = ss.node_map[el.node_id1].vertex
                    n2 = ss.node_map[el.node_id2].vertex
                    
                    # Check vertical position (must match slab level)
                    if np.isclose(n1.y, slab['level']) and np.isclose(n2.y, slab['level']):
                        # Check horizontal position (must be within span)
                        # Local coordinate of frame corresponds to global perpendicular coord
                        # e.g. if Frame is on Line 1 (Vertical), its local x is Y-global.
                        # We need to map global span to local frame coords.
                        # Assuming frame starts at 0 local x = 0 global perp.
                        # Adjust for offset
                        
                        el_min = min(n1.x, n2.x) + offset
                        el_max = max(n1.x, n2.x) + offset
                        
                        # Check overlap
                        if max(el_min, span_start) < min(el_max, span_end):
                            # Apply load
                            ss.q_load(q=-w, element_id=el.id, direction='y')

    # ----------------------------------------------------------------------
    # TAB 5: RESULTS
    # ----------------------------------------------------------------------
    def init_tab_results(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        hbox_sel = QHBoxLayout()
        self.res_combo = QComboBox()
        self.res_combo.currentTextChanged.connect(self.switch_result_view)
        hbox_sel.addWidget(QLabel("Select Grid Line:"))
        hbox_sel.addWidget(self.res_combo)
        layout.addLayout(hbox_sel)
        
        self.res_table = QTableWidget()
        layout.addWidget(self.res_table)
        
        self.tabs.addTab(tab, "5. Results")

    def refresh_results_tab(self):
        self.res_combo.blockSignals(True)
        self.res_combo.clear()
        self.res_combo.addItems(sorted(self.analysis_results.keys()))
        self.res_combo.blockSignals(False)
        
        if self.res_combo.count() > 0:
            self.switch_result_view(self.res_combo.itemText(0))
            
        # Consolidate Reactions
        self.consolidate_reactions()

    def switch_result_view(self, label):
        if label in self.analysis_results:
            self.current_analysis_label = label
            self.ss = self.analysis_results[label]
            self.view_mode.setCurrentText("Bending Moment")
            self.plotter.update_plot()

    def consolidate_reactions(self):
        # Simple aggregation of reactions for display
        self.res_table.clear()
        self.res_table.setColumnCount(4)
        self.res_table.setHorizontalHeaderLabels(["Grid Line", "Node ID", "Rx (kN)", "Ry (kN)"])
        
        rows = 0
        for label, ss in self.analysis_results.items():
            for nid, node in ss.node_map.items():
                if nid in ss.reaction_forces:
                    rows += 1
        
        self.res_table.setRowCount(rows)
        r = 0
        for label, ss in self.analysis_results.items():
            for nid, node in ss.node_map.items():
                if nid in ss.reaction_forces:
                    reac = ss.reaction_forces[nid]
                    self.res_table.setItem(r, 0, QTableWidgetItem(label))
                    self.res_table.setItem(r, 1, QTableWidgetItem(str(nid)))
                    self.res_table.setItem(r, 2, QTableWidgetItem(f"{reac.Fx:.2f}"))
                    self.res_table.setItem(r, 3, QTableWidgetItem(f"{reac.Fy:.2f}"))
                    r += 1

    # --- Shared Logic ---
    def on_view_mode_changed(self, text):
        if text == "Grid Plan":
            self.floor_selector.setEnabled(True)
        else:
            self.floor_selector.setEnabled(False)
        
        if text == "Member Analysis":
            self.member_selector.setVisible(True)
            self.update_member_list()
        else:
            self.member_selector.setVisible(False)
            
        self.plotter.update_plot()

    def update_member_list(self):
        self.member_selector.clear()
        if self.ss:
            for eid in self.ss.element_map:
                self.member_selector.addItem(f"Element-{eid}")

    def on_slab_changed(self):
        self.building.slabs.clear()
        slabs_list = self.parse_slabs()
        for i, s in enumerate(slabs_list):
            # Use the name from the table if available, otherwise generate one
            name = self.slabs_table.item(i, 0).text() if self.slabs_table.item(i, 0) else f"Slab {i+1}"
            self.building.slabs[name] = s
        if self.view_mode.currentText() == "Grid Plan":
            self.plotter.update_plot()

    # --- Rebuild System (Required by ElementManagerWidget) ---
    def _update_blueprint_from_overrides(self, model, node_coords, element_props, supports_info, loads_info):
        """Updates the FrameModel blueprint using data from Element Manager tables."""
        # Get a map of old node IDs to their coordinates before any changes
        node_map = {nid: node.vertex for nid, node in model.system.node_map.items()}

        # Update element properties (EA, EI)
        if element_props:
            for eid, props in element_props.items():
                if 0 <= eid - 1 < len(model.elements):
                    model.elements[eid - 1]['EA'] = props.get('EA', model.elements[eid - 1]['EA'])
                    model.elements[eid - 1]['EI'] = props.get('EI', model.elements[eid - 1]['EI'])

        # Update node coordinates. This is tricky as it affects all connected items.
        if node_coords:
            for nid, new_coords in node_coords.items():
                old_v = node_map.get(nid)
                if not old_v: continue
                
                old_coords_list = [old_v.x, old_v.y]
                
                # Update elements attached to this node
                for e in model.elements:
                    if np.allclose(e['loc'][0], old_coords_list): e['loc'][0] = new_coords
                    if np.allclose(e['loc'][1], old_coords_list): e['loc'][1] = new_coords
                
                # Update supports at this node
                for s in model.supports:
                    if np.allclose(s['loc'], old_coords_list): s['loc'] = new_coords
                
                # Update loads at this node
                for p in model.point_loads:
                    if np.allclose(p['loc'], old_coords_list): p['loc'] = new_coords
                for m in model.moment_loads:
                    if np.allclose(m['loc'], old_coords_list): m['loc'] = new_coords

        # Recreate supports list from scratch based on table
        if supports_info is not None:
            model.supports = []
            for nid, stype in supports_info.items():
                v = node_map.get(nid)
                if v:
                    new_v_coords = node_coords.get(nid, [v.x, v.y])
                    args = {}
                    if 'roll' in stype.lower():
                        try: args['direction'] = int(stype.split('=')[-1].replace(')', ''))
                        except: args['direction'] = 2
                    elif 'spring' in stype.lower():
                        try: args['k'] = float(stype.split('=')[-1].replace(')', ''))
                        except: args['k'] = 5000
                        args['translation'] = 2
                    model.supports.append({'loc': new_v_coords, 'type': stype.split(' ')[0].lower(), 'args': args})

        # Recreate loads lists from scratch based on table
        if loads_info is not None:
            model.point_loads, model.moment_loads, model.q_loads = [], [], []
            for l in loads_info:
                if l['type'] == 'Point':
                    v = node_map.get(l['id'])
                    if v: model.point_loads.append({'loc': node_coords.get(l['id'], [v.x, v.y]), 'Fx': l['v1'], 'Fz': l['v2']})
                elif l['type'] == 'Moment':
                    v = node_map.get(l['id'])
                    if v: model.moment_loads.append({'loc': node_coords.get(l['id'], [v.x, v.y]), 'Ty': l['v1']})
                elif l['type'] == 'q-Load':
                    model.q_loads.append({'element_idx': l['id'] - 1, 'q': l['v1'], 'dir': l['v2'], 'qp': l.get('v3', 0)})

    def rebuild_system(self, node_coords=None, element_props=None, supports_info=None, loads_info=None):
        # This is called by ElementManagerWidget when editing a template
        # We update the FrameModel blueprint
        model = self.frames[self.current_frame_name]
        
        # Update blueprint based on edits from ElementManagerWidget
        if any([node_coords, element_props, supports_info, loads_info]):
            self._update_blueprint_from_overrides(model, node_coords, element_props, supports_info, loads_info)

        # Re-create the anastruct system from the updated blueprint
        ss = SystemElements()
        def clean_val(v):
            if isinstance(v, (list, tuple, np.ndarray)): return [x if abs(x) > 1e-12 else 0 for x in v]
            return v if not isinstance(v, (int, float)) or abs(v) > 1e-12 else 0

        for e in model.elements: ss.add_element(location=e['loc'], EA=e['EA'], EI=e['EI'])
        for s in model.supports:
            nid = ss.find_node_id(vertex=s['loc'])
            if nid:
                stype = s.get('type', '').lower()
                if stype == 'fixed': ss.add_support_fixed(nid)
                elif stype == 'hinged': ss.add_support_hinged(nid)
                elif stype == 'roll': ss.add_support_roll(nid, direction=s.get('args', {}).get('direction', 2))
                elif stype == 'spring': ss.add_support_spring(nid, translation=s.get('args', {}).get('translation', 2), k=s.get('args', {}).get('k', 5000), roll=s.get('args', {}).get('roll', False))
        for p in model.point_loads:
            nid = ss.find_node_id(vertex=p['loc'])
            if nid: ss.point_load(nid, Fx=clean_val(p.get('Fx', 0)), Fz=clean_val(p.get('Fz', 0)))
        for m in model.moment_loads:
            nid = ss.find_node_id(vertex=m['loc'])
            if nid: ss.moment_load(nid, Ty=clean_val(m.get('Ty', 0)))
        for q in model.q_loads:
            eid = q.get('element_idx', -1) + 1
            if eid in ss.element_map: ss.q_load(q=clean_val(q.get('q')), element_id=eid, direction=q.get('dir', 'element'), q_perp=clean_val(q.get('qp', 0)))

        # Update the main system object for the template
        model.system = ss
        self.ss = ss

        # Refresh UI and plot
        self.update_member_list()
        if self.view_mode.currentText() != "Structure":
            self.view_mode.setCurrentText("Structure")
        else:
            self.plotter.update_plot()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StructuralAppV2()
    window.show()
    sys.exit(app.exec())
