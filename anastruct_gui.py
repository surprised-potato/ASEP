import sys
import string
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
    QComboBox, QSlider, QScrollArea, QMessageBox, QTabWidget, QCheckBox,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QInputDialog, QGridLayout, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt

from anastruct import SystemElements

class ElementManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ss = parent.ss
        self.setWindowTitle("Element Manager")
        self.resize(900, 600)
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Elements Tab
        self.elements_tab = QWidget()
        self.elements_layout = QVBoxLayout(self.elements_tab)
        self.elements_table = QTableWidget()
        self.elements_table.setColumnCount(5)
        self.elements_table.setHorizontalHeaderLabels(["ID", "Node 1", "Node 2", "EA", "EI"])
        self.elements_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.elements_layout.addWidget(self.elements_table)
        self.del_el_btn = QPushButton("Delete Selected Elements")
        self.del_el_btn.clicked.connect(self.delete_elements)
        self.elements_layout.addWidget(self.del_el_btn)
        self.tabs.addTab(self.elements_tab, "Elements")
        
        # Nodes Tab
        self.nodes_tab = QWidget()
        self.nodes_layout = QVBoxLayout(self.nodes_tab)
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(3)
        self.nodes_table.setHorizontalHeaderLabels(["ID", "X", "Y"])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nodes_layout.addWidget(self.nodes_table)
        self.tabs.addTab(self.nodes_tab, "Nodes")
        
        # Supports Tab
        self.supports_tab = QWidget()
        self.supports_layout = QVBoxLayout(self.supports_tab)
        self.supports_table = QTableWidget()
        self.supports_table.setColumnCount(2)
        self.supports_table.setHorizontalHeaderLabels(["Node ID", "Type"])
        self.supports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.supports_layout.addWidget(self.supports_table)
        self.del_sup_btn = QPushButton("Delete Selected Supports")
        self.del_sup_btn.clicked.connect(self.delete_supports)
        self.supports_layout.addWidget(self.del_sup_btn)
        self.tabs.addTab(self.supports_tab, "Supports")
        
        # Loads Tab
        self.loads_tab = QWidget()
        self.loads_layout = QVBoxLayout(self.loads_tab)
        self.loads_table = QTableWidget()
        self.loads_table.setColumnCount(4)
        self.loads_table.setHorizontalHeaderLabels(["Type", "ID", "Value 1", "Value 2"])
        self.loads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.loads_layout.addWidget(self.loads_table)
        self.del_load_btn = QPushButton("Delete Selected Loads")
        self.del_load_btn.clicked.connect(self.delete_loads)
        self.loads_layout.addWidget(self.del_load_btn)
        self.tabs.addTab(self.loads_tab, "Loads")

        # Save Changes Button
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; height: 30px;")
        self.save_btn.clicked.connect(self.confirm_save)
        self.layout.addWidget(self.save_btn)

        # Connect change signals
        self.elements_table.itemChanged.connect(self.on_element_change)
        self.nodes_table.itemChanged.connect(self.on_node_change)

        self.refresh_data()

    def refresh_data(self):
        self.ss = self.parent_app.ss
        self.block_signals(True)
        
        # Elements
        self.elements_table.setRowCount(0)
        for el_id, el in self.ss.element_map.items():
            row = self.elements_table.rowCount()
            self.elements_table.insertRow(row)
            item_id = QTableWidgetItem(str(el_id))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.elements_table.setItem(row, 0, item_id)
            item_n1 = QTableWidgetItem(str(el.node_id1))
            item_n1.setFlags(item_n1.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.elements_table.setItem(row, 1, item_n1)
            item_n2 = QTableWidgetItem(str(el.node_id2))
            item_n2.setFlags(item_n2.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.elements_table.setItem(row, 2, item_n2)
            self.elements_table.setItem(row, 3, QTableWidgetItem(str(el.EA)))
            self.elements_table.setItem(row, 4, QTableWidgetItem(str(el.EI)))

        # Nodes
        self.nodes_table.setRowCount(0)
        for n_id, node in self.ss.node_map.items():
            row = self.nodes_table.rowCount()
            self.nodes_table.insertRow(row)
            item_id = QTableWidgetItem(str(n_id))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.nodes_table.setItem(row, 0, item_id)
            self.nodes_table.setItem(row, 1, QTableWidgetItem(str(node.vertex.x)))
            self.nodes_table.setItem(row, 2, QTableWidgetItem(str(node.vertex.y)))

        # Supports
        self.supports_table.setRowCount(0)
        if hasattr(self.ss, 'supports_fixed'):
            for node in self.ss.supports_fixed: self._add_support_row(node.id, "Fixed")
        if hasattr(self.ss, 'supports_hinged'):
            for node in self.ss.supports_hinged: self._add_support_row(node.id, "Hinged")
        
        if hasattr(self.ss, 'supports_roll') and hasattr(self.ss, 'supports_roll_direction'):
            for i, node in enumerate(self.ss.supports_roll):
                direction = self.ss.supports_roll_direction[i]
                self._add_support_row(node.id, f"Roll (dir={direction})")

        if hasattr(self.ss, 'supports_spring_args'):
            for nid, translation, k, _ in self.ss.supports_spring_args:
                self._add_support_row(nid, f"Spring (k={k}, dir={translation})")

        # Loads
        self.loads_table.setRowCount(0)
        
        # Point Loads
        for node_id, load_data in self.ss.loads_point.items():
            if isinstance(load_data, dict):
                fx = load_data.get('Fx', 0)
                fz = load_data.get('Fz', 0)
            elif isinstance(load_data, (list, tuple)):
                fx = load_data[0]
                fz = load_data[1]
            else: fx, fz = 0, 0
            self._add_load_row("Point", node_id, f"Fx={fx}", f"Fz={fz}", node_id)
            
        # Moment Loads
        for node_id, load_data in self.ss.loads_moment.items():
            if isinstance(load_data, dict):
                ty = load_data.get('Ty', 0)
            elif isinstance(load_data, (list, tuple)):
                ty = load_data[0]
            else: ty = load_data
            self._add_load_row("Moment", node_id, f"Ty={ty}", "", node_id)
            
        # q-Loads
        for el_id, load_data in self.ss.loads_q.items():
            if isinstance(load_data, dict):
                q = load_data.get('q', 0)
                direction = load_data.get('direction', '')
            elif isinstance(load_data, (list, tuple)):
                q = load_data[0]
                direction = load_data[1]
            else: q, direction = 0, ''
            self._add_load_row("q-Load", el_id, f"q={q}", f"Dir={direction}", el_id)

        self.block_signals(False)

    def _add_support_row(self, nid, type_str):
        row = self.supports_table.rowCount()
        self.supports_table.insertRow(row)
        self.supports_table.setItem(row, 0, QTableWidgetItem(str(nid)))
        self.supports_table.setItem(row, 1, QTableWidgetItem(type_str))

    def _add_load_row(self, ltype, oid, v1, v2, index):
        row = self.loads_table.rowCount()
        self.loads_table.insertRow(row)
        self.loads_table.setItem(row, 0, QTableWidgetItem(ltype))
        self.loads_table.setItem(row, 1, QTableWidgetItem(str(oid)))
        self.loads_table.setItem(row, 2, QTableWidgetItem(v1))
        self.loads_table.setItem(row, 3, QTableWidgetItem(v2))
        self.loads_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, index)

    def block_signals(self, block):
        self.elements_table.blockSignals(block)
        self.nodes_table.blockSignals(block)

    def on_element_change(self, item):
        try:
            el_id = int(self.elements_table.item(item.row(), 0).text())
            val = float(item.text())
            if item.column() == 3: self.ss.element_map[el_id].EA = val
            elif item.column() == 4: self.ss.element_map[el_id].EI = val
        except (ValueError, KeyError, AttributeError): pass

    def on_node_change(self, item):
        # Pending changes are stored in the table and applied during confirm_save -> rebuild_system
        pass

    def apply_changes(self):
        """Extracts data from tables and triggers a system rebuild."""
        node_coords = {}
        for row in range(self.nodes_table.rowCount()):
            try:
                nid = int(self.nodes_table.item(row, 0).text())
                x = float(self.nodes_table.item(row, 1).text())
                y = float(self.nodes_table.item(row, 2).text())
                node_coords[nid] = [x, y]
            except (ValueError, AttributeError): continue
        
        element_props = {}
        for row in range(self.elements_table.rowCount()):
            try:
                eid = int(self.elements_table.item(row, 0).text())
                ea = float(self.elements_table.item(row, 3).text())
                ei = float(self.elements_table.item(row, 4).text())
                element_props[eid] = {'EA': ea, 'EI': ei}
            except (ValueError, AttributeError): continue

        self.parent_app.rebuild_system(node_coords=node_coords, element_props=element_props)
        self.refresh_data()

    def confirm_save(self):
        reply = QMessageBox.question(
            self, 'Confirm Save', 
            "Do you want to save changes and rebuild the model?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.apply_changes()

    def delete_elements(self):
        for row in sorted(set(i.row() for i in self.elements_table.selectedIndexes()), reverse=True):
            el_id = int(self.elements_table.item(row, 0).text())
            if el_id in self.ss.element_map:
                el = self.ss.element_map.pop(el_id)
                self.ss.loads_q.pop(el_id, None)
                for nid in [el.node_id1, el.node_id2]:
                    if not any(e.node_id1 == nid or e.node_id2 == nid for e in self.ss.element_map.values()):
                        self.ss.loads_point.pop(nid, None)
                        self.ss.loads_moment.pop(nid, None)
        self.apply_changes()

    def delete_supports(self):
        for row in sorted(set(i.row() for i in self.supports_table.selectedIndexes()), reverse=True):
            nid_to_del = int(self.supports_table.item(row, 0).text())
            
            if hasattr(self.ss, 'supports_fixed'):
                self.ss.supports_fixed = [n for n in self.ss.supports_fixed if n.id != nid_to_del]
            if hasattr(self.ss, 'supports_hinged'):
                self.ss.supports_hinged = [n for n in self.ss.supports_hinged if n.id != nid_to_del]

            if hasattr(self.ss, 'supports_roll'):
                new_rolls, new_dirs = [], []
                for i, node in enumerate(self.ss.supports_roll):
                    if node.id != nid_to_del:
                        new_rolls.append(node)
                        new_dirs.append(self.ss.supports_roll_direction[i])
                self.ss.supports_roll = new_rolls
                self.ss.supports_roll_direction = new_dirs

            if hasattr(self.ss, 'supports_spring_args'):
                self.ss.supports_spring_args = [s for s in self.ss.supports_spring_args if s[0] != nid_to_del]
            for attr in ['supports_spring_x', 'supports_spring_y', 'supports_spring_z']:
                if hasattr(self.ss, attr):
                    filtered_list = [s for s in getattr(self.ss, attr) if s[0].id != nid_to_del]
                    setattr(self.ss, attr, filtered_list)
        self.apply_changes()

    def delete_loads(self):
        rows = sorted(set(i.row() for i in self.loads_table.selectedIndexes()), reverse=True)
        to_del = {'Point': [], 'Moment': [], 'q-Load': []}
        
        for row in rows:
            load_type = self.loads_table.item(row, 0).text()
            # The UserRole now stores the dictionary key (node_id or el_id)
            key = self.loads_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            to_del[load_type].append(key)

        for key in to_del['Point']: self.ss.loads_point.pop(key, None)
        for key in to_del['Moment']: self.ss.loads_moment.pop(key, None)
        for key in to_del['q-Load']: self.ss.loads_q.pop(key, None)
        
        self.apply_changes()

class StructuralApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AnaStruct Desktop GUI - PyQt6 (Fixed Backend)")
        self.setGeometry(100, 100, 1200, 800)

        # Frame Management
        self.frames = {"Frame 1": SystemElements()}
        self.current_frame_name = "Frame 1"
        self.ss = self.frames[self.current_frame_name]
        
        # View State for Pan/Zoom
        self.press = None
        self.view_xlim = None
        self.view_ylim = None
        
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
        self.sidebar_selector.addItems(["Frames", "Geometry", "Loads & Supports", "Analysis", "Grid"])
        sidebar_layout.addWidget(QLabel("Select Section:"))
        sidebar_layout.addWidget(self.sidebar_selector)

        # Stacked widget to hold section content
        self.sidebar_stack = QStackedWidget()
        sidebar_layout.addWidget(self.sidebar_stack)

        # Connect dropdown to stack
        self.sidebar_selector.currentIndexChanged.connect(self.sidebar_stack.setCurrentIndex)
        self.sidebar_selector.currentTextChanged.connect(self.on_sidebar_changed)

        # --- SECTION 0: FRAMES ---
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

        # --- SECTION 1: GEOMETRY & BUILD ---
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
        self.geom_selector.addItems(["Manual", "Tower Grid", "Frame Grid", "Combined"])
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
        
        self.frame_ground_beam = QCheckBox("Add Ground Beam")
        self.frame_gb_height = QLineEdit("0.5")
        self.frame_gb_height.setEnabled(False)
        self.frame_ground_beam.toggled.connect(self.frame_gb_height.setEnabled)
        
        self.frame_q_loads = QLineEdit("-10")

        frame_btn = QPushButton("Generate Frame Grid")
        frame_btn.clicked.connect(self.build_frame_grid)
        
        frame_form.addRow("Bay Width:", self.frame_bay_w)
        frame_form.addRow("Bay Height:", self.frame_bay_h)
        frame_form.addRow("Number of Bays:", self.frame_n_bays)
        frame_form.addRow("Number of Floors:", self.frame_n_floors)
        frame_form.addRow("Foundation Support:", self.frame_sup_type)
        frame_form.addRow(self.frame_ground_beam)
        frame_form.addRow("GB Height from Found.:", self.frame_gb_height)
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

        geometry_layout.addWidget(self.geom_stack)
        geometry_layout.addStretch()
        self.sidebar_stack.addWidget(geometry_tab)

        # --- SECTION 2: LOADS & SUPPORTS ---
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
        assign_layout.addWidget(loads_group)
        assign_layout.addStretch()
        self.sidebar_stack.addWidget(assign_tab)

        # --- SECTION 3: ANALYSIS & TOOLS ---
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)

        # Solver Controls
        solve_btn = QPushButton("SOLVE SYSTEM")
        solve_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        solve_btn.clicked.connect(self.solve_system)
        analysis_layout.addWidget(solve_btn)

        # Visualization Controls (Moved from bottom of canvas)
        viz_group = QGroupBox("Visualization Results")
        viz_form = QFormLayout()
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Structure", "Displacement", "Axial Force", "Bending Moment", "Grid Plan"])
        self.view_mode.currentTextChanged.connect(self.update_plot)
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(1, 100)
        self.scale_slider.setValue(10)
        self.scale_slider.valueChanged.connect(self.update_plot)

        self.show_grid = QCheckBox("Show Grid")
        self.show_grid.setChecked(True)
        self.show_grid.stateChanged.connect(self.update_plot)

        self.show_ticks = QCheckBox("Show Ticks & Labels")
        self.show_ticks.setChecked(True)
        self.show_ticks.stateChanged.connect(self.update_plot)

        reset_view_btn = QPushButton("Reset View (Fit)")
        reset_view_btn.clicked.connect(self.reset_view)

        viz_form.addRow("View Mode:", self.view_mode)
        viz_form.addRow("Scale Factor:", self.scale_slider)
        viz_form.addRow(self.show_grid)
        viz_form.addRow(self.show_ticks)
        viz_form.addRow(reset_view_btn)
        viz_group.setLayout(viz_form)
        analysis_layout.addWidget(viz_group)

        # Element Manager
        mgr_btn = QPushButton("Element Manager")
        mgr_btn.clicked.connect(self.open_element_manager)
        analysis_layout.addWidget(mgr_btn)

        reset_btn = QPushButton("Reset Structure")
        reset_btn.clicked.connect(self.reset_system)
        analysis_layout.addWidget(reset_btn)
        
        analysis_layout.addStretch()
        self.sidebar_stack.addWidget(analysis_tab)

        # --- SECTION 4: GRID MANAGER ---
        grid_tab = QWidget()
        grid_layout = QVBoxLayout(grid_tab)
        
        grid_settings = QGroupBox("Grid Spacings")
        grid_settings_form = QFormLayout()
        self.grid_x_input = QLineEdit("5, 5, 5")
        self.grid_y_input = QLineEdit("6, 6")
        self.grid_x_input.textChanged.connect(self.update_plot)
        self.grid_y_input.textChanged.connect(self.update_plot)
        grid_settings_form.addRow("X Spacings (1,2,3...):", self.grid_x_input)
        grid_settings_form.addRow("Y Spacings (A,B,C...):", self.grid_y_input)
        grid_settings.setLayout(grid_settings_form)
        grid_layout.addWidget(grid_settings)
        
        grid_assign_group = QGroupBox("Frame Assignments")
        grid_assign_layout = QVBoxLayout()
        self.grid_table = QTableWidget(0, 3)
        self.grid_table.setHorizontalHeaderLabels(["Grid Line", "Frame", "Offset"])
        self.grid_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.grid_table.itemChanged.connect(self.update_plot)
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

        sidebar_scroll.setWidget(sidebar_widget)
        layout.addWidget(sidebar_scroll)

        # --- CENTRAL CANVAS (Visualization) ---
        viz_layout = QVBoxLayout()
        # Create figure managed by pyplot
        self.figure, self.ax = plt.subplots()
        # Use the canvas that pyplot created to maintain the manager link
        self.canvas = self.figure.canvas
        viz_layout.addWidget(self.canvas)

        # Connect Pan/Zoom events
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        layout.addLayout(viz_layout, stretch=1)

    # --- LOGIC METHODS ---

    def on_sidebar_changed(self, text):
        if text == "Grid":
            self.sync_grid_frame_combos()

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
        self.grid_table.insertRow(row)
        self.grid_table.setItem(row, 0, QTableWidgetItem("A"))
        
        combo = QComboBox()
        combo.addItems(list(self.frames.keys()))
        combo.currentTextChanged.connect(self.update_plot)
        self.grid_table.setCellWidget(row, 1, combo)
        
        self.grid_table.setItem(row, 2, QTableWidgetItem("0"))
        self.grid_table.blockSignals(False)
        self.update_plot()

    def delete_grid_assignment(self):
        rows = sorted(set(i.row() for i in self.grid_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.grid_table.removeRow(row)
        self.update_plot()

    def add_frame(self):
        name, ok = QInputDialog.getText(self, "New Frame", "Enter frame name:")
        if ok and name:
            if name in self.frames:
                QMessageBox.warning(self, "Error", "Frame name already exists.")
                return
            self.frames[name] = SystemElements()
            self.frame_list.addItem(name)
            self.frame_list.setCurrentItem(self.frame_list.findItems(name, Qt.MatchFlag.MatchExactly)[0])

    def switch_frame(self):
        selected = self.frame_list.selectedItems()
        if not selected: return
        self.current_frame_name = selected[0].text()
        self.ss = self.frames[self.current_frame_name]
        self.reset_view() # Auto-fit when switching

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

    def duplicate_frame(self):
        curr_item = self.frame_list.currentItem()
        if not curr_item: return
        old_name = curr_item.text()
        new_name = f"{old_name} (Copy)"
        
        state = self.get_ss_state(self.frames[old_name])
        new_ss = SystemElements()
        self.apply_ss_state(new_ss, state)
        
        self.frames[new_name] = new_ss
        self.frame_list.addItem(new_name)
        self.frame_list.setCurrentItem(self.frame_list.findItems(new_name, Qt.MatchFlag.MatchExactly)[0])

    def get_ss_state(self, ss):
        elements = []
        for el in ss.element_map.values():
            n1, n2 = ss.node_map[el.node_id1].vertex, ss.node_map[el.node_id2].vertex
            elements.append({'loc': [[n1.x, n1.y], [n2.x, n2.y]], 'EA': el.EA, 'EI': el.EI})
        fixed = [n.id for n in ss.supports_fixed]
        hinged = [n.id for n in ss.supports_hinged]
        rolls = []
        if hasattr(ss, 'supports_roll'):
            for i, node in enumerate(ss.supports_roll):
                rolls.append((node.id, ss.supports_roll_direction[i]))
        springs = []
        if hasattr(ss, 'supports_spring_args'):
            springs = [s for s in ss.supports_spring_args]
        return {
            'elements': elements, 'fixed': fixed, 'hinged': hinged, 'rolls': rolls, 'springs': springs,
            'p_loads': ss.loads_point.copy(), 'm_loads': ss.loads_moment.copy(), 'q_loads': ss.loads_q.copy()
        }

    def apply_ss_state(self, ss, state):
        for e in state['elements']: ss.add_element(location=e['loc'], EA=e['EA'], EI=e['EI'])
        for nid in state['fixed']: 
            if nid in ss.node_map: ss.add_support_fixed(node_id=nid)
        for nid in state['hinged']: 
            if nid in ss.node_map: ss.add_support_hinged(node_id=nid)
        for nid, d in state['rolls']: 
            if nid in ss.node_map: ss.add_support_roll(node_id=nid, direction=d)
        for s in state['springs']:
            if s[0] in ss.node_map: ss.add_support_spring(node_id=s[0], translation=s[1], k=s[2], roll=s[3])
        for nid, data in state['p_loads'].items():
            if nid in ss.node_map:
                fx, fz = (data[0], data[1]) if isinstance(data, (list, tuple)) else (data.get('Fx', 0), data.get('Fz', 0))
                ss.point_load(node_id=nid, Fx=fx, Fz=fz)
        for nid, data in state['m_loads'].items():
            if nid in ss.node_map:
                ty = data[0] if isinstance(data, (list, tuple)) else (data.get('Ty', 0) if isinstance(data, dict) else data)
                ss.moment_load(node_id=nid, Ty=ty)
        for eid, data in state['q_loads'].items():
            if eid in ss.element_map:
                q, d = (data[0], data[1]) if isinstance(data, (list, tuple)) else (data.get('q', 0), data.get('direction', ''))
                ss.q_load(q=q, element_id=eid, direction=d)

    # --- PAN & ZOOM HANDLERS ---
    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        base_scale = 1.2
        scale_factor = 1 / base_scale if event.button == 'up' else base_scale
        x_min, x_max = self.ax.get_xlim(); y_min, y_max = self.ax.get_ylim()
        new_width, new_height = (x_max - x_min) * scale_factor, (y_max - y_min) * scale_factor
        rel_x, rel_y = (event.xdata - x_min) / (x_max - x_min), (event.ydata - y_min) / (y_max - y_min)
        self.view_xlim = [event.xdata - rel_x * new_width, event.xdata + (1 - rel_x) * new_width]
        self.view_ylim = [event.ydata - rel_y * new_height, event.ydata + (1 - rel_y) * new_height]
        self.ax.set_xlim(self.view_xlim); self.ax.set_ylim(self.view_ylim)
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.button == 2: 
            self.press = event.x, event.y, self.ax.get_xlim(), self.ax.get_ylim()

    def on_release(self, event): self.press = None

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax or event.x is None or event.y is None: return
        start_x, start_y, x_lim, y_lim = self.press
        
        dx_pix = event.x - start_x
        dy_pix = event.y - start_y
        
        width_pix = self.ax.bbox.width
        height_pix = self.ax.bbox.height
        
        dx_data = dx_pix * (x_lim[1] - x_lim[0]) / width_pix
        dy_data = dy_pix * (y_lim[1] - y_lim[0]) / height_pix
        
        self.view_xlim = [x_lim[0] - dx_data, x_lim[1] - dx_data]
        self.view_ylim = [y_lim[0] - dy_data, y_lim[1] - dy_data]
        self.ax.set_xlim(self.view_xlim); self.ax.set_ylim(self.view_ylim)
        self.canvas.draw_idle()

    def reset_view(self):
        self.view_xlim = None
        self.view_ylim = None
        self.update_plot()

    def get_material(self):
        return float(self.ea_input.text()), float(self.ei_input.text())

    def reset_system(self):
        self.ss = SystemElements()
        self.frames[self.current_frame_name] = self.ss
        self.update_plot()

    def add_manual_element(self, element_type='frame'):
        try:
            ea, ei = self.get_material()
            p1 = [float(self.x1.text()), float(self.y1.text())]
            p2 = [float(self.x2.text()), float(self.y2.text())]
            
            if element_type == 'truss':
                self.ss.add_element(location=[p1, p2], EA=ea)
            else:
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
            self.frames[self.current_frame_name] = self.ss
            width = float(self.tower_width.text())
            span = float(self.tower_span.text())
            q_horiz = float(self.tower_q_horiz.text())
            k = float(self.tower_k_stiffness.text())
            ea, ei = self.get_material()
            
            y = np.arange(1, 10) * np.pi 
            x = np.cos(y) * width * 0.5
            x -= x.min()

            for length in [0, span]:
                x_left_column = np.ones(y[::2].shape) * x.min() + length
                x_right_column = np.ones(y[::2].shape[0] + 1) * x.max() + length

                # add triangles
                self.ss.add_element_grid(x + length, y, element_type='truss', EA=ea)
                # add vertical elements
                self.ss.add_element_grid(x_left_column, y[::2], element_type='truss', EA=ea)
                self.ss.add_element_grid(x_right_column, np.r_[y[0], y[1::2], y[-1]], element_type='truss', EA=ea)

                # Add spring supports at the base of each tower
                nid_left = self.ss.find_node_id(vertex=[x_left_column[0], y[0]])
                if nid_left:
                    self.ss.add_support_spring(node_id=nid_left, translation=2, k=k)
                
                nid_right = self.ss.find_node_id(vertex=[x_right_column[0], y[0]])
                if nid_right:
                    self.ss.add_support_spring(node_id=nid_right, translation=2, k=k)
            
            self.ss.add_element_grid([0, width, span, span + width], np.ones(4) * y.max(), EI=ei)

            # Add stability elements at the bottom.
            self.ss.add_truss_element(location=[[0, y.min()], [width, y.min()]], EA=ea)
            self.ss.add_truss_element(location=[[span, y.min()], [span + width, y.min()]], EA=ea)

            # Apply horizontal UDL to vertical elements (e.g., wind load)
            if q_horiz != 0:
                for el in self.ss.element_map.values():
                    # apply wind load on elements that are vertical
                    if np.isclose(np.sin(el.angle), 1):
                        self.ss.q_load(q=q_horiz, element_id=el.id, direction='x')

            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_frame_grid(self):
        """Generates a multi-bay, multi-floor frame grid."""
        try:
            self.ss = SystemElements()
            self.frames[self.current_frame_name] = self.ss
            ea, ei = self.get_material()
            
            w = float(self.frame_bay_w.text())
            h = float(self.frame_bay_h.text())
            n_bays = int(self.frame_n_bays.text())
            n_floors = int(self.frame_n_floors.text())
            sup_type = self.frame_sup_type.currentText()

            gb_enabled = self.frame_ground_beam.isChecked()
            gb_h = float(self.frame_gb_height.text()) if gb_enabled else 0
            
            try:
                q_vals = [float(x.strip()) for x in self.frame_q_loads.text().split(',')]
            except ValueError:
                q_vals = [-10.0]

            # Loop through floors
            for floor in range(n_floors):
                y_bot = floor * h
                y_top = (floor + 1) * h
                
                # Columns
                for bay in range(n_bays + 1):
                    x = bay * w
                    
                    if floor == 0 and gb_enabled:
                        # Split first floor column for ground beam
                        self.ss.add_element(location=[[x, 0], [x, gb_h]], EA=ea, EI=ei)
                        self.ss.add_element(location=[[x, gb_h], [x, y_top]], EA=ea, EI=ei)
                    else:
                        self.ss.add_element(location=[[x, y_bot], [x, y_top]], EA=ea, EI=ei)
                    
                    # Foundation supports at the very bottom
                    if floor == 0:
                        nid = self.ss.find_node_id(vertex=[x, 0])
                        if nid:
                            if sup_type == "Hinged":
                                self.ss.add_support_hinged(node_id=nid)
                            elif sup_type == "Fixed":
                                self.ss.add_support_fixed(node_id=nid)
                
                # Beams at y_top
                q_idx = floor + (1 if gb_enabled else 0)
                q = q_vals[q_idx] if q_idx < len(q_vals) else q_vals[-1]
                
                for bay in range(n_bays):
                    x_left = bay * w
                    x_right = (bay + 1) * w
                    eid = self.ss.add_element(location=[[x_left, y_top], [x_right, y_top]], EA=ea, EI=ei)
                    if q != 0:
                        self.ss.q_load(q=q, element_id=eid, direction='y')

            # Add Ground Beams at gb_h
            if gb_enabled:
                q = q_vals[0]
                for bay in range(n_bays):
                    x_left = bay * w
                    x_right = (bay + 1) * w
                    eid = self.ss.add_element(location=[[x_left, gb_h], [x_right, gb_h]], EA=ea, EI=ei)
                    if q != 0:
                        self.ss.q_load(q=q, element_id=eid, direction='y')

            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def build_combined_structure(self):
        """Generates a 2-story frame with a truss roof."""
        try:
            self.ss = SystemElements()
            self.frames[self.current_frame_name] = self.ss
            ea, ei = self.get_material()
            
            w = float(self.comb_width.text())
            h = float(self.comb_h_story.text())
            hr = float(self.comb_h_roof.text())
            q_floor = float(self.comb_q_floor.text())
            q_roof = float(self.comb_q_roof.text())

            # 1. Frame Structure (2 stories)
            # Columns
            self.ss.add_element(location=[[0, 0], [0, h]], EA=ea, EI=ei)
            self.ss.add_element(location=[[w, 0], [w, h]], EA=ea, EI=ei)
            self.ss.add_element(location=[[0, h], [0, 2*h]], EA=ea, EI=ei)
            self.ss.add_element(location=[[w, h], [w, 2*h]], EA=ea, EI=ei)
            
            # Beams
            b1 = self.ss.add_element(location=[[0, h], [w, h]], EA=ea, EI=ei)
            b2 = self.ss.add_element(location=[[0, 2*h], [w, 2*h]], EA=ea, EI=ei)
            
            # Supports
            n1 = self.ss.find_node_id(vertex=[0, 0])
            n2 = self.ss.find_node_id(vertex=[w, 0])
            if n1: self.ss.add_support_fixed(node_id=n1)
            if n2: self.ss.add_support_fixed(node_id=n2)
            
            # 2. Truss Roof
            # Rafters
            r1 = self.ss.add_element(location=[[0, 2*h], [w/2, 2*h + hr]], element_type='truss', EA=ea)
            r2 = self.ss.add_element(location=[[w, 2*h], [w/2, 2*h + hr]], element_type='truss', EA=ea)
            
            # 3. Loads
            if q_floor != 0:
                self.ss.q_load(q=q_floor, element_id=b1, direction='y')
                self.ss.q_load(q=q_floor, element_id=b2, direction='y')
            
            if q_roof != 0:
                self.ss.q_load(q=q_roof, element_id=r1, direction='y')
                self.ss.q_load(q=q_roof, element_id=r2, direction='y')

            self.update_plot()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def rebuild_system(self, node_coords=None, element_props=None):
        """
        Rebuilds the SystemElements object from the current state of element_map, 
        supports, and loads. This ensures all internal cached values (stiffness 
        matrices, lengths, angles) are correctly recomputed.
        """
        # 1. Capture current state
        elements = []
        for el_id in sorted(self.ss.element_map.keys()):
            el = self.ss.element_map[el_id]
            
            # Get coordinates, prioritizing node_coords override from Element Manager
            if node_coords and el.node_id1 in node_coords:
                p1 = node_coords[el.node_id1]
            else:
                n1 = self.ss.node_map[el.node_id1].vertex
                p1 = [n1.x, n1.y]
                
            if node_coords and el.node_id2 in node_coords:
                p2 = node_coords[el.node_id2]
            else:
                n2 = self.ss.node_map[el.node_id2].vertex
                p2 = [n2.x, n2.y]

            # Get EA/EI, prioritizing element_props override
            ea = element_props[el_id]['EA'] if element_props and el_id in element_props else el.EA
            ei = element_props[el_id]['EI'] if element_props and el_id in element_props else el.EI

            elements.append({
                'location': [p1, p2], 
                'EA': ea, 
                'EI': ei
            })
            
        fixed = [n.id for n in self.ss.supports_fixed]
        hinged = [n.id for n in self.ss.supports_hinged]
        rolls = []
        if hasattr(self.ss, 'supports_roll'):
            for i, node in enumerate(self.ss.supports_roll):
                rolls.append((node.id, self.ss.supports_roll_direction[i]))
        springs = []
        if hasattr(self.ss, 'supports_spring_args'):
            for s in self.ss.supports_spring_args:
                springs.append(s)

        p_loads = self.ss.loads_point.copy()
        m_loads = self.ss.loads_moment.copy()
        q_loads = self.ss.loads_q.copy()

        # 2. Reset the system
        self.ss = SystemElements()
        self.frames[self.current_frame_name] = self.ss
        
        # 3. Re-add elements (recreates nodes and internal geometry)
        for e in elements:
            self.ss.add_element(location=e['location'], EA=e['EA'], EI=e['EI'])
            
        # 4. Re-apply supports (only if node still exists)
        for nid in fixed: 
            if nid in self.ss.node_map: self.ss.add_support_fixed(node_id=nid)
        for nid in hinged: 
            if nid in self.ss.node_map: self.ss.add_support_hinged(node_id=nid)
        for nid, d in rolls: 
            if nid in self.ss.node_map: self.ss.add_support_roll(node_id=nid, direction=d)
        for s in springs:
            if s[0] in self.ss.node_map:
                self.ss.add_support_spring(node_id=s[0], translation=s[1], k=s[2], roll=s[3])
            
        # 5. Re-apply loads (only if node/element still exists)
        for nid, data in p_loads.items():
            if nid in self.ss.node_map:
                if isinstance(data, (list, tuple)): fx, fz = data[0], data[1]
                elif isinstance(data, dict): fx, fz = data.get('Fx', 0), data.get('Fz', 0)
                else: fx, fz = 0, 0
                self.ss.point_load(node_id=nid, Fx=fx, Fz=fz)
        for nid, data in m_loads.items():
            if nid in self.ss.node_map:
                if isinstance(data, (list, tuple)): ty = data[0]
                elif isinstance(data, dict): ty = data.get('Ty', 0)
                else: ty = data
                self.ss.moment_load(node_id=nid, Ty=ty)
        for eid, data in q_loads.items():
            if eid in self.ss.element_map:
                if isinstance(data, (list, tuple)): q, d = data[0], data[1]
                elif isinstance(data, dict): q, d = data.get('q', 0), data.get('direction', '')
                else: q, d = 0, ''
                self.ss.q_load(q=q, element_id=eid, direction=d)

        # Reset view mode to Structure to avoid plotting errors on the new system
        if self.view_mode.currentText() == "Structure":
            self.update_plot()
        else:
            self.view_mode.setCurrentText("Structure")

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

    def open_element_manager(self):
        dlg = ElementManagerDialog(self)
        dlg.exec()

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

        # Get current figure size to maintain aspect ratio logic in anastruct
        current_figsize = self.figure.get_size_inches()

        mode = self.view_mode.currentText()
        factor = self.scale_slider.value()

        def prepare_plotter():
            # Ensure anastruct uses our existing axes and figure
            self.ss.plotter.axes = [self.ax]
            self.ss.plotter.fig = self.figure
            self.ss.plotter.figure = self.figure

        try:
            if mode == "Structure":
                prepare_plotter()
                self.ss.plotter.plot_structure(
                    figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                )
            elif mode == "Displacement":
                prepare_plotter()
                self.ss.plotter.displacements(
                    factor=factor, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Axial Force":
                prepare_plotter()
                self.ss.plotter.axial_force(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Bending Moment":
                prepare_plotter()
                self.ss.plotter.bending_moment(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Grid Plan":
                # Custom drawing for Top View Grid
                self.ax.set_axis_off()
                
                # 1. Parse spacings
                try:
                    sx = [float(s.strip()) for s in self.grid_x_input.text().split(',') if s.strip()]
                    sy = [float(s.strip()) for s in self.grid_y_input.text().split(',') if s.strip()]
                except ValueError:
                    sx, sy = [], []
                    
                gx = [0.0] + list(np.cumsum(sx))
                gy = [0.0] + list(np.cumsum(sy))
                
                # 2. Draw Grid Lines (Dotted)
                for x in gx:
                    self.ax.axvline(x, color='gray', linestyle=':', linewidth=1.0)
                for y in gy:
                    self.ax.axhline(y, color='gray', linestyle=':', linewidth=1.0)
                    
                # 3. Labels
                alphabet = string.ascii_uppercase
                for i, x in enumerate(gx):
                    self.ax.text(x, gy[0] - 0.5, str(i+1), ha='center', va='top', color='white', fontweight='bold')
                for i, y in enumerate(gy):
                    label = alphabet[i] if i < len(alphabet) else f"Z{i}"
                    self.ax.text(gx[0] - 0.5, y, label, ha='right', va='center', color='white', fontweight='bold')
                    
                # 4. Draw Frames
                for row in range(self.grid_table.rowCount()):
                    line_item = self.grid_table.item(row, 0)
                    offset_item = self.grid_table.item(row, 2)
                    if not line_item or not offset_item: continue
                    
                    line_label = line_item.text().upper()
                    frame_name = self.grid_table.cellWidget(row, 1).currentText()
                    try:
                        offset = float(offset_item.text())
                    except ValueError: offset = 0.0
                    
                    if frame_name not in self.frames: continue
                    f_ss = self.frames[frame_name]
                    if not f_ss.element_map: continue
                    
                    nodes_x = [n.vertex.x for n in f_ss.node_map.values()]
                    min_fx, max_fx = min(nodes_x), max(nodes_x)
                    min_fy = min(n.vertex.y for n in f_ss.node_map.values())
                    base_nodes_x = [n.vertex.x for n in f_ss.node_map.values() if np.isclose(n.vertex.y, min_fy)]
                    
                    if line_label.isdigit(): # Vertical line (1, 2, 3...)
                        idx = int(line_label) - 1
                        if idx < len(gx):
                            pos_x = gx[idx]
                            self.ax.plot([pos_x, pos_x], [gy[0] + offset + min_fx, gy[0] + offset + max_fx], color='cyan', linewidth=2)
                            for bx in base_nodes_x: self.ax.plot(pos_x, gy[0] + offset + bx, 's', color='red', markersize=6)
                    else: # Horizontal line (A, B, C...)
                        idx = alphabet.find(line_label)
                        if idx != -1 and idx < len(gy):
                            pos_y = gy[idx]
                            self.ax.plot([gx[0] + offset + min_fx, gx[0] + offset + max_fx], [pos_y, pos_y], color='cyan', linewidth=2)
                            for bx in base_nodes_x: self.ax.plot(gx[0] + offset + bx, pos_y, 's', color='red', markersize=6)

                self.ax.set_aspect('equal', adjustable='datalim')
                self.ax.autoscale_view()

        except Exception as e:
            print(f"Plotting error: {type(e).__name__}: {e}")
            # Fallback to structure view and update UI if results aren't available
            if mode != "Structure":
                self.view_mode.blockSignals(True)
                self.view_mode.setCurrentText("Structure")
                self.view_mode.blockSignals(False)
                try:
                    prepare_plotter()
                    self.ss.plotter.plot_structure(
                        figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                    )
                except Exception:
                    pass
        
        # Apply grid and tick settings
        # Control axis visibility (ticks, labels, spines)
        self.ax.set_axis_on() if self.show_ticks.isChecked() else self.ax.set_axis_off()

        # Control grid visibility independently
        self.ax.grid(self.show_grid.isChecked())

        # Restore view state
        if self.view_xlim:
            self.ax.set_xlim(self.view_xlim)
            self.ax.set_ylim(self.view_ylim)
        else:
            self.ax.set_aspect('equal', adjustable='box')

        # Refresh the canvas
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StructuralApp()
    window.show()
    sys.exit(app.exec())