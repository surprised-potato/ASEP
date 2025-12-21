import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import openseespy.opensees as ops
import opsvis as opsv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class TrussAnalyzerApp(tb.Window):
    """
    A GUI application for planar truss analysis using OpenSeesPy and OpsVis.
    """
    def __init__(self):
        super().__init__(themename="superhero") # superhero, darkly, cyborg, vapor
        self.title("Planar Truss Analyzer")
        self.geometry("1400x900")

        # --- Data Storage ---
        self.nodes = {}  # {tag: [x, y]}
        self.elements = {}  # {tag: [node_i, node_j]}
        self.supports = {}  # {node_tag: [dof1_fix, dof2_fix]} (1=fixed, 0=free)
        self.loads = {}  # {node_tag: [fx, fy]}
        self.E = tk.StringVar(value="29000")  # Modulus of Elasticity
        self.A = tk.StringVar(value="10")     # Cross-sectional Area
        
        # --- State Variables ---
        self.interaction_mode = tk.StringVar(value="none") # 'support', 'load', 'none'
        self.viz_mode = tk.StringVar(value="model")
        self.analysis_has_run = False
        self.defo_sfac = 50.0
        self.reac_sfac = 0.5
        self.axial_sfac = 0.05

        # --- GUI Layout ---
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._create_left_panel()
        self._create_right_panel()

        self._build_and_draw_model()

    def _create_left_panel(self):
        """Creates the left panel for inputs and controls."""
        left_frame = ttk.Frame(self.main_frame, padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(8, weight=1) # Give weight to results frame

        # --- Material Properties ---
        props_frame = ttk.LabelFrame(left_frame, text="Material & Section Properties", padding=10)
        props_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        props_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(props_frame, text="E (Modulus):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(props_frame, textvariable=self.E).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Label(props_frame, text="A (Area):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(props_frame, textvariable=self.A).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # --- Nodes Table ---
        nodes_frame = ttk.LabelFrame(left_frame, text="Nodes", padding=10)
        nodes_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        nodes_frame.grid_rowconfigure(0, weight=1)
        nodes_frame.grid_columnconfigure(0, weight=1)

        self.node_tree = ttk.Treeview(nodes_frame, columns=("tag", "x", "y"), show="headings", height=4)
        self.node_tree.heading("tag", text="Tag")
        self.node_tree.heading("x", text="X-Coord")
        self.node_tree.heading("y", text="Y-Coord")
        self.node_tree.grid(row=0, column=0, sticky="nsew")
        
        node_buttons = ttk.Frame(nodes_frame)
        node_buttons.grid(row=1, column=0, pady=5)
        ttk.Button(node_buttons, text="Add", command=self._add_node, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(node_buttons, text="Delete", command=self._delete_node, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)

        # --- Elements Table ---
        elements_frame = ttk.LabelFrame(left_frame, text="Elements", padding=10)
        elements_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)
        elements_frame.grid_rowconfigure(0, weight=1)
        elements_frame.grid_columnconfigure(0, weight=1)

        self.element_tree = ttk.Treeview(elements_frame, columns=("tag", "node_i", "node_j"), show="headings", height=4)
        self.element_tree.heading("tag", text="Tag")
        self.element_tree.heading("node_i", text="Node I")
        self.element_tree.heading("node_j", text="Node J")
        self.element_tree.grid(row=0, column=0, sticky="nsew")

        element_buttons = ttk.Frame(elements_frame)
        element_buttons.grid(row=1, column=0, pady=5)
        ttk.Button(element_buttons, text="Add", command=self._add_element, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(element_buttons, text="Delete", command=self._delete_element, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)
        
        # --- Supports Table ---
        supports_frame = ttk.LabelFrame(left_frame, text="Supports", padding=10)
        supports_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=5)
        supports_frame.grid_rowconfigure(0, weight=1)
        supports_frame.grid_columnconfigure(0, weight=1)

        self.support_tree = ttk.Treeview(supports_frame, columns=("tag", "fix_x", "fix_y"), show="headings", height=3)
        self.support_tree.heading("tag", text="Node Tag")
        self.support_tree.heading("fix_x", text="Fixity X (1=Fix)")
        self.support_tree.heading("fix_y", text="Fixity Y (1=Fix)")
        self.support_tree.grid(row=0, column=0, sticky="nsew")

        support_buttons = ttk.Frame(supports_frame)
        support_buttons.grid(row=1, column=0, pady=5)
        ttk.Button(support_buttons, text="Add", command=self._add_support, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(support_buttons, text="Delete", command=self._delete_support, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)
        
        # --- Loads Table ---
        loads_frame = ttk.LabelFrame(left_frame, text="Loads", padding=10)
        loads_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        loads_frame.grid_rowconfigure(0, weight=1)
        loads_frame.grid_columnconfigure(0, weight=1)

        self.load_tree = ttk.Treeview(loads_frame, columns=("tag", "fx", "fy"), show="headings", height=3)
        self.load_tree.heading("tag", text="Node Tag")
        self.load_tree.heading("fx", text="Fx")
        self.load_tree.heading("fy", text="Fy")
        self.load_tree.grid(row=0, column=0, sticky="nsew")

        load_buttons = ttk.Frame(loads_frame)
        load_buttons.grid(row=1, column=0, pady=5)
        ttk.Button(load_buttons, text="Add", command=self._add_load, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(load_buttons, text="Delete", command=self._delete_load, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)

        # --- Interaction Controls ---
        interact_frame = ttk.LabelFrame(left_frame, text="Define on Plot", padding=10)
        interact_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Radiobutton(interact_frame, text="Add/Edit Supports", variable=self.interaction_mode, value="support").pack(anchor=tk.W)
        ttk.Radiobutton(interact_frame, text="Add/Edit Loads", variable=self.interaction_mode, value="load").pack(anchor=tk.W)
        ttk.Radiobutton(interact_frame, text="None (View)", variable=self.interaction_mode, value="none").pack(anchor=tk.W)
        
        # --- Analysis and Reset ---
        action_frame = ttk.Frame(left_frame, padding=5)
        action_frame.grid(row=6, column=0, columnspan=2, pady=5)
        ttk.Button(action_frame, text="Run Analysis", command=self._run_analysis, bootstyle=PRIMARY).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(action_frame, text="Reset Model", command=self._reset_model, bootstyle=SECONDARY).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- Visualization Controls ---
        viz_frame = ttk.LabelFrame(left_frame, text="Visualization", padding=10)
        viz_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Radiobutton(viz_frame, text="Model View", variable=self.viz_mode, value="model", command=self._update_visualization).pack(anchor=tk.W)
        self.deformed_rb = ttk.Radiobutton(viz_frame, text="Deformed Shape", variable=self.viz_mode, value="deformed", command=self._update_visualization, state=tk.DISABLED)
        self.deformed_rb.pack(anchor=tk.W)
        self.reactions_rb = ttk.Radiobutton(viz_frame, text="Reactions", variable=self.viz_mode, value="reactions", command=self._update_visualization, state=tk.DISABLED)
        self.reactions_rb.pack(anchor=tk.W)
        self.axial_rb = ttk.Radiobutton(viz_frame, text="Axial Force", variable=self.viz_mode, value="axial", command=self._update_visualization, state=tk.DISABLED)
        self.axial_rb.pack(anchor=tk.W)
        
        # --- Results Table ---
        results_frame = ttk.LabelFrame(left_frame, text="Results", padding=10)
        results_frame.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        self.results_tree = ttk.Treeview(results_frame, columns=("item", "value"), show="headings")
        self.results_tree.heading("item", text="Result")
        self.results_tree.heading("value", text="Value")
        self.results_tree.grid(row=0, column=0, sticky="nsew")

    def _create_right_panel(self):
        """Creates the right panel for the Matplotlib canvas."""
        plot_frame = ttk.LabelFrame(self.main_frame, text="Structure View", padding=10)
        plot_frame.grid(row=0, column=1, sticky="nsew")
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.fig.set_facecolor("#222222") # Match dark theme
        self.ax.set_facecolor("#333333")
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['right'].set_color('none')
        self.ax.spines['top'].set_color('none')

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)

    def _invalidate_results(self):
        """Called when the model is changed, making prior analysis results invalid."""
        if self.analysis_has_run:
            self.analysis_has_run = False
            self.deformed_rb.config(state=tk.DISABLED)
            self.reactions_rb.config(state=tk.DISABLED)
            self.axial_rb.config(state=tk.DISABLED)
            self.viz_mode.set("model")
            self.results_tree.delete(*self.results_tree.get_children())
            messagebox.showinfo("Results Invalidated", "Model has been modified. Please re-run analysis to see new results.")

    # --- Table Management Callbacks ---
    def _add_node(self):
        try:
            data = simpledialog.askstring("Add Node", "Enter tag, x, y (comma-separated):", parent=self)
            if data:
                tag, x, y = map(float, data.split(','))
                tag = int(tag)
                if tag in self.nodes:
                    raise ValueError("Node tag already exists.")
                self.nodes[tag] = [x, y]
                self._populate_node_table()
                self._invalidate_results()
                self._build_and_draw_model()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")

    def _delete_node(self):
        selected = self.node_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No node selected.")
            return
        
        node_tag = int(self.node_tree.item(selected[0])['values'][0])
        
        for ele_tag, ele_nodes in self.elements.items():
            if node_tag in ele_nodes:
                messagebox.showerror("Error", f"Cannot delete node {node_tag}. It is used in element {ele_tag}.")
                return
                
        del self.nodes[node_tag]
        self.supports.pop(node_tag, None)
        self.loads.pop(node_tag, None)
        
        self._populate_node_table()
        self._populate_support_table()
        self._populate_load_table()
        self._invalidate_results()
        self._build_and_draw_model()

    def _populate_node_table(self):
        self.node_tree.delete(*self.node_tree.get_children())
        for tag, coords in sorted(self.nodes.items()):
            self.node_tree.insert("", "end", values=(tag, coords[0], coords[1]))
            
    def _add_element(self):
        try:
            data = simpledialog.askstring("Add Element", "Enter tag, node_i, node_j (comma-separated):", parent=self)
            if data:
                tag, i, j = map(int, data.split(','))
                if tag in self.elements:
                    raise ValueError("Element tag already exists.")
                if i not in self.nodes or j not in self.nodes:
                    raise ValueError("One or both nodes do not exist.")
                self.elements[tag] = [i, j]
                self._populate_element_table()
                self._invalidate_results()
                self._build_and_draw_model()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")

    def _delete_element(self):
        selected = self.element_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No element selected.")
            return
        tag = int(self.element_tree.item(selected[0])['values'][0])
        del self.elements[tag]
        self._populate_element_table()
        self._invalidate_results()
        self._build_and_draw_model()
        
    def _populate_element_table(self):
        self.element_tree.delete(*self.element_tree.get_children())
        for tag, nodes in sorted(self.elements.items()):
            self.element_tree.insert("", "end", values=(tag, nodes[0], nodes[1]))

    def _add_support(self):
        try:
            data = simpledialog.askstring("Add Support", "Node Tag, Fixity X, Fixity Y (e.g., 1,1,0):", parent=self)
            if data:
                tag, fix_x, fix_y = map(int, data.split(','))
                if tag not in self.nodes:
                    raise ValueError(f"Node {tag} does not exist.")
                if fix_x not in [0, 1] or fix_y not in [0, 1]:
                    raise ValueError("Fixity values must be 0 (free) or 1 (fixed).")
                self.supports[tag] = [fix_x, fix_y]
                self._populate_support_table()
                self._invalidate_results()
                self._build_and_draw_model()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")

    def _delete_support(self):
        selected = self.support_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No support selected.")
            return
        tag = int(self.support_tree.item(selected[0])['values'][0])
        del self.supports[tag]
        self._populate_support_table()
        self._invalidate_results()
        self._build_and_draw_model()

    def _populate_support_table(self):
        self.support_tree.delete(*self.support_tree.get_children())
        for tag, fixity in sorted(self.supports.items()):
            self.support_tree.insert("", "end", values=(tag, fixity[0], fixity[1]))

    def _add_load(self):
        try:
            data = simpledialog.askstring("Add Load", "Node Tag, Fx, Fy (e.g., 4, 100, -50):", parent=self)
            if data:
                tag_str, fx_str, fy_str = data.split(',')
                tag = int(tag_str)
                fx, fy = float(fx_str), float(fy_str)
                if tag not in self.nodes:
                    raise ValueError(f"Node {tag} does not exist.")
                self.loads[tag] = [fx, fy]
                self._populate_load_table()
                self._invalidate_results()
                self._build_and_draw_model()
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")

    def _delete_load(self):
        selected = self.load_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No load selected.")
            return
        tag = int(self.load_tree.item(selected[0])['values'][0])
        del self.loads[tag]
        self._populate_load_table()
        self._invalidate_results()
        self._build_and_draw_model()

    def _populate_load_table(self):
        self.load_tree.delete(*self.load_tree.get_children())
        for tag, forces in sorted(self.loads.items()):
            self.load_tree.insert("", "end", values=(tag, forces[0], forces[1]))

    # --- Plotting and OpenSees Interaction ---
    def _build_and_draw_model(self, viz_mode='model', sfac=50.0):
        """
        Wipes and rebuilds the OpenSees model from stored data, then draws it.
        Also runs analysis if a results visualization is requested.
        """
        self.ax.clear()
        ops.wipe()
        ops.model('basic', '-ndm', 2, '-ndf', 2)

        if not self.nodes:
            self.ax.set_title("No Model Defined", color='white')
            self.canvas.draw()
            return
            
        for tag, (x, y) in self.nodes.items():
            ops.node(tag, x, y)
        
        try:
            E_val = float(self.E.get())
            A_val = float(self.A.get())
            if E_val > 0 and A_val > 0:
                ops.uniaxialMaterial("Elastic", 1, E_val)
                for tag, (i, j) in self.elements.items():
                    ops.element("Truss", tag, i, j, A_val, 1)
        except (ValueError, RuntimeError):
            pass
            
        for node_tag, fixity in self.supports.items():
            ops.fix(node_tag, *fixity)
            
        if self.loads:
            ops.timeSeries("Linear", 1)
            ops.pattern("Plain", 1, 1)
            for node_tag, (fx, fy) in self.loads.items():
                ops.load(node_tag, fx, fy)

        # If a results visualization is requested, run a silent analysis first
        if viz_mode in ['deformed', 'reactions', 'axial']:
            if not self.analysis_has_run: # Avoid re-running if just switching viz
                messagebox.showwarning("Analysis Required", "Please run analysis first to view results.")
                self.viz_mode.set('model')
                self._build_and_draw_model(viz_mode='model')
                return

            # Rebuild model with analysis components
            ops.system("BandGeneral")
            ops.numberer("RCM")
            ops.constraints("Plain")
            ops.integrator("LoadControl", 1.0)
            ops.algorithm("Linear")
            ops.analysis("Static")
            ok = ops.analyze(1)
            if ok != 0:
                messagebox.showerror("Analysis Error", "Could not re-run analysis for visualization. The model may be unstable.")
                self.viz_mode.set('model')
                self._build_and_draw_model(viz_mode='model')
                return

        # Plot using OpsVis
        plt.sca(self.ax)
        if viz_mode == 'model':
            opsv.plot_model(node_labels=1, element_labels=0)
            if self.loads:
                opsv.plot_load(load_sf=sfac*0.01) # Use a scaled factor for loads
            self.ax.set_title("Model View", color='white')
        elif viz_mode == 'deformed':
            opsv.plot_defo(sfac=sfac, unDefoFlag=1)
            self.ax.set_title(f"Deformed Shape (sfac={sfac})", color='white')
        elif viz_mode == 'reactions':
            ops.reactions()
            opsv.plot_reactions(reac_sf=sfac)
            opsv.plot_model(node_labels=0, element_labels=0)
            self.ax.set_title("Support Reactions", color='white')
        elif viz_mode == 'axial':
            opsv.section_force_diagram_2d('N', sfac=sfac)
            opsv.plot_model(node_labels=0, element_labels=0)
            self.ax.set_title("Axial Force Diagram", color='white')

        self.ax.set_xlabel("X-direction")
        self.ax.set_ylabel("Y-direction")
        self.ax.axis('equal')
        self.fig.tight_layout()
        self.canvas.draw()

    def _update_visualization(self):
        """Prompts for a scale factor and redraws the plot based on the viz_mode."""
        mode = self.viz_mode.get()

        if mode == 'deformed':
            sfac = simpledialog.askfloat("Deformation Scale", "Enter deformation scale factor:", initialvalue=self.defo_sfac, parent=self)
            if sfac is not None:
                self.defo_sfac = sfac
                self._build_and_draw_model(viz_mode='deformed', sfac=self.defo_sfac)
        elif mode == 'reactions':
            sfac = simpledialog.askfloat("Reaction Scale", "Enter reaction vector scale factor:", initialvalue=self.reac_sfac, parent=self)
            if sfac is not None:
                self.reac_sfac = sfac
                self._build_and_draw_model(viz_mode='reactions', sfac=self.reac_sfac)
        elif mode == 'axial':
            sfac = simpledialog.askfloat("Axial Force Scale", "Enter axial force diagram scale factor:", initialvalue=self.axial_sfac, parent=self)
            if sfac is not None:
                self.axial_sfac = sfac
                self._build_and_draw_model(viz_mode='axial', sfac=self.axial_sfac)
        else: # model view
            self._build_and_draw_model(viz_mode='model')

    def _on_canvas_click(self, event):
        """Handles clicks on the canvas to add supports or loads."""
        mode = self.interaction_mode.get()
        if mode == 'none' or event.xdata is None or event.ydata is None or not self.nodes:
            return
            
        min_dist = float('inf')
        clicked_node_tag = -1
        for tag, (nx, ny) in self.nodes.items():
            dist = ((event.xdata - nx)**2 + (event.ydata - ny)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                clicked_node_tag = tag

        plot_x_range = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
        tolerance = plot_x_range * 0.05 if plot_x_range > 0 else 0.5
        
        if min_dist > tolerance:
            return
            
        model_changed = False
        if mode == 'support':
            support_type = simpledialog.askstring("Support Type", "Enter type ('pin', 'roller-y', 'roller-x', 'none'):", parent=self)
            if support_type:
                support_type = support_type.lower()
                if support_type == 'pin': self.supports[clicked_node_tag] = [1, 1]
                elif support_type == 'roller-y': self.supports[clicked_node_tag] = [0, 1]
                elif support_type == 'roller-x': self.supports[clicked_node_tag] = [1, 0]
                elif support_type == 'none': self.supports.pop(clicked_node_tag, None)
                else: messagebox.showerror("Error", "Invalid support type.")
                model_changed = True
        
        elif mode == 'load':
            load_data = simpledialog.askstring("Define Load", "Enter Fx, Fy (e.g., 100, -50) or '0,0' to remove:", parent=self)
            if load_data:
                try:
                    fx, fy = map(float, load_data.split(','))
                    if fx == 0 and fy == 0: self.loads.pop(clicked_node_tag, None)
                    else: self.loads[clicked_node_tag] = [fx, fy]
                    model_changed = True
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid load data: {e}")
        
        if model_changed:
            self._populate_support_table()
            self._populate_load_table()
            self._invalidate_results()
            self._build_and_draw_model()
        
    def _run_analysis(self):
        """Performs the static analysis and displays results."""
        if not self.elements:
            messagebox.showerror("Error", "No elements defined. Cannot run analysis.")
            return

        try:
            self._build_and_draw_model() # Rebuild to ensure model is current
            ops.system("BandGeneral"); ops.numberer("RCM"); ops.constraints("Plain")
            ops.integrator("LoadControl", 1.0); ops.algorithm("Linear"); ops.analysis("Static")
            ok = ops.analyze(1)
            
            if ok != 0:
                messagebox.showerror("Analysis Failed", "The analysis did not converge. The model may be unstable.")
                return

            messagebox.showinfo("Success", "Analysis complete.")
            self.analysis_has_run = True
            
            self.deformed_rb.config(state=tk.NORMAL)
            self.reactions_rb.config(state=tk.NORMAL)
            self.axial_rb.config(state=tk.NORMAL)
            
            self.viz_mode.set("deformed")
            self._update_visualization()
            self._populate_results()

        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred during analysis: {e}")
            
    def _populate_results(self):
        """Fills the results table with analysis output."""
        self.results_tree.delete(*self.results_tree.get_children())
        
        self.results_tree.insert("", "end", values=("--- Deformations ---", ""))
        for node_tag in sorted(self.nodes.keys()):
            disp_x = ops.nodeDisp(node_tag, 1); disp_y = ops.nodeDisp(node_tag, 2)
            self.results_tree.insert("", "end", values=(f"Node {node_tag} Ux", f"{disp_x:.4e}"))
            self.results_tree.insert("", "end", values=(f"Node {node_tag} Uy", f"{disp_y:.4e}"))
            
        ops.reactions()
        self.results_tree.insert("", "end", values=("--- Reactions ---", ""))
        for node_tag in sorted(self.supports.keys()):
            react_x = ops.nodeReaction(node_tag, 1); react_y = ops.nodeReaction(node_tag, 2)
            self.results_tree.insert("", "end", values=(f"Node {node_tag} Rx", f"{react_x:.4f}"))
            self.results_tree.insert("", "end", values=(f"Node {node_tag} Ry", f"{react_y:.4f}"))

        self.results_tree.insert("", "end", values=("--- Member Forces ---", ""))
        for ele_tag in sorted(self.elements.keys()):
            force = ops.eleForce(ele_tag, 1) # Axial force for truss element
            self.results_tree.insert("", "end", values=(f"Element {ele_tag} Force", f"{force:.4f}"))
    
    def _reset_model(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to clear the entire model?"):
            self.nodes.clear(); self.elements.clear(); self.supports.clear(); self.loads.clear()
            self._populate_node_table(); self._populate_element_table()
            self._populate_support_table(); self._populate_load_table()
            self._invalidate_results()
            self.viz_mode.set("model")
            self._build_and_draw_model()

if __name__ == "__main__":
    try:
        import openseespy, opsvis, matplotlib, numpy, ttkbootstrap
    except ImportError as e:
        print(f"Error: A required library is not installed: {e.name}")
        print("Please install it using pip, e.g., 'pip install openseespy opsvis matplotlib numpy ttkbootstrap'")
        exit()
        
    app = TrussAnalyzerApp()
    app.mainloop()

