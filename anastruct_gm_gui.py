import sys
import string
import numpy as np
import traceback

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
from PyQt6.QtCore import Qt, QTimer

from anastruct import SystemElements
from grid_manager import GridManager
from models import FrameModel, BuildingModel
from widgets import ElementManagerWidget
from plotter import StructuralPlotter

class GridManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GridManager Structural Analyzer")
        self.setGeometry(100, 100, 1400, 900)

        # --- Data Model ---
        self.frame_templates = {"Portal Frame": FrameModel()}
        self.current_template_name = "Portal Frame"
        self.building = BuildingModel()
        self.manager = None  # The GridManager instance for the whole building
        self.ss = self.frame_templates[self.current_template_name].system

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- Visualization (Right Panel) ---
        viz_container = QWidget()
        viz_layout = QVBoxLayout(viz_container)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        viz_layout.addWidget(self.canvas)

        # Visualization Controls
        controls_layout = QHBoxLayout()
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Structure", "Displacement", "Axial Force", "Shear Force", "Bending Moment", "Grid Plan", "3D Wireframe", "Member Analysis"])
        self.view_mode.currentTextChanged.connect(self.on_view_mode_changed)

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100); self.scale_slider.setValue(10); self.scale_slider.setFixedWidth(100)

        self.floor_selector = QComboBox()
        self.member_selector = QComboBox(); self.member_selector.setVisible(False)

        self.show_grid = QCheckBox("Grid"); self.show_grid.setChecked(True)
        self.show_ticks = QCheckBox("Ticks"); self.show_ticks.setChecked(True)
        self.show_grid_labels = QCheckBox("Labels"); self.show_grid_labels.setChecked(True)
        self.show_beam_marks = QCheckBox("Marks")
        self.lock_3d_rotation = QCheckBox("Lock 3D")

        controls_layout.addWidget(QLabel("View:")); controls_layout.addWidget(self.view_mode)
        controls_layout.addWidget(self.member_selector); controls_layout.addWidget(self.floor_selector)
        controls_layout.addWidget(QLabel("Scale:")); controls_layout.addWidget(self.scale_slider)
        controls_layout.addWidget(self.show_grid); controls_layout.addWidget(self.show_ticks)
        controls_layout.addWidget(self.show_grid_labels); controls_layout.addWidget(self.show_beam_marks)
        controls_layout.addWidget(self.lock_3d_rotation); controls_layout.addStretch()

        viz_layout.addLayout(controls_layout)

        # --- Initialize Plotter and connect signals ---
        self.plotter = StructuralPlotter(self)
        for widget in [self.scale_slider, self.show_grid, self.show_ticks, self.show_grid_labels, self.show_beam_marks, self.lock_3d_rotation, self.floor_selector, self.member_selector]:
            widget.blockSignals(True) # Block until fully initialized
            if isinstance(widget, QComboBox): widget.currentTextChanged.connect(self.plotter.update_plot)
            elif isinstance(widget, QSlider): widget.valueChanged.connect(self.plotter.update_plot)
            elif isinstance(widget, QCheckBox): widget.stateChanged.connect(self.plotter.update_plot)
            widget.blockSignals(False)

        # --- Workflow Tabs (Left Panel) ---
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(450)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.init_tab_grid()
        self.init_tab_frames()
        self.init_tab_layout()
        self.init_tab_analysis()
        self.init_tab_results()

        main_layout.addWidget(self.tabs); main_layout.addWidget(viz_container, stretch=1)

        self.update_floor_levels()
        self.on_tab_changed(0)

    def on_tab_changed(self, index):
        """Handle logic when switching between main workflow tabs."""
        tab_name = self.tabs.tabText(index)

        if tab_name == "2. Frame Templates":
            # When editing templates, show the template's system
            self.switch_frame_template(self.template_combo.currentText())
            return

        if tab_name == "5. Results":
            # When viewing results, show the selected result slice
            self.switch_result_view(self.res_combo.currentText())
            return

        self.ss = None
        if tab_name == "3. Building Layout":
            self.view_mode.setCurrentText("Grid Plan")
        self.plotter.update_plot()

    # --- TAB 1: GRID ---
    def init_tab_grid(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        grp_xy = QGroupBox("Plan Grid"); form_xy = QFormLayout(grp_xy)
        self.grid_x_input = QLineEdit("6, 6"); self.grid_y_input = QLineEdit("5, 5, 5")
        self.grid_x_input.textChanged.connect(self.plotter.update_plot)
        self.grid_y_input.textChanged.connect(self.plotter.update_plot)
        form_xy.addRow("X Spacings (m):", self.grid_x_input); form_xy.addRow("Y Spacings (m):", self.grid_y_input)
        layout.addWidget(grp_xy)

        grp_z = QGroupBox("Levels (Z)"); vbox_z = QVBoxLayout(grp_z)
        self.grid_z_table = QTableWidget(3, 2)
        self.grid_z_table.setHorizontalHeaderLabels(["Name", "Elevation (m)"])
        self.grid_z_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid_z_table.setItem(0, 0, QTableWidgetItem("Foundation")); self.grid_z_table.setItem(0, 1, QTableWidgetItem("-1.5"))
        self.grid_z_table.setItem(1, 0, QTableWidgetItem("Ground")); self.grid_z_table.setItem(1, 1, QTableWidgetItem("0.0"))
        self.grid_z_table.setItem(2, 0, QTableWidgetItem("Roof")); self.grid_z_table.setItem(2, 1, QTableWidgetItem("3.5"))
        self.grid_z_table.itemChanged.connect(self.update_floor_levels)
        
        hbox_z = QHBoxLayout(); btn_z_add = QPushButton("Add Level"); btn_z_del = QPushButton("Remove Level")
        btn_z_add.clicked.connect(lambda: self.grid_z_table.insertRow(self.grid_z_table.rowCount()))
        btn_z_del.clicked.connect(lambda: self.grid_z_table.rowCount() > 0 and self.grid_z_table.removeRow(self.grid_z_table.rowCount()-1))
        hbox_z.addWidget(btn_z_add); hbox_z.addWidget(btn_z_del)
        vbox_z.addWidget(self.grid_z_table); vbox_z.addLayout(hbox_z)
        
        btn_gen_test = QPushButton("Generate Test Building")
        btn_gen_test.clicked.connect(self.generate_test_building)
        layout.addWidget(btn_gen_test)
        layout.addWidget(grp_z)
        
        layout.addStretch()
        self.tabs.addTab(tab, "1. Grid")

    def update_floor_levels(self):
        self.floor_selector.blockSignals(True)
        self.floor_selector.clear()
        levels = []
        for r in range(self.grid_z_table.rowCount()):
            try:
                name = self.grid_z_table.item(r, 0).text()
                elev = float(self.grid_z_table.item(r, 1).text())
                levels.append((elev, name))
            except: continue
        levels.sort()
        for elev, name in levels: self.floor_selector.addItem(f"{name} ({elev}m)")
        self.floor_selector.blockSignals(False)
        self.plotter.update_plot()

    def _print_current_building_state(self):
        """Prints a summary of the current building definition to the console."""
        print("\n" + "="*60)
        print("           CURRENT BUILDING STATE DUMP")
        print("="*60)

        # 1. Grid Definition
        print("\n--- Grid Definition ---")
        print(f"  X Spacings: {self.grid_x_input.text()}")
        print(f"  Y Spacings: {self.grid_y_input.text()}")
        print("  Z Levels:")
        for r in range(self.grid_z_table.rowCount()):
            try:
                name = self.grid_z_table.item(r, 0).text()
                elev = self.grid_z_table.item(r, 1).text()
                print(f"    - {name}: {elev}m")
            except AttributeError:
                print("    - (empty row)")

        # 2. Frame Templates
        print("\n--- Frame Templates ---")
        for name, model in self.frame_templates.items():
            print(f"  Template '{name}':")
            print(f"    - Elements in blueprint: {len(model.elements)}")
            print(f"    - Supports in blueprint: {len(model.supports)}")
            if model.system and model.system.element_map:
                print(f"    - Anastruct system has {len(model.system.element_map)} elements and {len(model.system.node_map)} nodes.")
            else:
                print("    - Anastruct system not built or is empty.")

        # 3. Frame Assignments
        print("\n--- Frame Assignments ---")
        for r in range(self.grid_table.rowCount()):
            line = self.grid_table.item(r, 0).text()
            frame = self.grid_table.cellWidget(r, 1).currentText()
            offset = self.grid_table.item(r, 2).text()
            print(f"  - Grid Line '{line}': Use template '{frame}' with offset {offset}m")

        # 4. Slabs
        print("\n--- Slabs ---")
        for r in range(self.slabs_table.rowCount()):
            name = self.slabs_table.item(r, 0).text()
            points = self.slabs_table.item(r, 1).text()
            load = self.slabs_table.item(r, 2).text()
            level = self.slabs_table.item(r, 3).text()
            print(f"  - Slab '{name}': Points='{points}', Load={load} kN/m², Level={level}m")
        
        print("\n" + "="*60 + "\n")

    def generate_test_building(self):
        # 1. Grid
        self.grid_x_input.setText("5, 5")
        self.grid_y_input.setText("6, 6, 6")
        
        self.grid_z_table.setRowCount(0)
        z_elevations = [-1.5, 0.0, 3.5, 7.0]
        z_names = ["Foundation", "Ground", "Level 1", "Roof"]
        for name, elev in zip(z_names, z_elevations):
            r = self.grid_z_table.rowCount()
            self.grid_z_table.insertRow(r)
            self.grid_z_table.setItem(r, 0, QTableWidgetItem(name))
            self.grid_z_table.setItem(r, 1, QTableWidgetItem(str(elev)))
        self.update_floor_levels()

        # 2. Templates
        EA, EI = 2.1e8, 8e5
        
        # Calculate story heights relative to the foundation to build local frame templates
        story_heights = np.diff(z_elevations)
        local_z_coords = [0] + list(np.cumsum(story_heights))  # e.g., [0, 1.5, 5.0, 8.5]

        # Frame X (Spans 10m, 2 bays of 5m)
        fx = FrameModel()
        x_coords_fx = [0, 5, 10]
        for x in x_coords_fx:  # Columns
            for i in range(len(local_z_coords) - 1):
                fx.elements.append({'loc': [[x, local_z_coords[i]], [x, local_z_coords[i+1]]], 'EA': EA, 'EI': EI})
            fx.supports.append({'loc': [x, local_z_coords[0]], 'type': 'fixed', 'args': {}})
        for z in local_z_coords[1:]:  # Beams (skip foundation level)
            for i in range(len(x_coords_fx) - 1):
                fx.elements.append({'loc': [[x_coords_fx[i], z], [x_coords_fx[i+1], z]], 'EA': EA, 'EI': EI})
        self.frame_templates["Frame X"] = fx
        
        # Frame Y (Spans 18m, 3 bays of 6m)
        fy = FrameModel()
        x_coords_fy = [0, 6, 12, 18]
        for x in x_coords_fy:  # Columns
            for i in range(len(local_z_coords) - 1):
                fy.elements.append({'loc': [[x, local_z_coords[i]], [x, local_z_coords[i+1]]], 'EA': EA, 'EI': EI})
            fy.supports.append({'loc': [x, local_z_coords[0]], 'type': 'fixed', 'args': {}})
        for z in local_z_coords[1:]:  # Beams
            for i in range(len(x_coords_fy) - 1):
                fy.elements.append({'loc': [[x_coords_fy[i], z], [x_coords_fy[i+1], z]], 'EA': EA, 'EI': EI})
        self.frame_templates["Frame Y"] = fy
        
        # Rebuild the anastruct systems for the new templates
        original_name = self.current_template_name
        for name in ["Frame X", "Frame Y"]:
            self.current_template_name = name
            self.rebuild_system()
        
        # Restore context and update UI
        self.current_template_name = original_name
        self.template_combo.clear()
        self.template_combo.addItems(list(self.frame_templates.keys()))
        self.template_combo.setCurrentText("Frame X")

        # 3. Assignments
        self.grid_table.setRowCount(0)
        for line in ["A", "B", "C", "D"]:
            self.add_assignment()
            r = self.grid_table.rowCount() - 1
            self.grid_table.setItem(r, 0, QTableWidgetItem(line))
            self.grid_table.cellWidget(r, 1).setCurrentText("Frame X")
        for line in ["1", "2", "3"]:
            self.add_assignment()
            r = self.grid_table.rowCount() - 1
            self.grid_table.setItem(r, 0, QTableWidgetItem(line))
            self.grid_table.cellWidget(r, 1).setCurrentText("Frame Y")

        # 4. Slabs
        self.slabs_table.setRowCount(0)
        r = self.slabs_table.rowCount()
        self.slabs_table.insertRow(r)
        self.slabs_table.setItem(r, 0, QTableWidgetItem("L1 Slab"))
        self.slabs_table.setItem(r, 1, QTableWidgetItem("A1, D1, D3, A3"))
        self.slabs_table.setItem(r, 2, QTableWidgetItem("5.0"))
        self.slabs_table.setItem(r, 3, QTableWidgetItem("3.5"))
        
        self.on_slab_data_changed()
        
        QMessageBox.information(self, "Success", "Test building generated.")
        self._print_current_building_state()
        self.plotter.update_plot()

    # --- TAB 2: FRAME TEMPLATES ---
    def init_tab_frames(self):
        tab = QWidget(); tab.setObjectName("tab_frames")
        layout = QVBoxLayout(tab)
        
        hbox_mng = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItems(list(self.frame_templates.keys()))
        self.template_combo.currentTextChanged.connect(self.switch_frame_template)
        btn_new = QPushButton("New"); btn_new.clicked.connect(self.add_frame_template)
        btn_del = QPushButton("Delete"); btn_del.clicked.connect(self.delete_frame_template)
        hbox_mng.addWidget(QLabel("Template:")); hbox_mng.addWidget(self.template_combo)
        hbox_mng.addWidget(btn_new); hbox_mng.addWidget(btn_del)
        layout.addLayout(hbox_mng)
        
        gen_group = QGroupBox("Frame Generators")
        gen_layout = QFormLayout(gen_group)
        self.grid_bays = QLineEdit("6, 6, 6"); self.grid_stories = QLineEdit("4, 3.5")
        btn_gen_grid = QPushButton("Generate Multi-bay Frame")
        btn_gen_grid.clicked.connect(self.generate_grid_frame)
        gen_layout.addRow("Bay Widths (m):", self.grid_bays)
        gen_layout.addRow("Story Heights (m):", self.grid_stories)
        gen_layout.addRow(btn_gen_grid)
        layout.addWidget(gen_group)
        
        self.element_mgr = ElementManagerWidget(self)
        layout.addWidget(self.element_mgr)
        self.tabs.addTab(tab, "2. Frame Templates")

    def generate_grid_frame(self):
        try:
            bay_widths = [float(b.strip()) for b in self.grid_bays.text().split(',') if b.strip()]
            story_heights = [float(h.strip()) for h in self.grid_stories.text().split(',') if h.strip()]
            model = self.frame_templates[self.current_template_name]; model.clear()
            EA, EI = 2.1e8, 8e5 # Defaults
            x_coords = [0] + list(np.cumsum(bay_widths)); y_coords = [0] + list(np.cumsum(story_heights))
            for x in x_coords:
                for i in range(len(y_coords) - 1):
                    model.elements.append({'loc': [[x, y_coords[i]], [x, y_coords[i+1]]], 'EA': EA, 'EI': EI})
            for y in y_coords[1:]:
                for i in range(len(x_coords) - 1):
                    model.elements.append({'loc': [[x_coords[i], y], [x_coords[i+1], y]], 'EA': EA, 'EI': EI})
            for x in x_coords: model.supports.append({'loc': [x, 0], 'type': 'fixed', 'args': {}})
            self.rebuild_system(); self.element_mgr.refresh_data()
            QMessageBox.information(self, "Success", "Multi-bay frame generated.")
        except Exception as e: QMessageBox.critical(self, "Error", f"Could not generate frame: {e}")

    def add_frame_template(self):
        name, ok = QInputDialog.getText(self, "New Frame", "Frame Name:")
        if ok and name and name not in self.frame_templates:
            self.frame_templates[name] = FrameModel()
            self.template_combo.addItem(name); self.template_combo.setCurrentText(name)

    def delete_frame_template(self):
        if len(self.frame_templates) > 1:
            del self.frame_templates[self.template_combo.currentText()]
            self.template_combo.removeItem(self.template_combo.currentIndex())

    def switch_frame_template(self, name):
        if name not in self.frame_templates: return
        self.current_template_name = name
        self.ss = self.frame_templates[name].system
        self.element_mgr.refresh_data()
        self.view_mode.setCurrentText("Structure")
        self.plotter.update_plot()

    # --- TAB 3: BUILDING LAYOUT ---
    def init_tab_layout(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grp_assign = QGroupBox("Assign Frames to Grid Lines"); vbox_assign = QVBoxLayout(grp_assign)
        self.grid_table = QTableWidget(0, 3)
        self.grid_table.setHorizontalHeaderLabels(["Grid Line", "Frame Template", "Offset (m)"])
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hbox_assign_btns = QHBoxLayout()
        btn_add_assign = QPushButton("Add"); btn_del_assign = QPushButton("Remove")
        btn_add_assign.clicked.connect(self.add_assignment)
        btn_del_assign.clicked.connect(lambda: self.grid_table.removeRow(self.grid_table.currentRow()))
        hbox_assign_btns.addWidget(btn_add_assign); hbox_assign_btns.addWidget(btn_del_assign)
        vbox_assign.addWidget(self.grid_table); vbox_assign.addLayout(hbox_assign_btns)
        layout.addWidget(grp_assign)
        
        grp_slabs = QGroupBox("Slabs & Area Loads"); vbox_slabs = QVBoxLayout(grp_slabs)
        self.slabs_table = QTableWidget(0, 4)
        self.slabs_table.setHorizontalHeaderLabels(["Name", "Points (e.g. A1,B2)", "Load (kN/m²)", "Level (m)"])
        self.slabs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.slabs_table.itemChanged.connect(self.on_slab_data_changed)
        hbox_slab_btns = QHBoxLayout()
        btn_add_slab = QPushButton("Add"); btn_del_slab = QPushButton("Remove")
        btn_add_slab.clicked.connect(self.add_slab)
        btn_del_slab.clicked.connect(self.delete_slab)
        hbox_slab_btns.addWidget(btn_add_slab); hbox_slab_btns.addWidget(btn_del_slab)
        vbox_slabs.addWidget(self.slabs_table); vbox_slabs.addLayout(hbox_slab_btns)
        layout.addWidget(grp_slabs)
        
        self.tabs.addTab(tab, "3. Building Layout")

    def on_slab_data_changed(self, item=None):
        self.building.slabs.clear()
        for r in range(self.slabs_table.rowCount()):
            try:
                name = self.slabs_table.item(r, 0).text()
                pts_str = self.slabs_table.item(r, 1).text()
                level = float(self.slabs_table.item(r, 3).text())
                
                pts = []
                for p_str in pts_str.split(','):
                    p_str = p_str.strip().upper()
                    if not p_str: continue
                    i = 0
                    while i < len(p_str) and p_str[i].isalpha(): i += 1
                    y_label, x_char = p_str[:i], p_str[i:]
                    if not y_label or not x_char or not x_char.isdigit(): continue
                    y_idx = string.ascii_uppercase.find(y_label)
                    x_idx = int(x_char) - 1
                    pts.append((x_idx, y_idx))
                
                if pts:
                    self.building.slabs[name] = {'points': pts, 'level': level}
            except (ValueError, AttributeError, IndexError):
                continue
        self.plotter.update_plot()

    def add_assignment(self):
        row = self.grid_table.rowCount()
        self.grid_table.insertRow(row)
        self.grid_table.setItem(row, 0, QTableWidgetItem("A"))
        combo = QComboBox(); combo.addItems(list(self.frame_templates.keys()))
        self.grid_table.setCellWidget(row, 1, combo)
        self.grid_table.setItem(row, 2, QTableWidgetItem("0.0"))

    def add_slab(self):
        row = self.slabs_table.rowCount()
        self.slabs_table.insertRow(row)
        self.slabs_table.setItem(row, 0, QTableWidgetItem(f"Slab {row+1}"))
        self.slabs_table.setItem(row, 1, QTableWidgetItem("A1, B1, B2, A2"))
        self.slabs_table.setItem(row, 2, QTableWidgetItem("5.0"))
        self.slabs_table.setItem(row, 3, QTableWidgetItem("3.5"))
        self.on_slab_data_changed()

    def delete_slab(self):
        if self.slabs_table.currentRow() >= 0:
            self.slabs_table.removeRow(self.slabs_table.currentRow())
            self.on_slab_data_changed()

    # --- TAB 4: ANALYSIS ---
    def init_tab_analysis(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grp_found = QGroupBox("Foundation"); form_found = QFormLayout(grp_found)
        self.foundation_level_combo = QComboBox()
        self.foundation_type_combo = QComboBox(); self.foundation_type_combo.addItems(["Fixed", "Hinged", "Roll", "Spring"])
        form_found.addRow("Foundation Level:", self.foundation_level_combo)
        form_found.addRow("Support Type:", self.foundation_type_combo)
        layout.addWidget(grp_found)

        self.btn_run = QPushButton("RUN ANALYSIS")
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_run.clicked.connect(self.run_analysis)
        layout.addWidget(self.btn_run)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        
        self.tabs.addTab(tab, "4. Analysis")
        self.grid_z_table.itemChanged.connect(self._update_foundation_combo)
        self._update_foundation_combo()

    def _update_foundation_combo(self):
        self.foundation_level_combo.clear()
        for r in range(self.grid_z_table.rowCount()):
            try:
                name = self.grid_z_table.item(r, 0).text()
                elev = self.grid_z_table.item(r, 1).text()
                self.foundation_level_combo.addItem(f"{name} ({elev}m)")
            except: pass

    def run_analysis(self):
        self.log_list.clear(); self.progress.setValue(0)
        
        def log(msg): self.log_list.addItem(msg); QApplication.processEvents()

        try:
            # 1. Create GridManager
            x_coords = [0.0] + list(np.cumsum([float(s) for s in self.grid_x_input.text().split(',') if s.strip()]))
            y_coords = [0.0] + list(np.cumsum([float(s) for s in self.grid_y_input.text().split(',') if s.strip()]))
            z_coords = sorted([float(self.grid_z_table.item(r, 1).text()) for r in range(self.grid_z_table.rowCount())])
            self.manager = GridManager(x_coords, y_coords, z_coords)
            log("✅ GridManager initialized.")

            # 2. Populate members from assignments
            self.populate_manager_from_assignments()
            log("✅ Members added to GridManager.")

            # 3. Add slab loads
            self.add_slab_loads_to_manager()
            log("✅ Slab loads added.")

            # 4. Set foundation
            z_found_str = self.foundation_level_combo.currentText().split('(')[1].replace('m)', '')
            z_foundation = float(z_found_str)
            support_type = self.foundation_type_combo.currentText().lower()
            self.manager.set_foundation(z_level=z_foundation, support_type=support_type)
            log(f"✅ Foundation set at z={z_foundation} as {support_type}.")

            # 5. Solve
            log("⏳ Solving building... (this may take a moment)")
            self.manager.solve_building()
            log("🚀 Analysis Complete.")
            self.progress.setValue(100)
            
            # 6. Switch to results
            QTimer.singleShot(500, lambda: self.tabs.setCurrentIndex(4))
            self.refresh_results_tab()

        except Exception as e:
            log(f"❌ ANALYSIS FAILED: {e}")
            traceback.print_exc()

    def populate_manager_from_assignments(self):
        gx, gy = self.manager.grid['x'], self.manager.grid['y']
        
        # Determine foundation level (min_z) to align frame templates
        z_coords = sorted([float(self.grid_z_table.item(r, 1).text()) for r in range(self.grid_z_table.rowCount())])
        min_z = z_coords[0] if z_coords else 0.0

        for r in range(self.grid_table.rowCount()):
            line_label = self.grid_table.item(r, 0).text().upper()
            template_name = self.grid_table.cellWidget(r, 1).currentText()
            offset = float(self.grid_table.item(r, 2).text())
            template = self.frame_templates.get(template_name)
            if not template: continue

            is_vert_line = line_label.isdigit()
            for el in template.elements:
                (x1_loc, z1_loc), (x2_loc, z2_loc) = el['loc']
                if is_vert_line:
                    line_idx = int(line_label) - 1
                    if line_idx >= len(gx): continue
                    x_pos = gx[line_idx]
                    start_xyz = (x_pos, x1_loc + offset, z1_loc + min_z)
                    end_xyz = (x_pos, x2_loc + offset, z2_loc + min_z)
                else:
                    line_idx = string.ascii_uppercase.find(line_label)
                    if line_idx >= len(gy): continue
                    y_pos = gy[line_idx]
                    start_xyz = (x1_loc + offset, y_pos, z1_loc + min_z)
                    end_xyz = (x2_loc + offset, y_pos, z2_loc + min_z)
                
                # Use self-weight from template if available
                g = el.get('g', 0)
                self.manager.add_orthogonal_member(start_xyz, end_xyz, el['EA'], el['EI'], g=g)

    def add_slab_loads_to_manager(self):
        gx, gy = self.manager.grid['x'], self.manager.grid['y']
        for r in range(self.slabs_table.rowCount()):
            try:
                pts_str = self.slabs_table.item(r, 1).text()
                load = float(self.slabs_table.item(r, 2).text())
                level = float(self.slabs_table.item(r, 3).text())
                
                pts = []
                for p in pts_str.split(','):
                    p = p.strip().upper()
                    if not p: continue
                    idx = 0
                    while idx < len(p) and p[idx].isalpha(): idx += 1
                    y_char, x_char = p[:idx], p[idx:]
                    pts.append((int(x_char) - 1, string.ascii_uppercase.find(y_char)))
                
                if not pts: continue
                x_indices = [p[0] for p in pts]; y_indices = [p[1] for p in pts]
                x_range = (gx[min(x_indices)], gx[max(x_indices)])
                y_range = (gy[min(y_indices)], gy[max(y_indices)])
                self.manager.add_slab_load(x_range, y_range, level, load)
            except Exception as e:
                self.log_list.addItem(f"Warning: Could not parse slab row {r}: {e}")

    # --- TAB 5: RESULTS ---
    def init_tab_results(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        hbox_sel = QHBoxLayout()
        self.res_combo = QComboBox()
        self.res_combo.currentTextChanged.connect(self.switch_result_view)
        hbox_sel.addWidget(QLabel("Select Grid Line:")); hbox_sel.addWidget(self.res_combo)
        layout.addLayout(hbox_sel)
        
        self.res_table = QTableWidget()
        layout.addWidget(self.res_table)
        self.tabs.addTab(tab, "5. Results")

    def refresh_results_tab(self):
        self.res_combo.blockSignals(True); self.res_combo.clear()
        if not self.manager: return
        
        for y, frame in self.manager.xz_frames.items():
            if frame.element_map: self.res_combo.addItem(f"XZ Frame at Y={y}")
        for x, frame in self.manager.yz_frames.items():
            if frame.element_map: self.res_combo.addItem(f"YZ Frame at X={x}")
        
        self.res_combo.blockSignals(False)
        if self.res_combo.count() > 0: self.switch_result_view(self.res_combo.currentText())
        self.consolidate_reactions()

    def switch_result_view(self, label):
        if not self.manager or not label:
            self.ss = None
        else:
            parts = label.split(' at ')
            plane, coord_str = parts[0].split(' ')[0], parts[1].split('=')[1]
            coord = float(coord_str)
            
            if plane == 'XZ': self.ss = self.manager.xz_frames.get(coord)
            elif plane == 'YZ': self.ss = self.manager.yz_frames.get(coord)
            else: self.ss = None
        
        if self.ss:
            self.view_mode.setCurrentText("Bending Moment")
            self.plotter.update_plot()
            self.update_member_list()

    def consolidate_reactions(self):
        self.res_table.clear(); self.res_table.setRowCount(0)
        self.res_table.setColumnCount(5)
        self.res_table.setHorizontalHeaderLabels(["Plane", "Grid Line", "Node ID", "Rx (kN)", "Rz (kN)"])
        
        if not self.manager: return
        
        all_frames = list(self.manager.xz_frames.items()) + list(self.manager.yz_frames.items())
        for coord, ss in all_frames:
            if not ss.reaction_forces: continue
            for nid, reac in ss.reaction_forces.items():
                row = self.res_table.rowCount()
                self.res_table.insertRow(row)
                plane = "XZ" if isinstance(coord, float) and coord in self.manager.grid['y'] else "YZ"
                self.res_table.setItem(row, 0, QTableWidgetItem(plane))
                self.res_table.setItem(row, 1, QTableWidgetItem(str(coord)))
                self.res_table.setItem(row, 2, QTableWidgetItem(str(nid)))
                self.res_table.setItem(row, 3, QTableWidgetItem(f"{reac.Fx:.2f}"))
                self.res_table.setItem(row, 4, QTableWidgetItem(f"{reac.Fy:.2f}"))

    # --- SHARED LOGIC & UTILITIES ---
    def on_view_mode_changed(self, text):
        is_template_active = self.tabs.tabText(self.tabs.currentIndex()) == "2. Frame Templates"
        if is_template_active and text not in ["Structure", "Grid Plan", "3D Wireframe"]:
            QTimer.singleShot(0, lambda: self.view_mode.setCurrentText("Structure"))
            QMessageBox.information(self, "Info", "Result views are only available after running analysis.")
            return

        self.floor_selector.setEnabled(text == "Grid Plan")
        self.member_selector.setVisible(text == "Member Analysis")
        self.plotter.update_plot()

    def update_member_list(self):
        self.member_selector.clear()
        if self.ss:
            for eid in sorted(self.ss.element_map.keys()):
                self.member_selector.addItem(f"Element-{eid}")

    def _update_blueprint_from_overrides(self, model, node_coords, element_props, supports_info, loads_info):
        """Updates the FrameModel blueprint from ElementManagerWidget edits."""
        node_map = {nid: node.vertex for nid, node in model.system.node_map.items()}
        if element_props:
            for eid, props in element_props.items():
                if 0 <= eid - 1 < len(model.elements):
                    model.elements[eid-1]['EA'] = props['EA']
                    model.elements[eid-1]['EI'] = props['EI']
        if node_coords:
            for nid, coords in node_coords.items():
                old_v = node_map.get(nid)
                if not old_v: continue
                for item_list in [model.elements, model.supports, model.point_loads, model.moment_loads]:
                    for item in item_list:
                        if 'loc' in item:
                            if isinstance(item['loc'], list) and len(item['loc']) == 2 and isinstance(item['loc'][0], list): # Element
                                if np.allclose(item['loc'][0], [old_v.x, old_v.y]): item['loc'][0] = coords
                                if np.allclose(item['loc'][1], [old_v.x, old_v.y]): item['loc'][1] = coords
                            elif np.allclose(item['loc'], [old_v.x, old_v.y]): # Node-based
                                item['loc'] = coords
        if supports_info is not None:
            model.supports = []
            for nid, stype in supports_info.items():
                v = node_map.get(nid)
                if v: model.supports.append({'loc': [v.x, v.y], 'type': stype.lower(), 'args': {}})
        if loads_info is not None:
            model.point_loads, model.moment_loads, model.q_loads = [], [], []
            for l in loads_info:
                if l['type'] == 'Point':
                    v = node_map.get(l['id'])
                    if v: model.point_loads.append({'loc': [v.x, v.y], 'Fx': l['v1'], 'Fz': l['v2']})
                elif l['type'] == 'Moment':
                    v = node_map.get(l['id'])
                    if v: model.moment_loads.append({'loc': [v.x, v.y], 'Ty': l['v1']})
                elif l['type'] == 'q-Load':
                    model.q_loads.append({'element_idx': l['id'] - 1, 'q': l['v1'], 'dir': l['v2'], 'qp': l.get('v3', 0)})

    def rebuild_system(self, node_coords=None, element_props=None, supports_info=None, loads_info=None):
        """Rebuilds the anastruct system for the currently active FRAME TEMPLATE."""
        model = self.frame_templates[self.current_template_name]
        if any([node_coords, element_props, supports_info, loads_info]):
            self._update_blueprint_from_overrides(model, node_coords, element_props, supports_info, loads_info)

        ss = SystemElements()
        for e in model.elements: ss.add_element(location=e['loc'], EA=e['EA'], EI=e['EI'])
        for s in model.supports:
            nid = ss.find_node_id(vertex=s['loc'])
            if nid:
                stype = s.get('type', '').lower()
                if stype == 'fixed': ss.add_support_fixed(nid)
                elif stype == 'hinged': ss.add_support_hinged(nid)
                elif stype == 'roll': ss.add_support_roll(nid, **s.get('args', {}))
        for p in model.point_loads:
            nid = ss.find_node_id(vertex=p['loc'])
            if nid: ss.point_load(nid, Fx=p.get('Fx', 0), Fz=p.get('Fz', 0))
        for m in model.moment_loads:
            nid = ss.find_node_id(vertex=m['loc'])
            if nid: ss.moment_load(nid, Ty=m.get('Ty', 0))
        for q in model.q_loads:
            eid = q.get('element_idx', -1) + 1
            if eid in ss.element_map: ss.q_load(q=q.get('q'), element_id=eid, direction=q.get('dir', 'element'), q_perp=q.get('qp', 0))

        model.system = ss
        self.ss = ss
        self.update_member_list()
        self.plotter.update_plot()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GridManagerGUI()
    window.show()
    sys.exit(app.exec())