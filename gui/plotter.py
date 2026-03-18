import string
import numpy as np
import matplotlib.pyplot as plt
import traceback
from mpl_toolkits.mplot3d import Axes3D

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

    def _ensure_axes(self, projection='2d'):
        """Recreates axes if the projection type changes (e.g., 2D to 3D)."""
        target_proj = '3d' if projection == '3d' else 'rectilinear'
        if not hasattr(self.ax, 'name') or self.ax.name != target_proj:
            self.figure.clear()
            if projection == '3d':
                self.ax = self.figure.add_subplot(111, projection='3d')
            else:
                self.ax = self.figure.add_subplot(111)
            self.main.ax = self.ax

    def update_plot(self):
        mode = self.main.view_mode.currentText()

        # Determine required projection and clear axes
        if mode == "3D Wireframe":
            self._ensure_axes('3d')
        else:
            self._ensure_axes('2d')
        self.ax.clear()

        try:
            if mode == "Grid Plan":
                self.plot_grid_plan()
            elif mode == "3D Wireframe":
                self.plot_3d_wireframe()
            elif mode == "Member Analysis":
                self.plot_member_analysis()
            else: # Standard anastruct plots
                self.plot_anastruct_results(mode)
        except Exception as e:
            print(f"Plotting error in mode '{mode}': {type(e).__name__}: {e}")
            traceback.print_exc()
            self.ax.text(0.5, 0.5, f"Error plotting '{mode}'", ha='center', va='center', color='red')

        # Restore view state
        if self.view_xlim and self.ax.name != '3d':
            self.ax.set_xlim(self.view_xlim)
            self.ax.set_ylim(self.view_ylim)
            
        self.canvas.draw()

    def plot_grid_plan(self):
        """Custom drawing for the pre-analysis top-down grid view."""
        self.ax.set_axis_off()
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        alphabet = string.ascii_uppercase

        # 1. Parse grid spacings from UI
        try:
            sx = [float(s.strip()) for s in self.main.grid_x_input.text().split(',') if s.strip()]
            sy = [float(s.strip()) for s in self.main.grid_y_input.text().split(',') if s.strip()]
            gx = [0.0] + list(np.cumsum(sx))
            gy = [0.0] + list(np.cumsum(sy))
        except ValueError:
            self.ax.text(0.5, 0.5, "Invalid Grid Spacing", ha='center', va='center', color='red')
            return

        # 2. Parse Z-levels from UI
        try:
            z_levels = sorted([float(self.main.grid_z_table.item(r, 1).text()) for r in range(self.main.grid_z_table.rowCount())])
            min_z = z_levels[0] if z_levels else 0.0
            sel_text = self.main.floor_selector.currentText()
            sel_height = float(sel_text.split('(')[1].split('m')[0])
        except (ValueError, AttributeError, IndexError):
            min_z, sel_height = 0.0, 0.0

        # 3. Draw Grid Lines and Labels
        if self.main.show_grid.isChecked():
            for x in gx: self.ax.axvline(x, color='gray', linestyle='--', linewidth=1.0)
            for y in gy: self.ax.axhline(y, color='gray', linestyle='--', linewidth=1.0)
        
        if self.main.show_grid_labels.isChecked():
            for i, x in enumerate(gx): self.ax.text(x, gy[0] - 0.5, str(i+1), ha='center', va='top', color='black', fontweight='bold')
            for i, y in enumerate(gy): self.ax.text(gx[0] - 0.5, gy[i], alphabet[i], ha='right', va='center', color='black', fontweight='bold')

        # 4. Draw Slabs (using the self.main.building model populated by the GUI)
        for name, data in self.main.building.slabs.items():
            if not np.isclose(data.get('level', -1), sel_height): continue
            
            pts = []
            for x_idx, y_idx in data.get('points', []):
                if x_idx < len(gx) and y_idx < len(gy):
                    pts.append([gx[x_idx], gy[y_idx]])
            if pts:
                poly = plt.Polygon(pts, closed=True, facecolor='orange', alpha=0.3, edgecolor='darkorange', linewidth=1)
                self.ax.add_patch(poly)
                cx, cy = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
                self.ax.text(cx, cy, name, ha='center', va='center', color='darkred', fontsize=9)

        # 5. Draw Frames
        template_h = sel_height - min_z
        for row in range(self.main.grid_table.rowCount()):
            try:
                line_label = self.main.grid_table.item(row, 0).text().upper()
                frame_name = self.main.grid_table.cellWidget(row, 1).currentText()
                offset = float(self.main.grid_table.item(row, 2).text())
                
                f_model = self.main.frame_templates.get(frame_name)
                if not f_model or not f_model.system.element_map: continue

                # Find beams in the template at the correct relative height
                for el in f_model.system.element_map.values():
                    n1 = f_model.system.node_map[el.node_id1].vertex
                    n2 = f_model.system.node_map[el.node_id2].vertex
                    
                    if np.isclose(n1.y, template_h) and np.isclose(n2.y, template_h):
                        # This is a beam at the correct level, now plot it
                        if line_label.isdigit(): # Vertical grid line
                            idx = int(line_label) - 1
                            if idx < len(gx):
                                pos_x = gx[idx]
                                # Frame's local X is along global Y
                                self.ax.plot([pos_x, pos_x], [n1.x + offset, n2.x + offset], color='steelblue', linewidth=2.5)
                        else: # Horizontal grid line
                            idx = alphabet.find(line_label)
                            if idx != -1 and idx < len(gy):
                                pos_y = gy[idx]
                                # Frame's local X is along global X
                                self.ax.plot([n1.x + offset, n2.x + offset], [pos_y, pos_y], color='steelblue', linewidth=2.5)
            except (ValueError, AttributeError, IndexError):
                continue # Skip invalid rows

        self.ax.set_aspect('equal', adjustable='box')
        self.ax.autoscale_view()

    def plot_3d_wireframe(self):
        """Plots the solved 3D model from the GridManager."""
        self.ax.set_axis_on()
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        if not self.main.manager:
            self.ax.text(0.5, 0.5, 0.5, "Run analysis to view 3D model", ha='center', va='center', transform=self.ax.transAxes)
            return

        gx, gy, gz = self.main.manager.grid['x'], self.main.manager.grid['y'], self.main.manager.grid['z']
        
        # Draw all elements from all solved frames
        all_frames = list(self.main.manager.xz_frames.items()) + list(self.main.manager.yz_frames.items())
        for coord, ss in all_frames:
            if not ss.element_map: continue
            is_xz = coord in gy

            for el in ss.element_map.values():
                n1, n2 = ss.node_map[el.node_id1].vertex, ss.node_map[el.node_id2].vertex
                if is_xz: # XZ frame at Y=coord
                    self.ax.plot([n1.x, n2.x], [coord, coord], [n1.y, n2.y], color='steelblue', linewidth=1.5)
                else: # YZ frame at X=coord
                    self.ax.plot([coord, coord], [n1.x, n2.x], [n1.y, n2.y], color='steelblue', linewidth=1.5)

        # Ticks and Labels
        if self.main.show_ticks.isChecked():
            self.ax.set_xticks(gx); self.ax.set_yticks(gy); self.ax.set_zticks(gz)
        self.ax.set_xlabel('X'); self.ax.set_ylabel('Y'); self.ax.set_zlabel('Z')
        self.ax.grid(self.main.show_grid.isChecked())
        if not self.view_xlim: self.ax.view_init(elev=20, azim=-35)

    def plot_anastruct_results(self, mode):
        """Calls the standard anastruct plotting functions."""
        if not self.main.ss or not self.main.ss.element_map:
            self.ax.text(0.5, 0.5, "No system loaded or system is empty.", ha='center', va='center')
            return

        # Ensure anastruct uses our existing axes
        self.main.ss.plotter.axes = [self.ax]
        self.main.ss.plotter.fig = self.figure
        
        scale = self.main.scale_slider.value()
        
        plot_map = {
            "Structure": self.main.ss.show_structure,
            "Displacement": self.main.ss.show_displacement,
            "Axial Force": self.main.ss.show_axial_force,
            "Shear Force": self.main.ss.show_shear_force,
            "Bending Moment": self.main.ss.show_bending_moment,
        }
        
        plot_func = plot_map.get(mode)
        if plot_func:
            kwargs = {'show': False, 'verbosity': 0}
            # Special handling for different method signatures in anastruct
            if mode == "Displacement":
                kwargs['factor'] = scale
            # For all plot types, we can pass figsize. For older anastruct versions,
            # this is critical for show_structure(), which had it as a required argument.
            kwargs['figsize'] = self.main.ss.figsize
            plot_func(**kwargs)
            self.ax.set_title(mode, color='black')

    def plot_member_analysis(self):
        # This can be implemented later if needed
        self.ax.text(0.5, 0.5, "Member Analysis not yet implemented.", ha='center', va='center')

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        # Simplified zoom logic
        scale_factor = 1.1 if event.button == 'up' else 1 / 1.1
        cur_xlim = self.ax.get_xlim(); cur_ylim = self.ax.get_ylim()
        self.ax.set_xlim([c - (c - event.xdata) * scale_factor for c in cur_xlim])
        self.ax.set_ylim([c - (c - event.ydata) * scale_factor for c in cur_ylim])
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.button == 2: self.press = event.xdata, event.ydata, self.ax.get_xlim(), self.ax.get_ylim()

    def on_release(self, event): self.press = None

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax: return
        xpress, ypress, xlim, ylim = self.press
        dx = event.xdata - xpress; dy = event.ydata - ypress
        self.ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
        self.ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
        self.canvas.draw_idle()

    def reset_view(self):
        self.view_xlim = None
        self.view_ylim = None
        self.update_plot()