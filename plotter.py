import string
import numpy as np
import matplotlib.pyplot as plt

class StructuralPlotter:
    def __init__(self, main_window):
        self.main = main_window
        self.ax = self.main.ax
        self.figure = self.main.figure
        self.canvas = self.main.canvas
        
        # View State
        self.press = None
        self.view_xlim = None
        self.view_ylim = None

        # Connect Pan/Zoom events
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def update_plot(self):
        # Clear the axes for the new plot
        self.ax.clear()
        
        # Check if there are elements to plot
        if not self.main.ss.element_map:
            self.canvas.draw()
            return

        # Get current figure size to maintain aspect ratio logic in anastruct
        current_figsize = self.figure.get_size_inches()

        mode = self.main.view_mode.currentText()
        factor = self.main.scale_slider.value()

        # Update UI state
        self.main.floor_selector.setEnabled(mode == "Grid Plan")
        self.main.show_beam_marks.setEnabled(mode == "Grid Plan")

        def prepare_plotter():
            # Ensure anastruct uses our existing axes and figure
            self.main.ss.plotter.axes = [self.ax]
            self.main.ss.plotter.fig = self.figure
            self.main.ss.plotter.figure = self.figure
            self.ax.set_aspect('equal', adjustable='box')

        try:
            if mode == "Structure":
                prepare_plotter()
                self.main.ss.plotter.plot_structure(
                    figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                )
            elif mode == "Displacement":
                prepare_plotter()
                self.main.ss.plotter.displacements(
                    factor=factor, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Axial Force":
                prepare_plotter()
                self.main.ss.plotter.axial_force(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Shear Force":
                prepare_plotter()
                self.main.ss.plotter.shear_force(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Bending Moment":
                prepare_plotter()
                self.main.ss.plotter.bending_moment(
                    factor=None, figsize=current_figsize, verbosity=0, show=False, gridplot=True
                )
            elif mode == "Grid Plan":
                # Custom drawing for Top View Grid
                self.ax.set_axis_off()
                alphabet = string.ascii_uppercase
                
                # 1. Parse spacings
                try:
                    sx = [float(s.strip()) for s in self.main.grid_x_input.text().split(',') if s.strip()]
                    sy = [float(s.strip()) for s in self.main.grid_y_input.text().split(',') if s.strip()]
                except ValueError:
                    sx, sy = [], []
                    
                gx = [0.0] + list(np.cumsum(sx))
                gy = [0.0] + list(np.cumsum(sy))
                
                # 2. Draw Grid Lines (Dotted)
                if self.main.show_grid.isChecked():
                    for x in gx:
                        self.ax.axvline(x, color='gray', linestyle=':', linewidth=1.0)
                    for y in gy:
                        self.ax.axhline(y, color='gray', linestyle=':', linewidth=1.0)
                    
                # 2.5 Draw Slabs
                for name, data in self.main.slabs.items():
                    pts = []
                    for x_idx, y_idx in data['points']:
                        if x_idx < len(gx) and y_idx < len(gy):
                            pts.append([gx[x_idx], gy[y_idx]])
                    if pts:
                        poly = plt.Polygon(pts, closed=True, facecolor='orange', alpha=0.3, edgecolor='darkorange', linewidth=2)
                        self.ax.add_patch(poly)
                        cx, cy = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
                        self.ax.text(cx, cy, name, ha='center', va='center', color='darkred', fontweight='bold', fontsize=10)

                # 3. Labels
                if self.main.show_grid_labels.isChecked():
                    for i, x in enumerate(gx):
                        self.ax.text(x, gy[0] - 0.5, str(i+1), ha='center', va='top', color='black', fontweight='bold')
                    for i, y in enumerate(gy):
                        label = alphabet[i] if i < len(alphabet) else f"Z{i}"
                        self.ax.text(gx[0] - 0.5, y, label, ha='right', va='center', color='black', fontweight='bold')
                    
                # Extract selected height and next height
                try:
                    current_idx = self.main.floor_selector.currentIndex()
                    sel_text = self.main.floor_selector.currentText()
                    sel_height = float(sel_text.split('(')[1].split('m')[0])
                    
                    if current_idx < self.main.floor_selector.count() - 1:
                        next_text = self.main.floor_selector.itemText(current_idx + 1)
                        next_height = float(next_text.split('(')[1].split('m')[0])
                    else:
                        next_height = None
                except (IndexError, ValueError):
                    sel_height = 0.0
                    next_height = None

                # 4. Draw Frames
                for row in range(self.main.grid_table.rowCount()):
                    line_item = self.main.grid_table.item(row, 0)
                    offset_item = self.main.grid_table.item(row, 2)
                    if not line_item or not offset_item: continue
                    
                    line_label = line_item.text().upper()
                    frame_name = self.main.grid_table.cellWidget(row, 1).currentText()
                    try:
                        offset = float(offset_item.text())
                    except ValueError: offset = 0.0
                    
                    if frame_name not in self.main.frames: continue
                    f_model = self.main.frames[frame_name]
                    f_ss = f_model.system
                    if not f_ss.element_map: continue
                    
                    # Filter by height: show only frames that reach this height
                    max_frame_y = max(n.vertex.y for n in f_ss.node_map.values())
                    if max_frame_y < sel_height:
                        continue
                    
                    # Find beams at this height for marking
                    beams_at_h = []
                    for eid, el in f_ss.element_map.items():
                        n1 = f_ss.node_map[el.node_id1].vertex
                        n2 = f_ss.node_map[el.node_id2].vertex
                        if np.isclose(n1.y, sel_height) and np.isclose(n2.y, sel_height):
                            beams_at_h.append(el)

                    # Find columns starting at this height and going to next_height
                    columns_at_h = []
                    if next_height is not None:
                        for eid, el in f_ss.element_map.items():
                            n1 = f_ss.node_map[el.node_id1].vertex
                            n2 = f_ss.node_map[el.node_id2].vertex
                            h_coords = sorted([n1.y, n2.y])
                            if np.isclose(h_coords[0], sel_height) and np.isclose(h_coords[1], next_height):
                                if np.isclose(n1.x, n2.x):
                                    columns_at_h.append(el)
                    
                    if line_label.isdigit(): # Vertical line (1, 2, 3...)
                        idx = int(line_label) - 1
                        if idx < len(gx):
                            pos_x = gx[idx]
                            
                            # Plot beams
                            for el in beams_at_h:
                                n1 = f_ss.node_map[el.node_id1].vertex
                                n2 = f_ss.node_map[el.node_id2].vertex
                                self.ax.plot([pos_x, pos_x], [gy[0] + offset + n1.x, gy[0] + offset + n2.x], color='cyan', linewidth=3)
                                
                                if self.main.show_beam_marks.isChecked():
                                    mid_x = (n1.x + n2.x) / 2.0
                                    self.ax.text(pos_x + 0.2, gy[0] + offset + mid_x, f"B:{frame_name}-{el.id}", 
                                                 color='blue', fontsize=8, fontweight='bold', va='center')
                            
                            # Plot columns and marks
                            if self.main.show_beam_marks.isChecked():
                                for el in columns_at_h:
                                    n1 = f_ss.node_map[el.node_id1].vertex
                                    pos_y = gy[0] + offset + n1.x
                                    self.ax.plot(pos_x, pos_y, 'o', color='darkcyan', markersize=6)
                                    self.ax.text(pos_x - 0.2, pos_y, f"C:{frame_name}-{el.id}", 
                                                 color='darkgreen', fontsize=8, fontweight='bold', ha='right', va='center')

                    else: # Horizontal line (A, B, C...)
                        idx = alphabet.find(line_label)
                        if idx != -1 and idx < len(gy):
                            pos_y = gy[idx]

                            # Plot beams
                            for el in beams_at_h:
                                n1 = f_ss.node_map[el.node_id1].vertex
                                n2 = f_ss.node_map[el.node_id2].vertex
                                self.ax.plot([gx[0] + offset + n1.x, gx[0] + offset + n2.x], [pos_y, pos_y], color='cyan', linewidth=3)
                                
                                if self.main.show_beam_marks.isChecked():
                                    mid_x = (n1.x + n2.x) / 2.0
                                    self.ax.text(gx[0] + offset + mid_x, pos_y + 0.2, f"B:{frame_name}-{el.id}", 
                                                 color='blue', fontsize=8, fontweight='bold', ha='center')

                            # Plot columns and marks
                            if self.main.show_beam_marks.isChecked():
                                for el in columns_at_h:
                                    n1 = f_ss.node_map[el.node_id1].vertex
                                    pos_x = gx[0] + offset + n1.x
                                    self.ax.plot(pos_x, pos_y, 'o', color='darkcyan', markersize=6)
                                    self.ax.text(pos_x, pos_y - 0.2, f"C:{frame_name}-{el.id}", 
                                                 color='darkgreen', fontsize=8, fontweight='bold', ha='center', va='top')

                self.ax.set_aspect('equal', adjustable='box')
                self.ax.autoscale_view()

        except Exception as e:
            print(f"Plotting error: {type(e).__name__}: {e}")
            # Fallback to structure view and update UI if results aren't available
            if mode != "Structure":
                self.main.view_mode.blockSignals(True)
                self.main.view_mode.setCurrentText("Structure")
                self.main.view_mode.blockSignals(False)
                try:
                    prepare_plotter()
                    self.main.ss.plotter.plot_structure(
                        figsize=current_figsize, verbosity=0, show=False, gridplot=True, annotations=False
                    )
                except Exception:
                    pass
        
        # Apply grid and tick settings
        if mode != "Grid Plan":
            # Control axis visibility (ticks, labels, spines)
            self.ax.set_axis_on() if self.main.show_ticks.isChecked() else self.ax.set_axis_off()

            # Control grid visibility independently
            self.ax.grid(self.main.show_grid.isChecked())

        # Ensure aspect ratio is handled correctly to avoid console warnings
        self.ax.set_aspect('equal', adjustable='box')

        # Restore view state
        if self.view_xlim:
            self.ax.set_xlim(self.view_xlim)
            self.ax.set_ylim(self.view_ylim)

        # Refresh the canvas
        self.canvas.draw()

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        self.ax.set_aspect('equal', adjustable='box')
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
            self.ax.set_aspect('equal', adjustable='box')
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