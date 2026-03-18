from grid_manager import GridManager

def run_analysis():
    # 1. Define the 3D Grid (Dimensions in meters)
    # X-axis: 2 bays of 5m
    # Y-axis: 1 bay of 6m
    # Z-axis: 2 floors of 3.5m
    x_coords = [0, 5, 10]
    y_coords = [0, 6]
    z_coords = [0, 3.5, 7.0]

    manager = GridManager(x_coords, y_coords, z_coords)

    # Optional: Set human-readable labels for the report
    manager.set_grid_labels('x', {0: 'Grid 1', 5: 'Grid 2', 10: 'Grid 3'})
    manager.set_grid_labels('y', {0: 'Grid A', 6: 'Grid B'})
    manager.set_grid_labels('z', {0: 'Ground', 3.5: 'Floor 1', 7.0: 'Roof'})

    # 2. Define Material Properties (SI Units: kN, m)
    # Typical Steel Section Properties (simplified)
    column_props = {
        'EA': 2.1e6,  # Axial Stiffness
        'EI': 5.0e4,  # Bending Stiffness
        'g': 0.8      # Self-weight (kN/m)
    }

    beam_props = {
        'EA': 1.5e6,
        'EI': 3.5e4,
        'g': 0.5
    }

    # 3. Add Vertical Members (Columns)
    # We loop through X and Y grid lines to place columns at intersections
    for x in x_coords:
        for y in y_coords:
            # Ground to Floor 1
            manager.add_orthogonal_member((x, y, 0), (x, y, 3.5), **column_props)
            # Floor 1 to Roof
            manager.add_orthogonal_member((x, y, 3.5), (x, y, 7.0), **column_props)

    # 4. Add Horizontal Members (Beams)
    # Longitudinal beams (along X)
    for y in y_coords:
        for z in [3.5, 7.0]:
            manager.add_orthogonal_member((0, y, z), (5, y, z), **beam_props)
            manager.add_orthogonal_member((5, y, z), (10, y, z), **beam_props)

    # Transverse beams (along Y)
    for x in x_coords:
        for z in [3.5, 7.0]:
            manager.add_orthogonal_member((x, 0, z), (x, 6, z), **beam_props)

    # 5. Apply Slab Loads (kN/m2)
    # Let's apply a dead load of 4 kN/m2 and live load of 2 kN/m2 to the first floor
    # We define the boundary using X and Y ranges
    manager.add_slab_load(x_range=(0, 5), y_range=(0, 6), z_level=3.5, area_load=6.0)
    manager.add_slab_load(x_range=(5, 10), y_range=(0, 6), z_level=3.5, area_load=6.0)

    # 5a. Define Foundation Supports
    manager.set_foundation(z_level=0.0, support_type='fixed')

    # 6. Solve the Building
    print("Starting global 3D decomposition solve...")
    manager.solve_building(enforce_diaphragm=True)

    # 7. Generate Reports
    print("\n--- Structural Analysis Summary ---")
    
    # Get Worst Case
    heatmap = manager.get_global_heatmap()
    print(f"Max Bending Moment: {heatmap['MaxMoment']:.2f} kNm")
    print(f"Critical Location: {heatmap['CriticalFrame']}")

    # Export CSV for detailed checking
    manager.report_to_csv("building_analysis_results.csv")

    # Visualize a specific slice (Grid Line A at Y=0) for all result types
    print("\nDisplaying results for XZ Plane at Y=0 (Grid Line A)...")
    result_types = ['moment', 'shear', 'axial', 'displacement']
    for r_type in result_types:
        print(f"  Plotting {r_type} diagram...")
        manager.plot_slice(plane='XZ', coord=0.0, result_type=r_type)

if __name__ == "__main__":
    run_analysis()