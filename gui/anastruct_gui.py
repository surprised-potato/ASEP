import sys
import string
import numpy as np
import json
import warnings
import traceback

# Suppress Matplotlib aspect ratio warnings during navigation
warnings.filterwarnings("ignore", message=".*Ignoring fixed y limits.*")

# --- CRITICAL: Matplotlib Backend Configuration ---
import matplotlib
matplotlib.use('QtAgg')  # Force Matplotlib to use the QtAgg backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
# --------------------------------------------------

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox, QFormLayout, 
    QComboBox, QSlider, QScrollArea, QMessageBox, QTabWidget, QCheckBox,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QInputDialog, QGridLayout, QStackedWidget, QSizePolicy,
    QFileDialog
)
from PyQt6.QtCore import Qt

from anastruct import SystemElements

from models import FrameModel, BuildingModel
from widgets import ElementManagerWidget
from plotter import StructuralPlotter

class StructuralApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnaStruct Desktop GUI - PyQt6 (Fixed Backend)")
        self.setGeometry(100, 100, 1200, 800)

        # Frame Management
        self.frames = {"Frame 1": FrameModel()}
        self.current_frame_name = "Frame 1"
        self.building = BuildingModel()
        self.ss = self.frames[self.current_frame_name].system
        self.slabs = {} # {name: {'points': [(x_idx, y_idx), ...], 'load': float}}
        
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # --- SIDEBAR (Controls) ---
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # Dropdown for section selection
        self.sidebar_selector = QComboBox()
        self.sidebar_selector.addItems(["Grid", "Frames", "Slabs", "Geometry", "Loads & Supports", "Analysis", "Element Manager", "Test"])
        sidebar_layout.addWidget(QLabel("Select Section:"))
        sidebar_layout.addWidget(self.sidebar_selector)

        # Global Frame Selector
        self.active_frame_label = QLabel("Active Frame:")
        self.global_frame_selector = QComboBox()
        self.global_frame_selector.addItems(list(self.frames.keys()))
        sidebar_layout.addWidget(self.active_frame_label)
        sidebar_layout.addWidget(self.global_frame_selector)
        self.global_frame_selector.currentTextChanged.connect(self.on_global_frame_selected)

        # Stacked widget to hold section content
        self.sidebar_stack = QStackedWidget()
        sidebar_layout.addWidget(self.sidebar_stack)

        # Connect dropdown to stack
        self.sidebar_selector.currentIndexChanged.connect(self.sidebar_stack.setCurrentIndex)
        self.sidebar_selector.currentTextChanged.connect(self.on_sidebar_changed)

        # --- SECTION 0: GRID MANAGER ---
        grid_tab = QWidget()
        grid_layout = QVBoxLayout(grid_tab)
        
        grid_settings = QGroupBox("Grid Spacings")
        grid_settings_form = QFormLayout()
        self.grid_x_input = QLineEdit("5")
        self.grid_y_input = QLineEdit("5")
        
        self.grid_z_table = QTableWidget(3, 2)
        self.grid_z_table.setHorizontalHeaderLabels(["Level", "Elevation (m)"])
        self.grid_z_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid_z_table.setMinimumHeight(150)
        self.grid_z_table.setItem(0, 0, QTableWidgetItem("Foundation"))
        self.grid_z_table.setItem(0, 1, QTableWidgetItem("-2.0"))
        self.grid_z_table.setItem(1, 0, QTableWidgetItem("Ground Floor"))
        self.grid_z_table.setItem(1, 1, QTableWidgetItem("0.0"))
        self.grid_z_table.setItem(2, 0, QTableWidgetItem("Floor 2"))
        self.grid_z_table.setItem(2, 1, QTableWidgetItem("3.5"))
        
        self.grid_z_table.itemChanged.connect(self.update_floor_levels)
        
        z_btns = QHBoxLayout()
        add_z_btn = QPushButton("Add Level")
        add_z_btn.clicked.connect(self.add_z_level)
        del_z_btn = QPushButton("Delete Level")
        del_z_btn.clicked.connect(self.delete_z_level)
        z_btns.addWidget(add_z_btn)
        z_btns.addWidget(del_z_btn)

        grid_settings_form.addRow("X Spacings (1,2,3...):", self.grid_x_input)
        grid_settings_form.addRow("Y Spacings (A,B,C...):", self.grid_y_input)
        grid_settings_form.addRow("Z Elevations:", self.grid_z_table)
        grid_settings_form.addRow("", z_btns)
        grid_settings.setLayout(grid_settings_form)
        grid_layout.addWidget(grid_settings)
        
        grid_assign_group = QGroupBox("Frame Assignments")
        grid_assign_layout = QVBoxLayout()
        self.grid_table = QTableWidget(0, 3)
        self.grid_table.setHorizontalHeaderLabels(["Grid Line", "Frame", "Offset"])
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        grid_assign_layout.addWidget(self.grid_table)
        
        grid_btns = QHBoxLayout()
        add_ga_btn = QPushButton("Add Assignment")
        add_ga_btn.clicked.connect(self.add_grid_assignment)
        del_ga_btn = QPushButton("Delete Selected")
        del_ga_btn.clicked.connect(self.delete_grid_assignment)
        grid_btns.addWidget(add_ga_btn)
        grid_btns.addWidget(del_ga_btn)
        grid_assign_layout.addLayout(grid_btns)
        grid_assign_group.setLayout(grid_assign_layout)
        grid_layout.addWidget(grid_assign_group)
        
        grid_layout.addStretch()
        self.sidebar_stack.addWidget(grid_tab)

        # --- SECTION 1: FRAMES ---
        frames_tab = QWidget()
        frames_layout = QVBoxLayout(frames_tab)
        
        self.frame_list = QListWidget()
        self.frame_list.addItem("Frame 1")
        self.frame_list.setCurrentRow(0)
        self.frame_list.itemSelectionChanged.connect(self.switch_frame)
        frames_layout.addWidget(QLabel("Manage Frames:"))
        frames_layout.addWidget(self.frame_list)
        
        frame_btns_grid = QGridLayout()
        add_f_btn = QPushButton("New")
        add_f_btn.clicked.connect(self.add_frame)
        dup_f_btn = QPushButton("Duplicate")
        dup_f_btn.clicked.connect(self.duplicate_frame)
        ren_f_btn = QPushButton("Rename")
        ren_f_btn.clicked.connect(self.rename_frame)
        del_f_btn = QPushButton("Delete")
        del_f_btn.clicked.connect(self.delete_frame)
        
        frame_btns_grid.addWidget(add_f_btn, 0, 0)
        frame_btns_grid.addWidget(dup_f_btn, 0, 1)
        frame_btns_grid.addWidget(ren_f_btn, 1, 0)
        frame_btns_grid.addWidget(del_f_btn, 1, 1)
        frames_layout.addLayout(frame_btns_grid)
        frames_layout.addStretch()
        self.sidebar_stack.addWidget(frames_tab)

        # --- SECTION: SLABS ---
        slabs_tab = QWidget()
        slabs_layout = QVBoxLayout(slabs_tab)
        
        slabs_group = QGroupBox("Manage Slabs")
        slabs_vbox = QVBoxLayout()
        self.slabs_table = QTableWidget(0, 4)
        self.slabs_table.setHorizontalHeaderLabels(["Name", "Points (e.g. A1,A2,B2,B1)", "Pressure (kN/m2)", "Level (m)"])
        self.slabs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.slabs_table.itemChanged.connect(self.on_slab_data_changed)
        slabs_vbox.addWidget(self.slabs_table)
        
        slab_btns = QHBoxLayout()
        add_slab_btn = QPushButton("Add Slab")
        add_slab_btn.clicked.connect(self.add_slab)
        del_slab_btn = QPushButton("Delete Slab")
        del_slab_btn.clicked.connect(self.delete_slab)
        dist_slab_btn = QPushButton("Distribute Slab Loads")
        dist_slab_btn.clicked.connect(self.distribute_slab_loads)
        slab_btns.addWidget(add_slab_btn)
        slab_btns.addWidget(del_slab_btn)
        slabs_vbox.addLayout(slab_btns)
        slabs_vbox.addWidget(dist_slab_btn)
        slabs_group.setLayout(slabs_vbox)
        slabs_layout.addWidget(slabs_group)
        slabs_layout.addStretch()
        self.sidebar_stack.addWidget(slabs_tab)

        # --- SECTION 2: GEOMETRY & BUILD ---
        geometry_tab = QWidget()
        geometry_layout = QVBoxLayout(geometry_tab)
        
        # Section: Global Defaults (Moved inside Geometry)
        globals_group = QGroupBox("Global Material Properties")
        globals_form = QFormLayout()
        self.ea_input = QLineEdit("5000")
        self.ei_input = QLineEdit("10000")
        globals_form.addRow("EA (Axial Rigidity):", self.ea_input)
        globals_form.addRow("EI (Flexural Rigidity):", self.ei_input)
        globals_group.setLayout(globals_form)
        geometry_layout.addWidget(globals_group)

        # Dropdown for Construction Methods
        self.geom_selector = QComboBox()
        self.geom_selector.addItems(["Manual", "Tower Grid", "Frame Grid", "Combined", "Test Frames"])
        geometry_layout.addWidget(QLabel("Construction Method:"))
        geometry_layout.addWidget(self.geom_selector)

        self.geom_stack = QStackedWidget()
        self.geom_selector.currentIndexChanged.connect(self.geom_stack.setCurrentIndex)
        
        # Tab 1: Manual Entry
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        self.x1, self.y1 = QLineEdit("0"), QLineEdit("0")
        self.x2, self.y2 = QLineEdit("0"), QLineEdit("5")
        
        manual_btns_layout = QHBoxLayout()
        truss_btn = QPushButton("Add Truss")
        truss_btn.clicked.connect(lambda: self.add_manual_element(element_type='truss'))
        frame_btn = QPushButton("Add Frame")
        frame_btn.clicked.connect(lambda: self.add_manual_element(element_type='frame'))
        manual_btns_layout.addWidget(truss_btn)
        manual_btns_layout.addWidget(frame_btn)

        manual_layout.addWidget(QLabel("Start (X, Y)"))
        manual_layout.addWidget(self.x1); manual_layout.addWidget(self.y1)
        manual_layout.addWidget(QLabel("End (X, Y)"))
        manual_layout.addWidget(self.x2); manual_layout.addWidget(self.y2)
        manual_layout.addLayout(manual_btns_layout)
        self.geom_stack.addWidget(manual_tab)

        # Tab 2: Truss Tower Builder (Ref: Example 4)
        tower_tab = QWidget()
        tower_form = QFormLayout(tower_tab)
        self.tower_width = QLineEdit("6")
        self.tower_span = QLineEdit("30")
        self.tower_q_horiz = QLineEdit("1")
        self.tower_k_stiffness = QLineEdit("5000")
        tower_btn = QPushButton("Generate Towers")
        tower_btn.clicked.connect(self.build_truss_towers)
        tower_form.addRow("Width:", self.tower_width)
        tower_form.addRow("Span:", self.tower_span)
        tower_form.addRow("Horizontal UDL (kN/m):", self.tower_q_horiz)
        tower_form.addRow("Support Stiffness k:", self.tower_k_stiffness)
        tower_form.addWidget(tower_btn)
        self.geom_stack.addWidget(tower_tab)

        # Tab 3: Frame Grid
        frame_tab = QWidget()
        frame_form = QFormLayout(frame_tab)
        self.frame_bay_w = QLineEdit("5")
        self.frame_bay_h = QLineEdit("5")
        self.frame_n_bays = QLineEdit("1")
        self.frame_n_floors = QLineEdit("1")
        self.frame_sup_type = QComboBox()
        self.frame_sup_type.addItems(["Hinged", "Fixed"])
        
        self.frame_q_loads = QLineEdit("-10")

        frame_btn = QPushButton("Generate Frame Grid")
        frame_btn.clicked.connect(self.build_frame_grid)
        
        frame_form.addRow("Bay Width:", self.frame_bay_w)
        frame_form.addRow("Bay Height:", self.frame_bay_h)
        frame_form.addRow("Number of Bays:", self.frame_n_bays)
        frame_form.addRow("Number of Floors:", self.frame_n_floors)
        frame_form.addRow("Foundation Support:", self.frame_sup_type)
        frame_form.addRow("Gravity UDLs (kN/m):", self.frame_q_loads)
        frame_form.addWidget(frame_btn)
        self.geom_stack.addWidget(frame_tab)

        # Tab 4: Combined Structure
        combined_tab = QWidget()
        combined_form = QFormLayout(combined_tab)
        self.comb_width = QLineEdit("6")
        self.comb_h_story = QLineEdit("3.5")
        self.comb_h_roof = QLineEdit("2")
        self.comb_q_floor = QLineEdit("-5")
        self.comb_q_roof = QLineEdit("-2")
        
        comb_btn = QPushButton("Generate Combined")
        comb_btn.clicked.connect(self.build_combined_structure)
        
        combined_form.addRow("Width:", self.comb_width)
        combined_form.addRow("Story Height:", self.comb_h_story)
        combined_form.addRow("Roof Height:", self.comb_h_roof)
        combined_form.addRow("Floor UDL (kN/m):", self.comb_q_floor)
        combined_form.addRow("Roof UDL (kN/m):", self.comb_q_roof)
        combined_form.addWidget(comb_btn)
        self.geom_stack.addWidget(combined_tab)

        # Tab 5: Test Frames
        test_frames_tab = QWidget()
        test_frames_layout = QVBoxLayout(test_frames_tab)
        btn_3bay = QPushButton("Generate 3-Bay Test Frame")
        btn_3bay.clicked.connect(lambda: self.build_test_frame(n_bays=3))
        btn_2bay = QPushButton("Generate 2-Bay Test Frame")
        btn_2bay.clicked.connect(lambda: self.build_test_frame(n_bays=2))
        
        test_frames_layout.addWidget(QLabel("Presets for Default Grid:"))
        test_frames_layout.addWidget(btn_3bay)
        test_frames_layout.addWidget(btn_2bay)
        test_frames_layout.addStretch()
        self.geom_stack.addWidget(test_frames_tab)

        geometry_layout.addWidget(self.geom_stack)
        geometry_layout.addStretch()
        self.sidebar_stack.addWidget(geometry_tab)

        # --- SECTION 3: LOADS & SUPPORTS ---
        assign_tab = QWidget()
        assign_layout = QVBoxLayout(assign_tab)

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
        assign_layout.addWidget(supports_group)

        # Section: Loads
        loads_group = QGroupBox("Loads")
        loads_form = QFormLayout()
        
        self.load_type = QComboBox()
        self.load_type.addItems(["Point Load", "Moment", "q-Load", "Triangular (Peak Mid)", "Trapezoidal (Uniform Mid)"])
        self.load_type.currentTextChanged.connect(self.update_load_ui)
        
        self.load_id_input = QLineEdit("1")
        self.load_val1 = QLineEdit("10")
        self.load_val1_end = QLineEdit("10")
        self.load_val2 = QLineEdit("0")
        self.load_val2_end = QLineEdit("0")
        self.load_pos1 = QLineEdit("0.5")
        self.load_pos2 = QLineEdit("0.75")
        self.load_dir = QComboBox()
        self.load_dir.addItems(["y", "x", "element", "parallel"])
        
        add_load_btn = QPushButton("Apply Load")
        add_load_btn.clicked.connect(self.apply_load)
        
        self.lbl_load_id = QLabel("Node ID:")
        self.lbl_val1 = QLabel("Fx (kN):")
        self.lbl_val1_end = QLabel("q End (kN/m):")
        self.lbl_val2 = QLabel("Fz (kN):")
        self.lbl_val2_end = QLabel("qp End (kN/m):")
        self.lbl_pos1 = QLabel("Pos 1 (ratio):")
        self.lbl_pos2 = QLabel("Pos 2 (ratio):")
        self.lbl_dir = QLabel("Direction:")
        
        loads_form.addRow("Load Type:", self.load_type)
        loads_form.addRow(self.lbl_load_id, self.load_id_input)
        loads_form.addRow(self.lbl_val1, self.load_val1)
        loads_form.addRow(self.lbl_val1_end, self.load_val1_end)
        loads_form.addRow(self.lbl_val2, self.load_val2)
        loads_form.addRow(self.lbl_val2_end, self.load_val2_end)
        loads_form.addRow(self.lbl_pos1, self.load_pos1)
        loads_form.addRow(self.lbl_pos2, self.load_pos2)
        loads_form.addRow(self.lbl_dir, self.load_dir)
        loads_form.addRow(add_load_btn)
        
        # Initial state
        self.lbl_val1_end.hide()
        self.load_val1_end.hide()
        self.lbl_val2_end.hide()
        self.load_val2_end.hide()
        self.lbl_pos1.hide()
        self.load_pos1.hide()
        self.lbl_pos2.hide()
        self.load_pos2.hide()
        self.lbl_dir.hide()
        self.load_dir.hide()
        
        loads_group.setLayout(loads_form)
        assign_layout.addWidget(loads_group)
        assign_layout.addStretch()
        self.sidebar_stack.addWidget(assign_tab)

        # --- SECTION 4: ANALYSIS & TOOLS ---
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)

        # Solver Controls
        solve_btn = QPushButton("SOLVE SYSTEM")
        solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        solve_btn.clicked.connect(self.solve_system)
        analysis_layout.addWidget(solve_btn)

        export_btn = QPushButton("Export Project (JSON)")
        export_btn.clicked.connect(self.export_project)
        analysis_layout.addWidget(export_btn)

        import_btn = QPushButton("Import Project (JSON)")
        import_btn.clicked.connect(self.import_project)
        analysis_layout.addWidget(import_btn)

        test_ui_btn = QPushButton("Run UI Smoke Test")
        test_ui_btn.clicked.connect(self.run_ui_test)
        analysis_layout.addWidget(test_ui_btn)

        # Element Manager
        mgr_btn = QPushButton("Element Manager")
        mgr_btn.clicked.connect(self.open_element_manager)
        analysis_layout.addWidget(mgr_btn)

        reset_btn = QPushButton("Reset Structure")
        reset_btn.clicked.connect(self.reset_system)
        analysis_layout.addWidget(reset_btn)
        
        analysis_layout.addStretch()
        self.sidebar_stack.addWidget(analysis_tab)

        # --- SECTION 5: ELEMENT MANAGER ---
        self.element_mgr_widget = ElementManagerWidget(self)
        self.sidebar_stack.addWidget(self.element_mgr_widget)

        # --- SECTION 6: TEST ---
        test_tab = QWidget()
        test_layout = QVBoxLayout(test_tab)
        
        self.test_foundation_type = QComboBox()
        self.test_foundation_type.addItems(["Fixed", "Hinged", "Spring"])
        test_layout.addWidget(QLabel("Test Foundation Type:"))
        test_layout.addWidget(self.test_foundation_type)
        
        gen_building_btn = QPushButton("Generate 3-Story Building (3x4 Grid)")
        gen_building_btn.clicked.connect(self.generate_test_building)
        test_layout.addWidget(gen_building_btn)
        test_layout.addStretch()
        self.sidebar_stack.addWidget(test_tab)

        sidebar_scroll.setWidget(sidebar_widget)
        layout.addWidget(sidebar_scroll)

        # --- CENTRAL AREA (Visualization & Results) ---
        central_container = QWidget()
        central_layout = QVBoxLayout(central_container)
        self.central_stack = QStackedWidget()
        
        self.figure, self.ax = plt.subplots()
        self.ax.set_aspect('equal', adjustable='box')
        self.figure.subplots_adjust(left=0.07, right=0.97, top=0.95, bottom=0.07)
        self.canvas = self.figure.canvas
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 1. Visualization View (Canvas only)
        self.central_stack.addWidget(self.canvas)
        
        # Visualization Toolbar
        viz_toolbar = QHBoxLayout()
        
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Structure", "Displacement", "Axial Force", "Shear Force", "Bending Moment", "Grid Plan", "3D Wireframe", "Member Analysis", "Results Table"])
        self.view_mode.currentTextChanged.connect(self.on_view_mode_changed)
        
        self.member_selector = QComboBox()
        self.member_selector.setVisible(False)
        
        self.floor_selector = QComboBox()
        self.floor_selector.setEnabled(False)
        
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100)
        self.scale_slider.setValue(10)
        self.scale_slider.setFixedWidth(150)

        self.show_grid = QCheckBox("Grid")
        self.show_grid.setChecked(True)
        self.show_ticks = QCheckBox("Ticks")
        self.show_ticks.setChecked(True)
        self.show_grid_labels = QCheckBox("Grid Labels")
        self.show_grid_labels.setChecked(True)
        self.show_beam_marks = QCheckBox("Beam Marks")
        self.lock_3d_rotation = QCheckBox("Lock 3D Rotation")
        self.lock_3d_rotation.setEnabled(False)

        reset_view_btn = QPushButton("Fit View")

        viz_toolbar.addWidget(QLabel("View:"))
        viz_toolbar.addWidget(self.view_mode)
        viz_toolbar.addWidget(QLabel("Member:"))
        viz_toolbar.addWidget(self.member_selector)
        viz_toolbar.addWidget(QLabel("Floor:"))
        viz_toolbar.addWidget(self.floor_selector)
        viz_toolbar.addWidget(QLabel("Scale:"))
        viz_toolbar.addWidget(self.scale_slider)
        viz_toolbar.addWidget(self.show_grid)
        viz_toolbar.addWidget(self.show_ticks)
        viz_toolbar.addWidget(self.show_grid_labels)
        viz_toolbar.addWidget(self.show_beam_marks)
        viz_toolbar.addWidget(self.lock_3d_rotation)
        viz_toolbar.addWidget(reset_view_btn)
        viz_toolbar.addStretch()

        central_layout.addWidget(self.central_stack, stretch=1)
        central_layout.addLayout(viz_toolbar)

        # 2. Results Table View
        self.results_table_container = QScrollArea()
        self.results_table_container.setWidgetResizable(True)
        self.results_table_widget = QWidget()
        self.results_table_layout = QVBoxLayout(self.results_table_widget)
        self.results_table_container.setWidget(self.results_table_widget)
        self.central_stack.addWidget(self.results_table_container)

        layout.addWidget(central_container, stretch=1)
        
        # Initialize Plotter
        self.plotter = StructuralPlotter(self)
        
        # Connect signals
        self.grid_z_table.itemChanged.connect(lambda: self.update_floor_levels())
        self.grid_x_input.textChanged.connect(lambda: (self.validate_grid_assignments(), self.plotter.update_plot()))
        self.grid_y_input.textChanged.connect(lambda: (self.validate_grid_assignments(), self.plotter.update_plot()))
        self.grid_table.itemChanged.connect(lambda: (self.validate_grid_assignments(), self.plotter.update_plot()))
        
        self.floor_selector.currentTextChanged.connect(self.plotter.update_plot)
        self.scale_slider.valueChanged.connect(self.plotter.update_plot)
        self.show_grid.stateChanged.connect(self.plotter.update_plot)
        self.show_ticks.stateChanged.connect(self.plotter.update_plot)
        self.show_grid_labels.stateChanged.connect(self.plotter.update_plot)
        self.show_beam_marks.stateChanged.connect(self.plotter.update_plot)
        self.lock_3d_rotation.stateChanged.connect(self.plotter.update_plot)
        self.member_selector.currentTextChanged.connect(self.plotter.update_plot)
        reset_view_btn.clicked.connect(self.plotter.reset_view)

        # Trigger initial visibility state after all UI components are initialized
        self.on_sidebar_changed(self.sidebar_selector.currentText())
        self.update_floor_levels()

    # --- LOGIC METHODS ---

    def on_global_frame_selected(self, name):
        if not name or name == self.current_frame_name:
            return
        items = self.frame_list.findItems(name, Qt.MatchFlag.MatchExactly)
        if items:
            self.frame_list.setCurrentItem(items[0])
            self.ss = self.frames[name].system

    def on_sidebar_changed(self, text):
        # Hide active frame selector for Frames and Grid sections
        show_active_frame = text not in ["Frames", "Grid", "Slabs", "Test"]
        self.active_frame_label.setVisible(show_active_frame)
        self.global_frame_selector.setVisible(show_active_frame)

        if text == "Slabs":
            self.view_mode.setCurrentText("Grid Plan")
            self.plotter.update_plot()
        elif text == "Grid":
            self.sync_grid_frame_combos()
        elif text == "Element Manager":
            self.element_mgr_widget.refresh_data()

    def sync_grid_frame_combos(self):
        """Updates the frame selection combo boxes in the grid table."""
        frame_names = list(self.frames.keys())
        for row in range(self.grid_table.rowCount()):
            combo = self.grid_table.cellWidget(row, 1)
            if isinstance(combo, QComboBox):
                current = combo.currentText()
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(frame_names)
                if current in frame_names:
                    combo.setCurrentText(current)
                combo.blockSignals(False)

    def add_grid_assignment(self):
        self.grid_table.blockSignals(True)
        row = self.grid_table.rowCount()
        
        # Default values
        new_label = "A"
        prev_frame = ""
        prev_offset = "0"
        
        if row > 0:
            # Get previous row data
            prev_label = self.grid_table.item(row - 1, 0).text()
            prev_frame_combo = self.grid_table.cellWidget(row - 1, 1)
            prev_frame = prev_frame_combo.currentText() if prev_frame_combo else ""
            prev_offset = self.grid_table.item(row - 1, 2).text()
            
            # Increment label
            if prev_label.isdigit():
                new_label = str(int(prev_label) + 1)
            elif len(prev_label) == 1 and prev_label.isalpha():
                if prev_label.upper() == 'Z':
                    new_label = 'AA'
                else:
                    new_label = chr(ord(prev_label.upper()) + 1)
            else:
                new_label = prev_label

        self.grid_table.insertRow(row)
        self.grid_table.setItem(row, 0, QTableWidgetItem(new_label))

        combo = QComboBox()
        combo.addItems(list(self.frames.keys()))
        if prev_frame in self.frames:
            combo.setCurrentText(prev_frame)
        combo.currentTextChanged.connect(self.plotter.update_plot)
        self.grid_table.setCellWidget(row, 1, combo)
        
        self.grid_table.setItem(row, 2, QTableWidgetItem(prev_offset))
        self.grid_table.blockSignals(False)
        self.plotter.update_plot()

    def delete_grid_assignment(self):
        rows = sorted(set(i.row() for i in self.grid_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.grid_table.removeRow(row)
        self.plotter.update_plot()

    def add_slab(self):
        row = self.slabs_table.rowCount()
        self.slabs_table.blockSignals(True)
        self.slabs_table.insertRow(row)
        name = f"Slab {row + 1}"
        self.slabs_table.setItem(row, 0, QTableWidgetItem(name))
        self.slabs_table.setItem(row, 1, QTableWidgetItem("A1, A2, B2, B1"))
        self.slabs_table.setItem(row, 2, QTableWidgetItem("5.0"))
        self.slabs_table.blockSignals(False)
        self.on_slab_data_changed()

    def delete_slab(self):
        rows = sorted(set(i.row() for i in self.slabs_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.slabs_table.removeRow(row)
        self.on_slab_data_changed()

    def on_slab_data_changed(self):
        self.slabs = {}
        for row in range(self.slabs_table.rowCount()):
            try:
                name_item = self.slabs_table.item(row, 0)
                pts_item = self.slabs_table.item(row, 1)
                load_item = self.slabs_table.item(row, 2)
                level_item = self.slabs_table.item(row, 3)
                if not all([name_item, pts_item, load_item, level_item]): continue
                
                name = name_item.text()
                pts_str = pts_item.text()
                load = float(load_item.text())
                level_h = float(level_item.text())
                
                pts = []
                for p_str in pts_str.split(','):
                    parsed = self.parse_grid_point(p_str)
                    if parsed: pts.append(parsed)
                
                if pts:
                    self.slabs[name] = {'points': pts, 'load': load, 'level_height': level_h}
            except (ValueError, AttributeError): continue
        self.plotter.update_plot()

    def parse_grid_point(self, pt_str):
        pt_str = pt_str.strip().upper()
        if not pt_str: return None
        i = 0
        while i < len(pt_str) and pt_str[i].isalpha(): i += 1
        y_label, x_label = pt_str[:i], pt_str[i:]
        if not y_label or not x_label or not x_label.isdigit(): return None
        y_idx = string.ascii_uppercase.find(y_label)
        x_idx = int(x_label) - 1
        return x_idx, y_idx

    def distribute_slab_loads(self):
        """Distributes slab pressure loads to beams using tributary area method."""
        if not self.slabs: return
        
        # 1. Get Grid Coordinates
        try:
            sx = [float(s.strip()) for s in self.grid_x_input.text().split(',') if s.strip()]
            sy = [float(s.strip()) for s in self.grid_y_input.text().split(',') if s.strip()]
        except ValueError: return
        gx = [0.0] + list(np.cumsum(sx))
        gy = [0.0] + list(np.cumsum(sy))

        # 2. Get Selected Height
        try:
            sel_text = self.floor_selector.currentText()
            sel_height = float(sel_text.split('(')[1].split('m')[0])
        except (IndexError, ValueError): sel_height = 0.0

        # 3. Map Grid Lines to Frames
        grid_mapping = {} # {line_label: (frame_name, offset)}
        for row in range(self.grid_table.rowCount()):
            line = self.grid_table.item(row, 0).text().upper()
            frame = self.grid_table.cellWidget(row, 1).currentText()
            try: offset = float(self.grid_table.item(row, 2).text())
            except ValueError: offset = 0.0
            grid_mapping[line] = (frame, offset)

        # 4. Process each slab
        for name, data in self.slabs.items():
            pts = data['points']
            w = data['load']
            slab_h = data.get('level_height')
            
            # Only process slabs on the selected level
            if slab_h is not None and not np.isclose(slab_h, sel_height):
                continue
            
            # Detect if rectangular (simple case)
            x_indices = sorted(list(set(p[0] for p in pts)))
            y_indices = sorted(list(set(p[1] for p in pts)))
            
            if len(x_indices) == 2 and len(y_indices) == 2 and len(pts) >= 4:
                # Rectangular slab
                x1_idx, x2_idx = x_indices[0], x_indices[1]
                y1_idx, y2_idx = y_indices[0], y_indices[1]
                
                Lx = gx[x2_idx] - gx[x1_idx]
                Ly = gy[y2_idx] - gy[y1_idx]
                
                # Edges: (Line, StartCoord, EndCoord, IsVerticalLine)
                x1_lbl, x2_label = str(x1_idx + 1), str(x2_idx + 1)
                y1_lbl = string.ascii_uppercase[y1_idx] if y1_idx < 26 else f"Z{y1_idx}"
                y2_lbl = string.ascii_uppercase[y2_idx] if y2_idx < 26 else f"Z{y2_idx}"
                
                edges = [
                    (y1_lbl, gx[x1_idx], gx[x2_idx], False), # Bottom
                    (y2_lbl, gx[x1_idx], gx[x2_idx], False), # Top
                    (x1_lbl, gy[y1_idx], gy[y2_idx], True),  # Left
                    (x2_label, gy[y1_idx], gy[y2_idx], True)  # Right
                ]
                
                short_dim = min(Lx, Ly)
                peak = w * short_dim / 2.0
                
                for line, start, end, is_vert in edges:
                    if line not in grid_mapping: continue
                    fname, offset = grid_mapping[line]
                    f_ss = self.frames[fname].system
                    
                    f_start = start - (gx[0] if not is_vert else gy[0]) - offset
                    f_end = end - (gx[0] if not is_vert else gy[0]) - offset
                    
                    target_elements = []
                    for eid, el in f_ss.element_map.items():
                        n1, n2 = f_ss.node_map[el.node_id1].vertex, f_ss.node_map[el.node_id2].vertex
                        if np.isclose(n1.y, sel_height) and np.isclose(n2.y, sel_height):
                            c1, c2 = sorted([n1.x, n2.x])
                            if c1 >= f_start - 1e-6 and c2 <= f_end + 1e-6 and not np.isclose(c1, c2):
                                target_elements.append(el)
                    
                    if not target_elements: continue
                    
                    # If it's a single element matching the full edge, use specialized split logic
                    if len(target_elements) == 1:
                        el = target_elements[0]
                        edge_len = f_end - f_start
                        if np.isclose(edge_len, short_dim):
                            self.apply_specialized_load(fname, el.id, "Triangular (Peak Mid)", peak, 0.5)
                        else:
                            pos1 = (short_dim / 2.0) / edge_len
                            pos2 = 1.0 - pos1
                            self.apply_specialized_load(fname, el.id, "Trapezoidal (Uniform Mid)", peak, pos1, pos2)
                    else:
                        # Multiple segments: apply uniform load to each as a simplified fallback
                        model = self.frames[fname]
                        for el in target_elements:
                            # Find index in blueprint by matching coordinates
                            n1, n2 = f_ss.node_map[el.node_id1].vertex, f_ss.node_map[el.node_id2].vertex
                            for i, e in enumerate(model.elements):
                                if (np.allclose(e['loc'][0], [n1.x, n1.y]) and np.allclose(e['loc'][1], [n2.x, n2.y])) or \
                                   (np.allclose(e['loc'][1], [n1.x, n1.y]) and np.allclose(e['loc'][0], [n2.x, n2.y])):
                                    model.q_loads.append({'element_idx': i, 'q': -abs(peak), 'dir': 'y', 'qp': 0})
                                    break
            else:
                # Irregular slab: Fallback or simplified distribution could be added here
                pass

        self.plotter.update_plot()
        QMessageBox.information(self, "Success", "Slab loads distributed to frames.")

    def apply_specialized_load(self, frame_name, eid, ltype, peak, pos1, pos2=0.75):
        """Helper to apply split-element loads to a specific frame."""
        peak = -abs(peak) # Ensure downward load for slab distribution
        model = self.frames[frame_name]
        ss = model.system
        el = ss.element_map.get(eid)
        if not el: return
        n1_v, n2_v = ss.node_map[el.node_id1].vertex, ss.node_map[el.node_id2].vertex

        # Find element in blueprint by matching coordinates
        target_idx = -1
        for i, e in enumerate(model.elements):
            if (np.allclose(e['loc'][0], [n1_v.x, n1_v.y]) and np.allclose(e['loc'][1], [n2_v.x, n2_v.y])) or \
               (np.allclose(e['loc'][1], [n1_v.x, n1_v.y]) and np.allclose(e['loc'][0], [n2_v.x, n2_v.y])):
                target_idx = i
                break
        
        if target_idx == -1: return
        
        el_data = model.elements.pop(target_idx)
        n1_loc, n2_loc = el_data['loc']
        ea, ei = el_data['EA'], el_data['EI']
        
        model.q_loads = [q for q in model.q_loads if q['element_idx'] != target_idx]
        for q in model.q_loads:
            if q['element_idx'] > target_idx: q['element_idx'] -= 1

        if ltype == "Triangular (Peak Mid)":
            mid = [float(n1_loc[0] + (n2_loc[0] - n1_loc[0]) * pos1), float(n1_loc[1] + (n2_loc[1] - n1_loc[1]) * pos1)]
            model.elements.append({'loc': [n1_loc, mid], 'EA': ea, 'EI': ei})
            model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [0, peak], 'dir': 'y', 'qp': 0})
            model.elements.append({'loc': [mid, n2_loc], 'EA': ea, 'EI': ei})
            model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, 0], 'dir': 'y', 'qp': 0})
        else:
            p1 = [float(n1_loc[0] + (n2_loc[0] - n1_loc[0]) * pos1), float(n1_loc[1] + (n2_loc[1] - n1_loc[1]) * pos1)]
            p2 = [float(n1_loc[0] + (n2_loc[0] - n1_loc[0]) * pos2), float(n1_loc[1] + (n2_loc[1] - n1_loc[1]) * pos2)]
            model.elements.append({'loc': [n1_loc, p1], 'EA': ea, 'EI': ei})
            model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [0, peak], 'dir': 'y', 'qp': 0})
            model.elements.append({'loc': [p1, p2], 'EA': ea, 'EI': ei})
            model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, peak], 'dir': 'y', 'qp': 0})
            model.elements.append({'loc': [p2, n2_loc], 'EA': ea, 'EI': ei})
            model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, 0], 'dir': 'y', 'qp': 0})

        old_active = self.current_frame_name
        self.current_frame_name = frame_name
        self.rebuild_system()
        self.current_frame_name = old_active

    def add_frame(self):
        default_name = f"Frame {len(self.frames) + 1}"
        name, ok = QInputDialog.getText(self, "New Frame", "Enter frame name:", text=default_name)
        if ok and name:
            if name in self.frames:
                QMessageBox.warning(self, "Error", "Frame name already exists.")
                return
            self.frames[name] = FrameModel()
            self.frame_list.addItem(name)
            self.global_frame_selector.addItem(name)
            self.frame_list.setCurrentItem(self.frame_list.findItems(name, Qt.MatchFlag.MatchExactly)[0])

    def switch_frame(self):
        selected = self.frame_list.selectedItems()
        if not selected: return
        self.current_frame_name = selected[0].text()
        self.ss = self.frames[self.current_frame_name].system

        # Sync Global Selector
        self.global_frame_selector.blockSignals(True)
        self.global_frame_selector.setCurrentText(self.current_frame_name)
        self.global_frame_selector.blockSignals(False)

        # Rebuild the system to ensure all internal state is fresh
        self.rebuild_system()
        self.update_member_selector()

        # Sync Element Manager if active
        if hasattr(self, 'element_mgr_widget') and self.sidebar_selector.currentText() == "Element Manager":
            self.element_mgr_widget.refresh_data()
            
        self.plotter.reset_view() # Auto-fit when switching

    def rename_frame(self):
        curr_item = self.frame_list.currentItem()
        if not curr_item: return
        old_name = curr_item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Frame", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            if new_name in self.frames:
                QMessageBox.warning(self, "Error", "Frame name already exists.")
                return
            self.frames[new_name] = self.frames.pop(old_name)
            curr_item.setText(new_name)
            self.current_frame_name = new_name
            # Update combo box
            idx = self.global_frame_selector.findText(old_name)
            if idx != -1:
                self.global_frame_selector.setItemText(idx, new_name)

    def delete_frame(self):
        if self.frame_list.count() <= 1:
            QMessageBox.warning(self, "Error", "Cannot delete the last frame.")
            return
        curr_item = self.frame_list.currentItem()
        if not curr_item: return
        name = curr_item.text()
        reply = QMessageBox.question(self, 'Confirm Delete', f"Delete frame '{name}'?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.frames.pop(name)
            self.frame_list.takeItem(self.frame_list.row(curr_item))
            # Update combo box
            idx = self.global_frame_selector.findText(name)
            if idx != -1:
                self.global_frame_selector.removeItem(idx)

    def add_z_level(self):
        row = self.grid_z_table.rowCount()
        self.grid_z_table.blockSignals(True)
        self.grid_z_table.insertRow(row)
        last_elev = 0.0
        if row > 0:
            try: last_elev = float(self.grid_z_table.item(row-1, 1).text())
            except: pass
        self.grid_z_table.setItem(row, 0, QTableWidgetItem(f"Floor {row+1}"))
        self.grid_z_table.setItem(row, 1, QTableWidgetItem(str(last_elev + 3.5)))
        self.grid_z_table.blockSignals(False)
        self.update_floor_levels()

    def delete_z_level(self):
        rows = sorted(set(i.row() for i in self.grid_z_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.grid_z_table.removeRow(row)
        self.update_floor_levels()

    def update_floor_levels(self):
        """Populates the floor level selector based on grid elevations."""
        levels = []
        elevs = []
        for row in range(self.grid_z_table.rowCount()):
            try:
                name = self.grid_z_table.item(row, 0).text()
                elev = float(self.grid_z_table.item(row, 1).text())
                elevs.append((elev, name))
            except (ValueError, AttributeError): continue
        
        # Sort by elevation to ensure dropdown is logical
        elevs.sort()
        for elev, name in elevs:
            levels.append(f"{name} ({elev:.2f}m)")
        
        # Debug output
        print(f"DEBUG: Populating floor levels: {levels}")
        
        self.floor_selector.blockSignals(True)
        current_sel = self.floor_selector.currentText()
        self.floor_selector.clear()
        self.floor_selector.addItems(levels)
        if current_sel in levels:
            self.floor_selector.setCurrentText(current_sel)
        self.floor_selector.blockSignals(False)
        self.plotter.update_plot()

    def duplicate_frame(self):
        curr_item = self.frame_list.currentItem()
        if not curr_item: return
        old_name = curr_item.text()
        new_name = f"{old_name} (Copy)"
        
        # Ensure old blueprint is in sync
        old_model = self.frames[old_name]
        self.sync_blueprint_from_system(old_model.system, old_model)
        
        # Deep copy blueprint data
        import copy
        new_model = FrameModel()
        new_model.elements = copy.deepcopy(old_model.elements)
        new_model.supports = copy.deepcopy(old_model.supports)
        new_model.point_loads = copy.deepcopy(old_model.point_loads)
        new_model.moment_loads = copy.deepcopy(old_model.moment_loads)
        new_model.q_loads = copy.deepcopy(old_model.q_loads)
        
        self.frames[new_name] = new_model
        self.frame_list.addItem(new_name)
        self.global_frame_selector.addItem(new_name)
        self.frame_list.setCurrentItem(self.frame_list.findItems(new_name, Qt.MatchFlag.MatchExactly)[0])

    def sync_blueprint_from_system(self, ss, model):
        """Scrapes the current SystemElements state into the FrameModel blueprint."""
        model.elements.clear()
        model.supports.clear()
        model.point_loads.clear()
        model.moment_loads.clear()
        model.q_loads.clear()
        
        for el in ss.element_map.values():
            n1, n2 = ss.node_map[el.node_id1].vertex, ss.node_map[el.node_id2].vertex
            model.elements.append({'loc': [[n1.x, n1.y], [n2.x, n2.y]], 'EA': el.EA, 'EI': el.EI})
            if el.id in ss.loads_q:
                # Use attributes from the Element object to preserve user intent (direction and sign)
                q_val = getattr(el, 'q_load', 0)
                d_val = getattr(el, 'q_direction', 'element')
                qp_val = getattr(el, 'q_perp_load', 0)
                
                # Ensure values are JSON serializable and consistent (convert numpy/tuples to lists)
                if isinstance(q_val, (np.ndarray, tuple)): q_val = list(q_val)
                if isinstance(qp_val, (np.ndarray, tuple)): qp_val = list(qp_val)
                
                model.q_loads.append({'element_idx': len(model.elements)-1, 'q': q_val, 'dir': d_val, 'qp': qp_val})

        for n in ss.supports_fixed: model.supports.append({'loc': [n.vertex.x, n.vertex.y], 'type': 'fixed', 'args': {}})
        for n in ss.supports_hinged: model.supports.append({'loc': [n.vertex.x, n.vertex.y], 'type': 'hinged', 'args': {}})
        if hasattr(ss, 'supports_roll'):
            for i, n in enumerate(ss.supports_roll):
                model.supports.append({'loc': [n.vertex.x, n.vertex.y], 'type': 'roll', 'args': {'direction': ss.supports_roll_direction[i]}})
        if hasattr(ss, 'supports_spring_args'):
            for nid, trans, k, roll in ss.supports_spring_args:
                v = ss.node_map[nid].vertex
                model.supports.append({'loc': [v.x, v.y], 'type': 'spring', 'args': {'translation': trans, 'k': k, 'roll': roll}})

        for nid, data in ss.loads_point.items():
            v = ss.node_map[nid].vertex
            fx, fz = (data[0], data[1]) if isinstance(data, (list, tuple)) else (data.get('Fx', 0), data.get('Fz', 0))
            model.point_loads.append({'loc': [v.x, v.y], 'Fx': fx, 'Fz': fz})
        for nid, data in ss.loads_moment.items():
            v = ss.node_map[nid].vertex
            ty = data[0] if isinstance(data, (list, tuple)) else (data.get('Ty', 0) if isinstance(data, dict) else data)
            model.moment_loads.append({'loc': [v.x, v.y], 'Ty': ty})

    def get_material(self):
        return float(self.ea_input.text()), float(self.ei_input.text())

    def reset_system(self):
        self.frames[self.current_frame_name].clear()
        self.ss = self.frames[self.current_frame_name].system
        self.rebuild_system()

    def add_manual_element(self, element_type='frame'):
        try:
            ea, ei = self.get_material()
            p1 = [float(self.x1.text()), float(self.y1.text())]
            p2 = [float(self.x2.text()), float(self.y2.text())]
            
            model = self.frames[self.current_frame_name]
            model.elements.append({'loc': [p1, p2], 'EA': ea, 'EI': ei if element_type == 'frame' else 0})
            self.rebuild_system()
            
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
            model = self.frames[self.current_frame_name]
            model.clear()
            width = float(self.tower_width.text())
            span = float(self.tower_span.text())
            q_horiz = float(self.tower_q_horiz.text())
            k = float(self.tower_k_stiffness.text())
            ea, ei = self.get_material()
            
            y = np.arange(1, 10) * np.pi 
            x = np.cos(y) * width * 0.5
            x -= x.min()

            for length in [0, span]:
                # Use a temporary system to leverage add_element_grid helper
                temp_ss = SystemElements()
                temp_ss.add_element_grid(x + length, y, element_type='truss', EA=ea)
                
                x_left_column = np.ones(y[::2].shape) * x.min() + length
                x_right_column = np.ones(y[::2].shape[0] + 1) * x.max() + length
                temp_ss.add_element_grid(x_left_column, y[::2], element_type='truss', EA=ea)
                temp_ss.add_element_grid(x_right_column, np.r_[y[0], y[1::2], y[-1]], element_type='truss', EA=ea)
                
                for el in temp_ss.element_map.values():
                    n1, n2 = temp_ss.node_map[el.node_id1].vertex, temp_ss.node_map[el.node_id2].vertex
                    model.elements.append({'loc': [[n1.x, n1.y], [n2.x, n2.y]], 'EA': el.EA, 'EI': el.EI})

                model.supports.append({'loc': [x_left_column[0], y[0]], 'type': 'spring', 'args': {'translation': 2, 'k': k}})
                model.supports.append({'loc': [x_right_column[0], y[0]], 'type': 'spring', 'args': {'translation': 2, 'k': k}})
            
            # Top beam
            model.elements.append({'loc': [[0, y.max()], [width, y.max()]], 'EA': ea, 'EI': ei})
            model.elements.append({'loc': [[width, y.max()], [span, y.max()]], 'EA': ea, 'EI': ei})
            model.elements.append({'loc': [[span, y.max()], [span + width, y.max()]], 'EA': ea, 'EI': ei})

            # Stability elements
            model.elements.append({'loc': [[0, y.min()], [width, y.min()]], 'EA': ea, 'EI': 0})
            model.elements.append({'loc': [[span, y.min()], [span + width, y.min()]], 'EA': ea, 'EI': 0})

            if q_horiz != 0:
                for i, e in enumerate(model.elements):
                    dx = e['loc'][1][0] - e['loc'][0][0]
                    dy = e['loc'][1][1] - e['loc'][0][1]
                    if np.isclose(dx, 0) and not np.isclose(dy, 0):
                        model.q_loads.append({'element_idx': i, 'q': q_horiz, 'dir': 'x', 'qp': 0})
            
            self.rebuild_system()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_frame_grid(self):
        """Generates a multi-bay, multi-floor frame grid."""
        try:
            model = self.frames[self.current_frame_name]
            model.clear()
            ea, ei = self.get_material()
            
            w = float(self.frame_bay_w.text())
            n_bays = int(self.frame_n_bays.text())
            n_floors = int(self.frame_n_floors.text())
            sup_type = self.frame_sup_type.currentText().lower()
            
            # Parse elevations from Grid Manager Table
            elevs = []
            for row in range(self.grid_z_table.rowCount()):
                try:
                    elevs.append(float(self.grid_z_table.item(row, 1).text()))
                except (ValueError, AttributeError): continue
            elevs.sort()
            
            if not elevs:
                elevs = [-2.0, 0.0, 3.5]
            
            target_segments = n_floors + 1
            while len(elevs) < target_segments + 1:
                step = elevs[-1] - elevs[-2] if len(elevs) >= 2 else 3.5
                elevs.append(elevs[-1] + step)
            
            y_coords = elevs[:target_segments + 1]

            try:
                q_vals = [float(x.strip()) for x in self.frame_q_loads.text().split(',')]
            except ValueError:
                q_vals = [-10.0]

            # Loop through segments
            for i in range(len(y_coords) - 1):
                y_bot = y_coords[i]
                y_top = y_coords[i+1]
                
                # Columns
                for bay in range(n_bays + 1):
                    x = bay * w
                    model.elements.append({'loc': [[x, y_bot], [x, y_top]], 'EA': ea, 'EI': ei})
                    
                    # Foundation supports at the very bottom (Footing level)
                    if i == 0:
                        args = {'k': float(self.k_input.text())} if sup_type == 'spring' else {}
                        model.supports.append({'loc': [x, y_bot], 'type': sup_type, 'args': args})
                
                # Beams at y_top (Ground Floor or Floor levels)
                q = q_vals[i] if i < len(q_vals) else q_vals[-1]
                for bay in range(n_bays):
                    x_left = bay * w
                    x_right = (bay + 1) * w
                    model.elements.append({'loc': [[x_left, y_top], [x_right, y_top]], 'EA': ea, 'EI': ei})
                    if q != 0:
                        # Ensure gravity loads are negative (downward)
                        model.q_loads.append({'element_idx': len(model.elements)-1, 'q': -abs(q), 'dir': 'y', 'qp': 0})
            
            self.rebuild_system()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_combined_structure(self):
        """Generates a 2-story frame with a truss roof."""
        try:
            model = self.frames[self.current_frame_name]
            model.clear()
            ea, ei = self.get_material()
            
            w = float(self.comb_width.text())
            h = float(self.comb_h_story.text())
            hr = float(self.comb_h_roof.text())
            q_floor = -abs(float(self.comb_q_floor.text()))
            q_roof = -abs(float(self.comb_q_roof.text()))

            # 1. Frame Structure (2 stories)
            # Columns
            model.elements.append({'loc': [[0, 0], [0, h]], 'EA': ea, 'EI': ei})
            model.elements.append({'loc': [[w, 0], [w, h]], 'EA': ea, 'EI': ei})
            model.elements.append({'loc': [[0, h], [0, 2*h]], 'EA': ea, 'EI': ei})
            model.elements.append({'loc': [[w, h], [w, 2*h]], 'EA': ea, 'EI': ei})
            
            # Beams
            model.elements.append({'loc': [[0, h], [w, h]], 'EA': ea, 'EI': ei})
            if q_floor != 0:
                model.q_loads.append({'element_idx': len(model.elements)-1, 'q': q_floor, 'dir': 'y', 'qp': 0})
            
            model.elements.append({'loc': [[0, 2*h], [w, 2*h]], 'EA': ea, 'EI': ei})
            if q_floor != 0:
                model.q_loads.append({'element_idx': len(model.elements)-1, 'q': q_floor, 'dir': 'y', 'qp': 0})

            # Supports
            model.supports.append({'loc': [0, 0], 'type': 'fixed', 'args': {}})
            model.supports.append({'loc': [w, 0], 'type': 'fixed', 'args': {}})
            
            # 2. Truss Roof
            # Rafters
            model.elements.append({'loc': [[0, 2*h], [w/2, 2*h + hr]], 'EA': ea, 'EI': 0})
            if q_roof != 0:
                model.q_loads.append({'element_idx': len(model.elements)-1, 'q': q_roof, 'dir': 'y', 'qp': 0})
                
            model.elements.append({'loc': [[w, 2*h], [w/2, 2*h + hr]], 'EA': ea, 'EI': 0})
            if q_roof != 0:
                model.q_loads.append({'element_idx': len(model.elements)-1, 'q': q_roof, 'dir': 'y', 'qp': 0})
            
            self.rebuild_system()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_test_frame(self, n_bays):
        """Generates a test frame matching current grid settings."""
        try:
            model = self.frames[self.current_frame_name]
            model.clear()
            ea, ei = self.get_material()
            
            # Parse spacings from Grid Manager
            try:
                sx_all = [float(s.strip()) for s in self.grid_x_input.text().split(',') if s.strip()]
            except ValueError:
                sx_all = [5.0]

            # Get elevations from table
            elevs = []
            for row in range(self.grid_z_table.rowCount()):
                try:
                    elevs.append(float(self.grid_z_table.item(row, 1).text()))
                except (ValueError, AttributeError): continue
            elevs.sort()
            
            if not elevs:
                elevs = [-2.0, 0.0, 3.5]

            # Use the requested number of bays, but take widths from the grid
            sx = []
            for i in range(n_bays):
                if i < len(sx_all):
                    sx.append(sx_all[i])
                else:
                    sx.append(sx_all[-1] if sx_all else 5.0)

            x_coords = [0.0] + list(np.cumsum(sx))
            y_coords = elevs

            # Loop through segments
            for i in range(len(y_coords) - 1):
                y_bot = y_coords[i]
                y_top = y_coords[i+1]
                
                # Columns
                for x in x_coords:
                    model.elements.append({'loc': [[x, y_bot], [x, y_top]], 'EA': ea, 'EI': ei})
                    
                    # Foundation supports at the very bottom
                    if i == 0:
                        model.supports.append({'loc': [x, y_bot], 'type': 'fixed', 'args': {}})
                
                # Beams at y_top
                for j in range(len(x_coords) - 1):
                    x_left = x_coords[j]
                    x_right = x_coords[j+1]
                    model.elements.append({'loc': [[x_left, y_top], [x_right, y_top]], 'EA': ea, 'EI': ei})

            self.rebuild_system()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def rebuild_system(self, node_coords=None, element_props=None, supports_info=None, loads_info=None):
        """Rebuilds the SystemElements object from the FrameModel blueprint."""
        model = self.frames[self.current_frame_name]
        if node_coords or element_props or supports_info or loads_info:
            self._update_blueprint_from_overrides(model, node_coords, element_props, supports_info, loads_info)

        self.ss = SystemElements()
        model.system = self.ss
        def clean_val(v):
            if isinstance(v, (list, tuple, np.ndarray)): return [x if abs(x) > 1e-12 else 0 for x in v]
            return v if not isinstance(v, (int, float)) or abs(v) > 1e-12 else 0

        for e in model.elements: self.ss.add_element(location=e['loc'], EA=e['EA'], EI=e['EI'])
        for s in model.supports:
            nid = self.ss.find_node_id(vertex=s['loc'])
            if nid:
                if s['type'] == 'fixed': self.ss.add_support_fixed(nid)
                elif s['type'] == 'hinged': self.ss.add_support_hinged(nid)
                elif s['type'] == 'roll': self.ss.add_support_roll(nid, direction=s['args'].get('direction', 2))
                elif s['type'] == 'spring': self.ss.add_support_spring(nid, translation=s['args'].get('translation', 2), k=s['args'].get('k', 5000), roll=s['args'].get('roll', False))
        
        for p in model.point_loads:
            nid = self.ss.find_node_id(vertex=p['loc'])
            if nid: self.ss.point_load(nid, Fx=clean_val(p['Fx']), Fz=clean_val(p['Fz']))
        for m in model.moment_loads:
            nid = self.ss.find_node_id(vertex=m['loc'])
            if nid: self.ss.moment_load(nid, Ty=clean_val(m['Ty']))
        for q in model.q_loads:
            eid = q['element_idx'] + 1
            if eid in self.ss.element_map:
                self.ss.q_load(q=clean_val(q['q']), element_id=eid, direction=q['dir'], q_perp=clean_val(q.get('qp')))

        self.update_member_selector()

        if self.view_mode.currentText() == "Structure":
            self.plotter.update_plot()
        else:
            self.view_mode.setCurrentText("Structure")

    def _update_blueprint_from_overrides(self, model, node_coords, element_props, supports_info, loads_info):
        """Updates the FrameModel blueprint using data from Element Manager tables."""
        node_map = {nid: node.vertex for nid, node in model.system.node_map.items()}
        if element_props:
            for eid, props in element_props.items():
                if 0 <= eid - 1 < len(model.elements):
                    model.elements[eid-1]['EA'], model.elements[eid-1]['EI'] = props['EA'], props['EI']
        if node_coords:
            for nid, coords in node_coords.items():
                old_v = node_map.get(nid)
                if not old_v: continue
                for e in model.elements:
                    if np.allclose(e['loc'][0], [old_v.x, old_v.y]): e['loc'][0] = coords
                    if np.allclose(e['loc'][1], [old_v.x, old_v.y]): e['loc'][1] = coords
                for s in model.supports:
                    if np.allclose(s['loc'], [old_v.x, old_v.y]): s['loc'] = coords
                for p in model.point_loads:
                    if np.allclose(p['loc'], [old_v.x, old_v.y]): p['loc'] = coords
                for m in model.moment_loads:
                    if np.allclose(m['loc'], [old_v.x, old_v.y]): m['loc'] = coords
        if supports_info:
            model.supports = []
            for nid, stype in supports_info.items():
                v = node_map.get(nid)
                if v: model.supports.append({'loc': [v.x, v.y], 'type': stype.lower(), 'args': {}})
        if loads_info:
            model.point_loads, model.moment_loads, model.q_loads = [], [], []
            for l in loads_info:
                v = node_map.get(l['id'])
                if l['type'] == 'Point' and v: model.point_loads.append({'loc': [v.x, v.y], 'Fx': l['v1'], 'Fz': l['v2']})
                elif l['type'] == 'Moment' and v: model.moment_loads.append({'loc': [v.x, v.y], 'Ty': l['v1']})
                elif l['type'] == 'q-Load': model.q_loads.append({'element_idx': l['id'] - 1, 'q': l['v1'], 'dir': l['v2'], 'qp': l.get('v3', 0)})

    def apply_support(self):
        try:
            nid = int(self.support_node_id.text())
            stype = self.support_type.currentText()
            model = self.frames[self.current_frame_name]
            node = model.system.node_map.get(nid)
            if not node: raise ValueError("Node ID not found.")
            
            # Remove existing support at this location in blueprint
            model.supports = [s for s in model.supports if not np.allclose(s['loc'], [node.vertex.x, node.vertex.y])]
            
            # Add new support to blueprint
            args = {}
            if stype == "Roll": args['direction'] = 2
            elif stype == "Spring": args = {'translation': 2, 'k': float(self.k_input.text()), 'roll': False}
            
            model.supports.append({
                'loc': [node.vertex.x, node.vertex.y],
                'type': stype.lower(),
                'args': args
            })
            
            self.rebuild_system()
            self.element_mgr_widget.refresh_data()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def update_support_ui(self, text):
        self.k_input.setEnabled(text == "Spring")

    def update_load_ui(self, text):
        # Hide all by default
        self.lbl_val1_end.hide()
        self.load_val1_end.hide()
        self.lbl_val2_end.hide()
        self.load_val2_end.hide()
        self.lbl_pos1.hide()
        self.load_pos1.hide()
        self.lbl_pos2.hide()
        self.load_pos2.hide()

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
            self.lbl_val1.setText("q Start (kN/m):")
            self.lbl_val1_end.setText("q End (kN/m):")
            self.lbl_val2.setText("qp Start (kN/m):")
            self.lbl_val2_end.setText("qp End (kN/m):")

            self.lbl_val1_end.show()
            self.load_val1_end.show()
            self.lbl_val2.show()
            self.load_val2.show()
            self.lbl_val2_end.show()
            self.load_val2_end.show()

            self.lbl_dir.show()
            self.load_dir.show()
        elif text == "Triangular (Peak Mid)":
            self.lbl_load_id.setText("Element ID:")
            self.lbl_val1.setText("Peak q (kN/m):")
            self.lbl_val1_end.hide()
            self.load_val1_end.hide()
            self.lbl_val2.hide()
            self.load_val2.hide()
            self.lbl_val2_end.hide()
            self.load_val2_end.hide()
            
            self.lbl_pos1.setText("Peak Pos (0-1):")
            self.lbl_pos1.show()
            self.load_pos1.show()
            self.load_pos1.setText("0.5")

            self.lbl_dir.show()
            self.load_dir.show()
        elif text == "Trapezoidal (Uniform Mid)":
            self.lbl_load_id.setText("Element ID:")
            self.lbl_val1.setText("Peak q (kN/m):")
            self.lbl_val1_end.hide()
            self.load_val1_end.hide()
            self.lbl_val2.hide()
            self.load_val2.hide()
            self.lbl_val2_end.hide()
            self.load_val2_end.hide()
            
            self.lbl_pos1.setText("Start Pos (0-1):")
            self.lbl_pos1.show()
            self.load_pos1.show()
            self.load_pos1.setText("0.25")
            self.lbl_pos2.setText("End Pos (0-1):")
            self.lbl_pos2.show()
            self.load_pos2.show()
            self.load_pos2.setText("0.75")

            self.lbl_dir.show()
            self.load_dir.show()

    def apply_load(self):
        try:
            ltype = self.load_type.currentText()
            oid = int(self.load_id_input.text())
            model = self.frames[self.current_frame_name]
            ss = model.system
            
            if ltype == "Point Load":
                val1 = float(self.load_val1.text())
                val2 = float(self.load_val2.text())
                node = ss.node_map.get(oid)
                if not node: raise ValueError("Node ID not found.")
                model.point_loads.append({'loc': [node.vertex.x, node.vertex.y], 'Fx': val1, 'Fz': val2})
                
            elif ltype == "Moment":
                val1 = float(self.load_val1.text())
                node = ss.node_map.get(oid)
                if not node: raise ValueError("Node ID not found.")
                model.moment_loads.append({'loc': [node.vertex.x, node.vertex.y], 'Ty': val1})
                
            elif ltype == "q-Load":
                q_start = float(self.load_val1.text())
                q_end = float(self.load_val1_end.text())
                qp_start = float(self.load_val2.text() or 0)
                qp_end = float(self.load_val2_end.text() or 0)

                q_val = q_start if q_start == q_end else [q_start, q_end]
                qp_val = qp_start if qp_start == qp_end else [qp_start, qp_end]

                direction = self.load_dir.currentText()
                if oid not in ss.element_map: raise ValueError("Element ID not found.")
                model.q_loads.append({'element_idx': oid - 1, 'q': q_val, 'dir': direction, 'qp': qp_val})
                
            elif ltype in ["Triangular (Peak Mid)", "Trapezoidal (Uniform Mid)"]:
                peak = float(self.load_val1.text())
                direction = self.load_dir.currentText()
                if direction == 'y': peak = -abs(peak) # Downward
                
                el = ss.element_map.get(oid)
                if not el:
                    raise ValueError(f"Element {oid} not found.")
                
                # Note: specialized loads already modify blueprint and rebuild
                n1 = ss.node_map[el.node_id1].vertex
                n2 = ss.node_map[el.node_id2].vertex
                ea, ei = el.EA, el.EI
                
                # Find element in blueprint by matching coordinates
                target_idx = -1
                for i, e in enumerate(model.elements):
                    if (np.allclose(e['loc'][0], [n1.x, n1.y]) and np.allclose(e['loc'][1], [n2.x, n2.y])) or \
                       (np.allclose(e['loc'][1], [n1.x, n1.y]) and np.allclose(e['loc'][0], [n2.x, n2.y])):
                        target_idx = i
                        break
                
                if target_idx != -1:
                    model.elements.pop(target_idx)
                    model.q_loads = [q for q in model.q_loads if q['element_idx'] != target_idx]
                    for q in model.q_loads:
                        if q['element_idx'] > target_idx: q['element_idx'] -= 1
                
                if ltype == "Triangular (Peak Mid)":
                    pos = float(self.load_pos1.text())
                    mid = [float(n1.x + (n2.x - n1.x) * pos), float(n1.y + (n2.y - n1.y) * pos)]
                    if np.allclose([n1.x, n1.y], mid) or np.allclose(mid, [n2.x, n2.y]):
                        raise ValueError("Element too short to split or peak at node.")
                    model.elements.append({'loc': [[n1.x, n1.y], mid], 'EA': ea, 'EI': ei})
                    model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [0, peak], 'dir': direction, 'qp': 0})
                    model.elements.append({'loc': [mid, [n2.x, n2.y]], 'EA': ea, 'EI': ei})
                    model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, 0], 'dir': direction, 'qp': 0})
                else: # Trapezoidal
                    pos1 = float(self.load_pos1.text())
                    pos2 = float(self.load_pos2.text())
                    if pos1 >= pos2:
                        raise ValueError("Start position must be less than end position.")
                    p1 = [float(n1.x + (n2.x - n1.x) * pos1), float(n1.y + (n2.y - n1.y) * pos1)]
                    p2 = [float(n1.x + (n2.x - n1.x) * pos2), float(n1.y + (n2.y - n1.y) * pos2)]
                    if np.allclose([n1.x, n1.y], p1) or np.allclose(p1, p2) or np.allclose(p2, [n2.x, n2.y]):
                        raise ValueError("Element too short to split or positions overlap.")
                    model.elements.append({'loc': [[n1.x, n1.y], p1], 'EA': ea, 'EI': ei})
                    model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [0, peak], 'dir': direction, 'qp': 0})
                    model.elements.append({'loc': [p1, p2], 'EA': ea, 'EI': ei})
                    model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, peak], 'dir': direction, 'qp': 0})
                    model.elements.append({'loc': [p2, [n2.x, n2.y]], 'EA': ea, 'EI': ei})
                    model.q_loads.append({'element_idx': len(model.elements)-1, 'q': [peak, 0], 'dir': direction, 'qp': 0})
                
            self.rebuild_system()
            self.element_mgr_widget.refresh_data()
        except Exception as e:
            msg = str(e) or f"An unknown error of type {type(e).__name__} occurred."
            QMessageBox.warning(self, "Input Error", msg)

    def open_element_manager(self):
        self.sidebar_selector.setCurrentText("Element Manager")

    def update_member_selector(self):
        self.member_selector.blockSignals(True)
        current = self.member_selector.currentText()
        self.member_selector.clear()
        for eid in sorted(self.ss.element_map.keys()):
            self.member_selector.addItem(f"M-{eid}")
        if current and self.member_selector.findText(current) != -1:
            self.member_selector.setCurrentText(current)
        self.member_selector.blockSignals(False)

    def on_view_mode_changed(self, text):
        self.member_selector.setVisible(text == "Member Analysis")
        if text == "Results Table":
            self.central_stack.setCurrentWidget(self.results_table_container)
            self.show_results_table()
        else:
            self.central_stack.setCurrentWidget(self.canvas)
            self.plotter.update_plot()

    def validate_grid_assignments(self):
        """Checks if grid labels in the assignment table exist in X/Y definitions."""
        self.grid_table.blockSignals(True)
        valid = True
        
        try:
            sx = [float(s.strip()) for s in self.grid_x_input.text().split(',') if s.strip()]
            sy = [float(s.strip()) for s in self.grid_y_input.text().split(',') if s.strip()]
        except ValueError:
            sx, sy = [], []

        num_x_lines = len(sx) + 1
        num_y_lines = len(sy) + 1
        alphabet = string.ascii_uppercase

        for row in range(self.grid_table.rowCount()):
            item = self.grid_table.item(row, 0)
            if not item: continue
            
            label = item.text().upper().strip()
            row_is_valid = False
            
            if label.isdigit():
                val = int(label)
                if 1 <= val <= num_x_lines:
                    row_is_valid = True
            else:
                idx = alphabet.find(label)
                if idx != -1 and idx < num_y_lines:
                    row_is_valid = True
            
            if row_is_valid:
                item.setBackground(Qt.GlobalColor.transparent)
            else:
                item.setBackground(Qt.GlobalColor.red)
                valid = False
        
        self.grid_table.blockSignals(False)
        return valid

    def consolidate_results(self):
        """Consolidates overlapping columns and footings from all frames."""
        self.building.consolidated_results = {}
        
        # 1. Parse grid spacings
        try:
            sx = [float(s.strip()) for s in self.grid_x_input.text().split(',') if s.strip()]
            sy = [float(s.strip()) for s in self.grid_y_input.text().split(',') if s.strip()]
        except ValueError: return
        gx = [0.0] + list(np.cumsum(sx))
        gy = [0.0] + list(np.cumsum(sy))
        
        # 2. Map grid lines to frames
        grid_mapping = [] # (line_label, frame_name, offset, is_vertical)
        for row in range(self.grid_table.rowCount()):
            line_item = self.grid_table.item(row, 0)
            frame_widget = self.grid_table.cellWidget(row, 1)
            offset_item = self.grid_table.item(row, 2)
            if not line_item or not frame_widget or not offset_item: continue
            
            line = line_item.text().upper()
            frame = frame_widget.currentText()
            try: offset = float(offset_item.text())
            except ValueError: offset = 0.0
            grid_mapping.append((line, frame, offset, line.isdigit()))

        # 3. Iterate through levels
        for l_idx in range(self.grid_z_table.rowCount()):
            try:
                elev = float(self.grid_z_table.item(l_idx, 1).text())
            except: continue
            
            # 4. Iterate through grid intersections
            for i, x_pos in enumerate(gx):
                for j, y_pos in enumerate(gy):
                    n_total, mx_total, my_total = 0.0, 0.0, 0.0
                    
                    for line, fname, offset, is_vert in grid_mapping:
                        if fname not in self.frames: continue
                        f_ss = self.frames[fname].system
                        
                        if is_vert:
                            if int(line) != i + 1: continue
                            local_x = y_pos - gy[0] - offset
                        else:
                            alphabet = string.ascii_uppercase
                            if alphabet.find(line) != j: continue
                            local_x = x_pos - gx[0] - offset
                        
                        target_node_id = None
                        for nid, node in f_ss.node_map.items():
                            if np.isclose(node.vertex.x, local_x) and np.isclose(node.vertex.y, elev):
                                target_node_id = nid; break
                        
                        if target_node_id is None: continue
                        
                        if target_node_id in f_ss.reaction_forces:
                            reac = f_ss.reaction_forces[target_node_id]
                            n_total += getattr(reac, 'Fy', 0.0)
                            if is_vert: mx_total += getattr(reac, 'Tz', 0.0)
                            else: my_total += getattr(reac, 'Tz', 0.0)
                        
                        for el in f_ss.element_map.values():
                            if el.node_id2 == target_node_id: # Element above node
                                n1, n2 = f_ss.node_map[el.node_id1].vertex, f_ss.node_map[el.node_id2].vertex
                                if np.isclose(n1.x, n2.x): # Column
                                    if el.axial_force is not None: n_total += el.axial_force[-1]
                                    if el.bending_moment is not None:
                                        if is_vert: mx_total += el.bending_moment[-1]
                                        else: my_total += el.bending_moment[-1]

                    if not np.allclose([n_total, mx_total, my_total], 0):
                        self.building.consolidated_results[(i, j, l_idx)] = {'N': n_total, 'Mx': mx_total, 'My': my_total}

    def show_results_table(self):
        for i in reversed(range(self.results_table_layout.count())): 
            item = self.results_table_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        if self.building.consolidated_results:
            lbl = QLabel("Consolidated Column/Footing Results")
            lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
            self.results_table_layout.addWidget(lbl)
            table = QTableWidget(len(self.building.consolidated_results), 5)
            table.setHorizontalHeaderLabels(["Grid", "Level", "N (kN)", "Mx (kNm)", "My (kNm)"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            alphabet = string.ascii_uppercase
            for row, (key, vals) in enumerate(sorted(self.building.consolidated_results.items())):
                i, j, l = key
                grid_lbl = f"{alphabet[j]}{i+1}"
                level_lbl = self.grid_z_table.item(l, 0).text() if l < self.grid_z_table.rowCount() else f"L{l}"
                table.setItem(row, 0, QTableWidgetItem(grid_lbl))
                table.setItem(row, 1, QTableWidgetItem(level_lbl))
                table.setItem(row, 2, QTableWidgetItem(f"{vals['N']:.2f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{vals['Mx']:.2f}"))
                table.setItem(row, 4, QTableWidgetItem(f"{vals['My']:.2f}"))
            table.setMinimumHeight(200)
            self.results_table_layout.addWidget(table)

        for fname, model in self.frames.items():
            ss = model.system
            if not ss.element_map: continue
            lbl = QLabel(f"Frame: {fname}"); lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px; color: #2196F3;")
            self.results_table_layout.addWidget(lbl)
            beams, columns = [], []
            for eid, el in ss.element_map.items():
                n1, n2 = ss.node_map[el.node_id1].vertex, ss.node_map[el.node_id2].vertex
                if np.isclose(n1.x, n2.x): columns.append(el)
                else: beams.append(el)
            for group, group_label in [(beams, "Beams"), (columns, "Columns")]:
                if not group: continue
                self.results_table_layout.addWidget(QLabel(f"{group_label}"))
                table = QTableWidget(len(group), 5); table.setHorizontalHeaderLabels(["ID", "Length (m)", "Max M (kNm)", "Max V (kN)", "Max N (kN)"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                for row, el in enumerate(group):
                    m_max = np.max(np.abs(el.bending_moment)) if el.bending_moment is not None else 0
                    v_max = np.max(np.abs(el.shear_force)) if el.shear_force is not None else 0
                    n_max = np.max(np.abs(el.axial_force)) if el.axial_force is not None else 0
                    table.setItem(row, 0, QTableWidgetItem(str(el.id))); table.setItem(row, 1, QTableWidgetItem(f"{el.l:.2f}"))
                    table.setItem(row, 2, QTableWidgetItem(f"{m_max:.2f}")); table.setItem(row, 3, QTableWidgetItem(f"{v_max:.2f}")); table.setItem(row, 4, QTableWidgetItem(f"{n_max:.2f}"))
                table.setMinimumHeight(150); self.results_table_layout.addWidget(table)
        self.results_table_layout.addStretch()

    def solve_system(self):
        try:
            if not self.validate_grid_assignments():
                QMessageBox.warning(self, "Validation Error", "Some grid assignments refer to non-existent grid lines (highlighted in red).")
                return

            for name, model in self.frames.items():
                if model.system.element_map: model.system.solve()
            self.consolidate_results()
            QMessageBox.information(self, "Success", "Analysis Complete for all frames.")
            self.plotter.update_plot()
            self.update_member_selector()
        except Exception as e:
            QMessageBox.critical(self, "Solver Error", str(e))

    def run_ui_test(self):
        """Cycles through all major UI sections and modes to detect crashes/bugs."""
        print("\n--- Starting UI Smoke Test ---")
        errors = []
        
        # Save current state to restore after test
        original_sidebar_idx = self.sidebar_selector.currentIndex()
        original_view_mode = self.view_mode.currentIndex()
        
        try:
            # 1. Cycle through Sidebar Sections
            for i in range(self.sidebar_selector.count()):
                section_name = self.sidebar_selector.itemText(i)
                print(f"DEBUG: Testing section: {section_name}")
                try:
                    self.sidebar_selector.setCurrentIndex(i)
                    QApplication.processEvents()
                    
                    # Sub-navigation testing for complex widgets
                    if section_name == "Element Manager":
                        for j in range(self.element_mgr_widget.sub_selector.count()):
                            self.element_mgr_widget.sub_selector.setCurrentIndex(j)
                            QApplication.processEvents()
                            if self.element_mgr_widget.sub_selector.itemText(j) == "Loads":
                                for k in range(self.element_mgr_widget.load_type_selector.count()):
                                    self.element_mgr_widget.load_type_selector.setCurrentIndex(k)
                                    QApplication.processEvents()
                    
                    elif section_name == "Geometry":
                        for j in range(self.geom_selector.count()):
                            self.geom_selector.setCurrentIndex(j)
                            QApplication.processEvents()

                    # 2. Cycle through View Modes for each section to test plotter stability
                    for j in range(self.view_mode.count()):
                        self.view_mode.setCurrentIndex(j)
                        QApplication.processEvents()
                except Exception as e:
                    err_msg = f"Error in section '{section_name}': {type(e).__name__}: {e}"
                    print(f"DEBUG ERROR: {err_msg}")
                    print(traceback.format_exc())
                    errors.append(err_msg)
        finally:
            self.sidebar_selector.setCurrentIndex(original_sidebar_idx)
            self.view_mode.setCurrentIndex(original_view_mode)
            
        print("--- UI Smoke Test Finished ---\n")
        if errors:
            QMessageBox.warning(self, "UI Test Results", f"Encountered {len(errors)} errors. Check console for details.")
        else:
            QMessageBox.information(self, "UI Test Results", "No errors encountered during UI cycle.")

    def export_project(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Project", "", "JSON Files (*.json)")
        if not file_path: return
        if not file_path.lower().endswith('.json'): file_path += '.json'

        # Sync all frames first
        for name, model in self.frames.items():
            self.sync_blueprint_from_system(model.system, model)

        try:
            data = {
                "grid": {
                    "x": self.grid_x_input.text(),
                    "y": self.grid_y_input.text(),
                    "z": [[self.grid_z_table.item(r, 0).text(), self.grid_z_table.item(r, 1).text()] 
                          for r in range(self.grid_z_table.rowCount())],
                    "assignments": [[self.grid_table.item(r, 0).text(), 
                                     self.grid_table.cellWidget(r, 1).currentText(),
                                     self.grid_table.item(r, 2).text()]
                                    for r in range(self.grid_table.rowCount())]
                },
                "frames": {name: {
                    "elements": m.elements,
                    "supports": m.supports,
                    "point_loads": m.point_loads,
                    "moment_loads": m.moment_loads,
                    "q_loads": m.q_loads
                } for name, m in self.frames.items()},
                "slabs": [[self.slabs_table.item(r, 0).text(),
                           self.slabs_table.item(r, 1).text(),
                           self.slabs_table.item(r, 2).text(),
                           self.slabs_table.item(r, 3).text()]
                          for r in range(self.slabs_table.rowCount())],
                "current_frame": self.current_frame_name
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Success", "Project exported.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def import_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Project", "", "JSON Files (*.json)")
        if not file_path: return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # 1. Restore Grid
            self.grid_x_input.setText(data['grid']['x'])
            self.grid_y_input.setText(data['grid']['y'])
            
            self.grid_z_table.setRowCount(0)
            for name, elev in data['grid']['z']:
                row = self.grid_z_table.rowCount()
                self.grid_z_table.insertRow(row)
                self.grid_z_table.setItem(row, 0, QTableWidgetItem(name))
                self.grid_z_table.setItem(row, 1, QTableWidgetItem(elev))
            
            # 2. Restore Frames
            self.frames = {}
            self.frame_list.clear()
            self.global_frame_selector.clear()
            for name, f_data in data['frames'].items():
                model = FrameModel()
                model.elements = f_data['elements']
                model.supports = f_data['supports']
                model.point_loads = f_data['point_loads']
                model.moment_loads = f_data['moment_loads']
                model.q_loads = f_data['q_loads']
                self.frames[name] = model
                self.frame_list.addItem(name)
                self.global_frame_selector.addItem(name)
            
            # 3. Restore Grid Assignments
            self.grid_table.setRowCount(0)
            for line, frame, offset in data['grid']['assignments']:
                row = self.grid_table.rowCount()
                self.grid_table.insertRow(row)
                self.grid_table.setItem(row, 0, QTableWidgetItem(line))
                combo = QComboBox()
                combo.addItems(list(self.frames.keys()))
                combo.setCurrentText(frame)
                combo.currentTextChanged.connect(self.plotter.update_plot)
                self.grid_table.setCellWidget(row, 1, combo)
                self.grid_table.setItem(row, 2, QTableWidgetItem(offset))

            # 4. Restore Slabs
            self.slabs_table.setRowCount(0)
            for slab_data in data['slabs']:
                row = self.slabs_table.rowCount()
                self.slabs_table.insertRow(row)
                for col, val in enumerate(slab_data):
                    self.slabs_table.setItem(row, col, QTableWidgetItem(str(val)))
            
            self.current_frame_name = data.get('current_frame', list(self.frames.keys())[0])
            items = self.frame_list.findItems(self.current_frame_name, Qt.MatchFlag.MatchExactly)
            if items: self.frame_list.setCurrentItem(items[0])
            
            self.on_slab_data_changed()
            self.update_floor_levels()
            self.rebuild_system()
            QMessageBox.information(self, "Success", "Project imported.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import: {e}")

    def generate_test_building(self):
        # 1. Setup Grid
        self.grid_x_input.setText("6, 6") # 2 bays (3 lines: 1, 2, 3)
        self.grid_y_input.setText("5, 5, 5") # 3 bays (4 lines: A, B, C, D)
        
        self.grid_z_table.setRowCount(0)
        levels = [("Foundation", "-2.0"), ("Ground Floor", "0.0"), ("Floor 2", "3.5"), ("Floor 3", "7.0")]
        for name, elev in levels:
            row = self.grid_z_table.rowCount()
            self.grid_z_table.insertRow(row)
            self.grid_z_table.setItem(row, 0, QTableWidgetItem(name))
            self.grid_z_table.setItem(row, 1, QTableWidgetItem(elev))
        
        # 2. Create Frames
        self.frames = {}
        self.frame_list.clear()
        self.global_frame_selector.clear()
        
        # Foundation selection
        sup_type = self.test_foundation_type.currentText()
        self.frame_sup_type.setCurrentText(sup_type)
        if sup_type == "Spring":
            self.k_input.setText("5000")

        # Frame A: Used for lines 1-3 (running along Y, so 3 bays of 5m)
        self.frames["Frame 3-Bay"] = FrameModel()
        self.current_frame_name = "Frame 3-Bay"
        self.frame_bay_w.setText("5")
        self.frame_n_bays.setText("3")
        self.frame_n_floors.setText("3")
        self.build_frame_grid()
        
        # Frame B: Used for lines A-D (running along X, so 2 bays of 6m)
        self.frames["Frame 2-Bay"] = FrameModel()
        self.current_frame_name = "Frame 2-Bay"
        self.frame_bay_w.setText("6")
        self.frame_n_bays.setText("2")
        self.frame_n_floors.setText("3")
        self.build_frame_grid()
        
        # Refresh UI lists
        for name in self.frames:
            self.frame_list.addItem(name)
            self.global_frame_selector.addItem(name)
        
        # 3. Assign Frames
        self.grid_table.setRowCount(0)
        # Vertical lines 1, 2, 3
        for i in range(1, 4):
            self.add_grid_assignment()
            row = self.grid_table.rowCount() - 1
            self.grid_table.setItem(row, 0, QTableWidgetItem(str(i)))
            self.grid_table.cellWidget(row, 1).setCurrentText("Frame 3-Bay")
            
        # Horizontal lines A, B, C, D
        for char in "ABCD":
            self.add_grid_assignment()
            row = self.grid_table.rowCount() - 1
            self.grid_table.setItem(row, 0, QTableWidgetItem(char))
            self.grid_table.cellWidget(row, 1).setCurrentText("Frame 2-Bay")

        # 4. Add Slabs
        self.slabs_table.setRowCount(0)
        alphabet = string.ascii_uppercase
        for floor_idx, floor in enumerate(["Ground", "Floor 2", "Floor 3"]):
            elev = [0.0, 3.5, 7.0][floor_idx]
            # Iterate through grid cells: 2 bays in X (1-2, 2-3), 3 bays in Y (A-B, B-C, C-D)
            for i in range(1, 3): # X lines 1 to 2, 2 to 3
                for j in range(3): # Y lines A to B, B to C, C to D
                    row = self.slabs_table.rowCount()
                    self.slabs_table.insertRow(row)
                    slab_name = f"{floor} {alphabet[j]}{i}-{alphabet[j+1]}{i+1}"
                    pts_str = f"{alphabet[j]}{i}, {alphabet[j]}{i+1}, {alphabet[j+1]}{i+1}, {alphabet[j+1]}{i}"
                    self.slabs_table.setItem(row, 0, QTableWidgetItem(slab_name))
                    self.slabs_table.setItem(row, 1, QTableWidgetItem(pts_str))
                    self.slabs_table.setItem(row, 2, QTableWidgetItem("5.0"))
                    self.slabs_table.setItem(row, 3, QTableWidgetItem(f"{elev:.2f}"))
        
        self.on_slab_data_changed()
        self.update_floor_levels()
        
        # Distribute loads for each floor
        for i in range(self.floor_selector.count()):
            self.floor_selector.setCurrentIndex(i)
            self.distribute_slab_loads()
            
        self.sidebar_selector.setCurrentText("Grid")
        QMessageBox.information(self, "Test Generated", "3-Story building defined. Switch to 'Grid Plan' or '3D Wireframe' to view.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StructuralApp()
    window.show()
    sys.exit(app.exec())