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
            ss.add_element(location=[[0, 0], [1, 0]])
            ss.add_support_hinged(node_id=1)
            ss.add_support_roll(node_id=2, direction=2)
            
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