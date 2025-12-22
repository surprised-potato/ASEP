import os
import datetime
import inspect
from anastruct import SystemElements

def investigate():
    # Setup output directory and file
    output_dir = "investigation_logs"
    output_file = os.path.join(output_dir, "anastruct_attributes.txt")
    
    # Create directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*60}\n")
        f.write(f"Investigation Run: {timestamp}\n")
        f.write(f"{'='*60}\n")
        
        try:
            import anastruct
            f.write(f"Anastruct Package Version: {getattr(anastruct, '__version__', 'Unknown')}\n")
            f.write(f"Anastruct File: {anastruct.__file__}\n\n")
        except ImportError:
            f.write("Anastruct package not found via standard import check.\n\n")

        ss = SystemElements()
        f.write("Initialized SystemElements()\n")
        
        # Add some dummy elements and supports to populate lists/dicts if they exist
        # This helps determine if attributes are initialized as None or empty lists/dicts
        try:
            f.write("--- Model Setup ---\n")
            ss.add_element(location=[[0, 0], [1, 0]], g=15) # Test dead load storage
            ss.add_support_hinged(node_id=1)
            ss.add_support_roll(node_id=2, direction=2)

            # Test q_load directions and non-uniform magnitudes based on GUI learnings
            f.write("--- Load Data Structure Testing ---\n")
            # 1. q_load Directions and Sequences
            for d in ['y', 'x', 'element', 'parallel']:
                try:
                    ss.loads_q = {} 
                    ss.q_load(q=10, element_id=1, direction=d)
                    f.write(f"  - q_load(direction='{d}'): loads_q[1] = {ss.loads_q.get(1)}\n")
                except Exception as e: f.write(f"  - q_load direction='{d}' failed: {type(e).__name__}: {e}\n")
            
            try:
                ss.loads_q = {}
                ss.q_load(q=[5, 15], element_id=1, direction='element')
                f.write(f"  - q_load(q=[5, 15]): loads_q[1] = {ss.loads_q.get(1)}\n")
            except Exception as e: f.write(f"  - non-uniform q_load failed: {type(e).__name__}: {e}\n")
            
            try:
                ss.loads_q = {}
                ss.q_load(q=[10, -10], element_id=1, direction='element')
                f.write(f"  - q_load(q=[10, -10]): loads_q[1] = {ss.loads_q.get(1)}\n")
            except Exception as e: f.write(f"  - sign-flipping q_load failed: {e}\n")

            # 2. Load Accumulation Test
            try:
                ss.loads_point = {}
                ss.point_load(node_id=1, Fx=10)
                ss.point_load(node_id=1, Fx=20)
                f.write(f"  - Sequential point_load(10 then 20): loads_point[1] = {ss.loads_point.get(1)} (Check if 30 or 20)\n")
            except Exception as e: f.write(f"  - point_load accumulation test failed: {e}\n")

            # 3. point_load and moment_load structures
            try:
                ss.point_load(node_id=1, Fx=10, Fz=-20)
                f.write(f"  - point_load(Fx=10, Fz=-20): loads_point[1] = {ss.loads_point.get(1)}\n")
                
                ss.moment_load(node_id=2, Ty=50)
                f.write(f"  - moment_load(Ty=50): loads_moment[2] = {ss.loads_moment.get(2)}\n")
            except Exception as e: f.write(f"  - point/moment load test failed: {type(e).__name__}: {e}\n")

            # 4. Mesh and Result Resolution Test
            f.write("--- Mesh and Result Resolution Testing ---\n")
            for m_val in [1, 5]:
                try:
                    ss_mesh = SystemElements(mesh=m_val)
                    ss_mesh.add_element(location=[[0, 0], [10, 0]])
                    ss_mesh.add_support_fixed(node_id=1)
                    ss_mesh.q_load(q=-10, element_id=1)
                    ss_mesh.solve()
                    el = ss_mesh.element_map[1]
                    f.write(f"  - System(mesh={m_val}): el.bending_moment length = {len(el.bending_moment) if el.bending_moment is not None else 'N/A'}\n")
                except Exception as e: f.write(f"  - Mesh test (m={m_val}) failed: {type(e).__name__}: {e}\n")

            # 5. Plasticity and Non-linear Elements
            f.write("--- Plasticity Testing ---\n")
            try:
                ss_pl = SystemElements()
                # Adding element with plastic moment capacity
                ss_pl.add_element(location=[[0, 0], [5, 0]], mp=100)
                f.write(f"  - Element with mp=100: non_linear_elements = {ss_pl.non_linear_elements}\n")
                if ss_pl.element_map:
                    el = ss_pl.element_map[list(ss_pl.element_map.keys())[0]]
                    f.write(f"    - Element attributes: mp={getattr(el, 'mp', 'N/A')}\n")
            except Exception as e: f.write(f"  - Plasticity test failed: {type(e).__name__}: {e}\n")

            # 6. Spring Roll Test
            f.write("--- Spring Roll Testing ---\n")
            try:
                ss_sp = SystemElements()
                ss_sp.add_element(location=[[0, 0], [1, 0]])
                ss_sp.add_support_spring(node_id=1, k=1000, translation=1, roll=True)
                f.write(f"  - Spring with roll=True: supports_spring_args = {ss_sp.supports_spring_args}\n")
                f.write(f"    - supports_spring_x: {getattr(ss_sp, 'supports_spring_x', 'N/A')}\n")
                
                ss_sp2 = SystemElements()
                ss_sp2.add_element(location=[[0, 0], [1, 0]])
                ss_sp2.add_support_spring(node_id=1, k=1000, translation=1, roll=False)
                f.write(f"  - Spring with roll=False: supports_spring_args = {ss_sp2.supports_spring_args}\n")
                f.write(f"    - supports_spring_x: {getattr(ss_sp2, 'supports_spring_x', 'N/A')}\n")
            except Exception as e: f.write(f"  - Spring roll test failed: {type(e).__name__}: {e}\n")

            # 7. Post-Solve Result and Reaction Discovery
            f.write("--- Post-Solve Result and Reaction Discovery ---\n")
            try:
                ss_res = SystemElements()
                ss_res.add_element(location=[[0, 0], [5, 0]])
                ss_res.add_support_fixed(node_id=1)
                ss_res.point_load(node_id=2, Fy=-10)
                ss_res.solve()
                
                f.write("  - System solved (Cantilever with -10 vertical load at tip).\n")
                
                # Search SystemElements for result-related attributes
                all_ss_attrs = dir(ss_res)
                interesting = [a for a in all_ss_attrs if any(k in a.lower() for k in ['reac', 'force', 'disp', 'moment'])]
                f.write("  - System-level result attributes:\n")
                for attr in sorted(interesting):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(ss_res, attr)
                            f.write(f"    - {attr:<20} | Type: {type(val).__name__:<10} | Value: {str(val)[:100]}\n")
                        except Exception: pass
                
                # Inspect Node 1 (Support) for reactions
                if 1 in ss_res.node_map:
                    n1 = ss_res.node_map[1]
                    f.write(f"  - Node 1 (Fixed Support) attributes after solve:\n")
                    for attr in ['Fx', 'Fy', 'Tz', 'ux', 'uy', 'phi_z']:
                        f.write(f"    - {attr:<10}: {getattr(n1, attr, 'N/A')}\n")
                
                # Inspect Element 1 for forces
                if 1 in ss_res.element_map:
                    el = ss_res.element_map[1]
                    f.write(f"  - Element 1 forces: axial={type(el.axial_force)}, shear={type(el.shear_force)}, moment={type(el.bending_moment)}\n")
                
                # 8. Result Re-solve Test
                f.write("--- Re-solve Testing ---\n")
                ss_res.point_load(node_id=2, Fy=-20) # Change load
                ss_res.solve()
                n1_new = ss_res.node_map[1]
                f.write(f"  - Node 1 Fy after re-solve with -20 load: {getattr(n1_new, 'Fy', 'N/A')}\n")

                # 9. JSON Serialization Pitfall Test
                f.write("--- JSON Serialization Pitfall Discovery ---\n")
                try:
                    import json
                    # Attempting to serialize the raw reaction_forces dict
                    json.dumps(ss_res.reaction_forces)
                    f.write("  - reaction_forces is directly serializable.\n")
                except TypeError as e:
                    f.write(f"  - reaction_forces serialization failed as expected: {e}\n")

            except Exception as e:
                f.write(f"  - Result discovery failed: {type(e).__name__}: {e}\n")

            
            # Try adding a spring if the method exists to see where it goes
            if hasattr(ss, 'add_support_spring'):
                try:
                    # Try generic spring
                    ss.add_support_spring(node_id=1, k=1000, translation=1)
                    f.write("  - Added spring support via add_support_spring(translation=1).\n")
                except Exception as e:
                    f.write(f"  - Failed to add spring support: {e}\n")
            else:
                f.write("  - method 'add_support_spring' NOT found.\n")

        except Exception as e:
            f.write(f"Error setting up dummy system: {e}\n")

        # Inspect Element and Node objects directly
        f.write("\n--- Object Inspection ---\n")
        if ss.element_map:
            el_id = list(ss.element_map.keys())[0]
            el_obj = ss.element_map[el_id]
            f.write(f"Element Object (ID {el_id}) Attributes:\n")
            for attr in sorted(dir(el_obj)):
                if not attr.startswith('_') and not callable(getattr(el_obj, attr)):
                    f.write(f"  {attr:<20}: {type(getattr(el_obj, attr)).__name__}\n")

        if ss.node_map:
            n_id = list(ss.node_map.keys())[0]
            n_obj = ss.node_map[n_id]
            f.write(f"\nNode Object (ID {n_id}) Attributes:\n")
            for attr in sorted(dir(n_obj)):
                if not attr.startswith('_') and not callable(getattr(n_obj, attr)):
                    f.write(f"  {attr:<20}: {type(getattr(n_obj, attr)).__name__}\n")

        # Inspect Method Signatures
        f.write("\n--- Method Signatures ---\n")
        methods_to_check = ['add_element', 'add_support_spring', 'q_load', 'point_load', 'solve']
        for m_name in methods_to_check:
            if hasattr(ss, m_name):
                try:
                    sig = inspect.signature(getattr(ss, m_name))
                    f.write(f"{m_name:<20}: {sig}\n")
                except Exception: pass

        f.write("\n--- SystemElements Attributes Inspection ---\n")
        attributes = dir(ss)
        
        # Filter for interesting attributes (supports, loads, nodes, elements)
        interesting_keywords = ['support', 'load', 'node', 'element', 'spring']
        
        found_attributes = []
        for attr_name in attributes:
            if attr_name.startswith('__'):
                continue
                
            # Check if it matches keywords
            if any(k in attr_name.lower() for k in interesting_keywords):
                try:
                    attr_value = getattr(ss, attr_name)
                    attr_type = type(attr_value).__name__
                    
                    # We are interested in data structures (lists, dicts) mostly
                    if not callable(attr_value):
                        found_attributes.append((attr_name, attr_type, str(attr_value)))
                except Exception:
                    pass

        # Sort and write
        for name, type_name, value in sorted(found_attributes):
            f.write(f"{name:<30} | Type: {type_name:<10} | Value: {value}\n")

        f.write("\n--- End of Log ---\n")
        
    print(f"Investigation complete. Results written to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    investigate()