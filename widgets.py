import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt

class ElementManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ss = parent.ss
        self.layout = QVBoxLayout(self)

        # Dropdown for sub-section selection
        self.sub_selector = QComboBox()
        self.sub_selector.addItems(["Elements", "Nodes", "Supports", "Loads"])
        self.layout.addWidget(QLabel("Manage Section:"))
        self.layout.addWidget(self.sub_selector)
        
        self.sub_stack = QStackedWidget()
        self.layout.addWidget(self.sub_stack)
        self.sub_selector.currentIndexChanged.connect(self.sub_stack.setCurrentIndex)
        
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
        self.sub_stack.addWidget(self.elements_tab)
        
        # Nodes Tab
        self.nodes_tab = QWidget()
        self.nodes_layout = QVBoxLayout(self.nodes_tab)
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(3)
        self.nodes_table.setHorizontalHeaderLabels(["ID", "X", "Y"])
        self.nodes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.nodes_layout.addWidget(self.nodes_table)
        self.sub_stack.addWidget(self.nodes_tab)
        
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
        self.sub_stack.addWidget(self.supports_tab)

        # Loads Container Widget
        self.loads_container_tab = QWidget()
        self.loads_container_layout = QVBoxLayout(self.loads_container_tab)

        self.load_type_selector = QComboBox()
        self.load_type_selector.addItems(["Point Loads", "Moments", "q-Loads"])
        self.loads_container_layout.addWidget(QLabel("Load Type:"))
        self.loads_container_layout.addWidget(self.load_type_selector)
        
        self.load_stack = QStackedWidget()
        self.load_type_selector.currentIndexChanged.connect(self.load_stack.setCurrentIndex)
        self.loads_container_layout.addWidget(self.load_stack)

        # Point Loads Sub-Tab
        self.p_loads_sub_tab = QWidget()
        self.p_loads_layout = QVBoxLayout(self.p_loads_sub_tab)
        self.p_loads_table = QTableWidget(0, 3)
        self.p_loads_table.setHorizontalHeaderLabels(["Node ID", "Fx (kN)", "Fz (kN)"])
        self.p_loads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.p_loads_layout.addWidget(self.p_loads_table)
        self.del_p_load_btn = QPushButton("Delete Selected Point Loads")
        self.del_p_load_btn.clicked.connect(self.delete_loads)
        self.p_loads_layout.addWidget(self.del_p_load_btn)
        self.load_stack.addWidget(self.p_loads_sub_tab)

        # Moments Sub-Tab
        self.m_loads_sub_tab = QWidget()
        self.m_loads_layout = QVBoxLayout(self.m_loads_sub_tab)
        self.m_loads_table = QTableWidget(0, 2)
        self.m_loads_table.setHorizontalHeaderLabels(["Node ID", "Moment (kNm)"])
        self.m_loads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.m_loads_layout.addWidget(self.m_loads_table)
        self.del_m_load_btn = QPushButton("Delete Selected Moments")
        self.del_m_load_btn.clicked.connect(self.delete_loads)
        self.m_loads_layout.addWidget(self.del_m_load_btn)
        self.load_stack.addWidget(self.m_loads_sub_tab)

        # q-Loads Sub-Tab
        self.q_loads_sub_tab = QWidget()
        self.q_loads_layout = QVBoxLayout(self.q_loads_sub_tab)
        self.q_loads_table = QTableWidget(0, 6)
        self.q_loads_table.setHorizontalHeaderLabels(["Element ID", "q Start", "q End", "qp Start", "qp End", "Direction"])
        self.q_loads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.q_loads_layout.addWidget(self.q_loads_table)
        self.del_q_load_btn = QPushButton("Delete Selected q-Loads")
        self.del_q_load_btn.clicked.connect(self.delete_loads)
        self.q_loads_layout.addWidget(self.del_q_load_btn)
        self.load_stack.addWidget(self.q_loads_sub_tab)

        self.sub_stack.addWidget(self.loads_container_tab) # Add the new container to main sub_stack

        # Connect change signals
        self.elements_table.itemChanged.connect(lambda _: self.apply_changes())
        self.nodes_table.itemChanged.connect(lambda _: self.apply_changes())
        self.p_loads_table.itemChanged.connect(lambda _: self.apply_changes())
        self.m_loads_table.itemChanged.connect(lambda _: self.apply_changes())
        self.q_loads_table.itemChanged.connect(lambda _: self.apply_changes())

        self.refresh_data()

    def refresh_data(self):
        model = self.parent_app.frame_templates[self.parent_app.current_template_name]
        self.ss = model.system
        
        self.block_signals(True)
        
        # Elements
        self.elements_table.setRowCount(0)
        for i, e in enumerate(model.elements):
            row = self.elements_table.rowCount()
            self.elements_table.insertRow(row)
            item_id = QTableWidgetItem(str(i + 1))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.elements_table.setItem(row, 0, item_id)
            
            nid1 = self.ss.find_node_id(vertex=e['loc'][0])
            nid2 = self.ss.find_node_id(vertex=e['loc'][1])
            self.elements_table.setItem(row, 1, QTableWidgetItem(str(nid1 or "?")))
            self.elements_table.setItem(row, 2, QTableWidgetItem(str(nid2 or "?")))
            self.elements_table.setItem(row, 3, QTableWidgetItem(str(e['EA'])))
            self.elements_table.setItem(row, 4, QTableWidgetItem(str(e['EI'])))

        # Nodes
        self.nodes_table.setRowCount(0)
        for n_id in sorted(self.ss.node_map.keys()):
            node = self.ss.node_map[n_id]
            row = self.nodes_table.rowCount()
            self.nodes_table.insertRow(row)
            item_id = QTableWidgetItem(str(n_id))
            item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.nodes_table.setItem(row, 0, item_id)
            self.nodes_table.setItem(row, 1, QTableWidgetItem(str(node.vertex.x)))
            self.nodes_table.setItem(row, 2, QTableWidgetItem(str(node.vertex.y)))

        # Supports
        self.supports_table.setRowCount(0)
        for s in model.supports:
            nid = self.ss.find_node_id(vertex=s['loc'])
            stype = s['type'].capitalize()
            if stype == "Roll": stype += f" (dir={s['args'].get('direction', 2)})"
            elif stype == "Spring": stype += f" (k={s['args'].get('k', 5000)})"
            self._add_support_row(nid, stype)

        # Point Loads
        self.p_loads_table.setRowCount(0)
        for p in model.point_loads:
            nid = self.ss.find_node_id(vertex=p['loc'])
            row = self.p_loads_table.rowCount()
            self.p_loads_table.insertRow(row)
            item = QTableWidgetItem(str(nid))
            item.setData(Qt.ItemDataRole.UserRole, nid)
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.p_loads_table.setItem(row, 0, item)
            self.p_loads_table.setItem(row, 1, QTableWidgetItem(str(p['Fx'])))
            self.p_loads_table.setItem(row, 2, QTableWidgetItem(str(p['Fz'])))
            
        # Moment Loads
        self.m_loads_table.setRowCount(0)
        for m in model.moment_loads:
            nid = self.ss.find_node_id(vertex=m['loc'])
            row = self.m_loads_table.rowCount()
            self.m_loads_table.insertRow(row)
            item = QTableWidgetItem(str(nid))
            item.setData(Qt.ItemDataRole.UserRole, nid)
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.m_loads_table.setItem(row, 0, item)
            self.m_loads_table.setItem(row, 1, QTableWidgetItem(str(m['Ty'])))
            
        # q-Loads
        self.q_loads_table.setRowCount(0)
        for q in model.q_loads:
            el_id = q['element_idx'] + 1
            row = self.q_loads_table.rowCount()
            self.q_loads_table.insertRow(row)
            item = QTableWidgetItem(str(el_id))
            item.setData(Qt.ItemDataRole.UserRole, el_id)
            item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.q_loads_table.setItem(row, 0, item)
            
            q_val = q.get('q', 0)
            if isinstance(q_val, (list, tuple, np.ndarray)):
                q_start, q_end = q_val[0], q_val[1] if len(q_val) > 1 else q_val[0]
            else:
                q_start = q_end = q_val
                
            qp_val = q.get('qp', 0)
            if isinstance(qp_val, (list, tuple, np.ndarray)):
                qp_start, qp_end = qp_val[0], qp_val[1] if len(qp_val) > 1 else qp_val[0]
            else:
                qp_start = qp_end = qp_val
            
            direction = q.get('dir', 'element')

            # Clean floating point noise for display
            def fmt(v): return str(v) if abs(v) > 1e-12 else "0.0"
            self.q_loads_table.setItem(row, 1, QTableWidgetItem(fmt(q_start)))
            self.q_loads_table.setItem(row, 2, QTableWidgetItem(fmt(q_end)))
            self.q_loads_table.setItem(row, 3, QTableWidgetItem(fmt(qp_start)))
            self.q_loads_table.setItem(row, 4, QTableWidgetItem(fmt(qp_end)))
            
            combo = QComboBox()
            combo.addItems(["y", "x", "element", "parallel"])
            combo.blockSignals(True)
            combo.setCurrentText(str(direction))
            combo.blockSignals(False)
            combo.currentTextChanged.connect(lambda _: self.apply_changes())
            self.q_loads_table.setCellWidget(row, 5, combo)

        self.block_signals(False)

    def _add_support_row(self, nid, type_str):
        row = self.supports_table.rowCount()
        self.supports_table.insertRow(row)
        item_id = QTableWidgetItem(str(nid))
        item_id.setFlags(item_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self.supports_table.setItem(row, 0, item_id)
        
        combo = QComboBox()
        combo.addItems(["Fixed", "Hinged", "Roll", "Spring"])
        if "Fixed" in type_str: combo.setCurrentText("Fixed")
        elif "Hinged" in type_str: combo.setCurrentText("Hinged")
        elif "Roll" in type_str: combo.setCurrentText("Roll")
        elif "Spring" in type_str: combo.setCurrentText("Spring")
        combo.currentTextChanged.connect(lambda _: self.apply_changes())
        self.supports_table.setCellWidget(row, 1, combo)

    def block_signals(self, block):
        self.elements_table.blockSignals(block)
        self.nodes_table.blockSignals(block)
        self.p_loads_table.blockSignals(block)
        self.m_loads_table.blockSignals(block)
        self.load_type_selector.blockSignals(block)
        self.q_loads_table.blockSignals(block)

    def apply_changes(self, refresh=False):
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

        # Extract supports and loads overrides
        supports_info = {}
        for row in range(self.supports_table.rowCount()):
            try:
                nid = int(self.supports_table.item(row, 0).text())
                stype = self.supports_table.cellWidget(row, 1).currentText()
                supports_info[nid] = stype
            except (ValueError, AttributeError): continue

        loads_info = []
        # Point Loads
        for row in range(self.p_loads_table.rowCount()):
            try:
                nid = int(self.p_loads_table.item(row, 0).text())
                fx = float(self.p_loads_table.item(row, 1).text())
                fz = float(self.p_loads_table.item(row, 2).text())
                loads_info.append({'type': 'Point', 'id': nid, 'v1': fx, 'v2': fz})
            except (ValueError, AttributeError): continue
        
        # Moments
        for row in range(self.m_loads_table.rowCount()):
            try:
                nid = int(self.m_loads_table.item(row, 0).text())
                ty = float(self.m_loads_table.item(row, 1).text())
                loads_info.append({'type': 'Moment', 'id': nid, 'v1': ty, 'v2': 0})
            except (ValueError, AttributeError): continue
            
        # q-Loads
        for row in range(self.q_loads_table.rowCount()):
            try:
                eid = int(self.q_loads_table.item(row, 0).text())
                q_start = float(self.q_loads_table.item(row, 1).text() or 0)
                q_end = float(self.q_loads_table.item(row, 2).text() or 0)
                qp_start = float(self.q_loads_table.item(row, 3).text() or 0)
                qp_end = float(self.q_loads_table.item(row, 4).text() or 0)
                direction = self.q_loads_table.cellWidget(row, 5).currentText()
                q_val = q_start if q_start == q_end else [q_start, q_end]
                qp_val = qp_start if qp_start == qp_end else [qp_start, qp_end]
                loads_info.append({'type': 'q-Load', 'id': eid, 'v1': q_val, 'v2': direction, 'v3': qp_val})
            except (ValueError, AttributeError): continue

        self.parent_app.rebuild_system(
            node_coords=node_coords, 
            element_props=element_props,
            supports_info=supports_info,
            loads_info=loads_info
        )
        if refresh:
            self.refresh_data()

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
        self.apply_changes(refresh=True)

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
        self.apply_changes(refresh=True)

    def delete_loads(self):
        # Determine which table is active
        load_type_idx = self.load_type_selector.currentIndex()
        # Indices: 0: Point Loads, 1: Moments, 2: q-Loads
        if load_type_idx == 0:
            table = self.p_loads_table
            ltype = 'Point'
        elif load_type_idx == 1:
            table = self.m_loads_table
            ltype = 'Moment'
        elif load_type_idx == 2:
            table = self.q_loads_table
            ltype = 'q-Load'
        else:
            return

        rows = sorted(set(i.row() for i in table.selectedIndexes()), reverse=True)
        for row in rows:
            key = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if ltype == 'Point': self.ss.loads_point.pop(key, None)
            elif ltype == 'Moment': self.ss.loads_moment.pop(key, None)
            elif ltype == 'q-Load': self.ss.loads_q.pop(key, None)
        
        self.apply_changes(refresh=True)