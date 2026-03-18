import os
import datetime
import inspect
import sys
import json
import traceback

# Delay import to allow logging of ImportError
ops = None
openseespy = None

def investigate():
    # Setup output directory and file
    output_dir = "investigation_logs"
    output_file = os.path.join(output_dir, "opensees_attributes.txt")
    
    # Create directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*60}\n")
        f.write(f"OpenSeesPy Investigation Run: {timestamp}\n")
        f.write(f"{'='*60}\n")
        
        try:
            global ops, openseespy
            import openseespy
            import openseespy.opensees as ops
            f.write(f"OpenSeesPy Package Version: {getattr(openseespy, '__version__', 'Unknown')}\n")
            f.write(f"OpenSeesPy File: {openseespy.__file__}\n")
            try:
                f.write(f"OpenSees Version: {ops.version()}\n\n")
            except Exception:
                f.write("Could not determine OpenSees internal version.\n\n")
        except ImportError:
            f.write("OpenSeesPy package not found via standard import check.\n\n")
            return

        # 1. Inspect Module Attributes
        f.write("--- Module Attributes ---\n")
        all_attrs = dir(ops)
        functions = [a for a in all_attrs if callable(getattr(ops, a))]
        others = [a for a in all_attrs if not callable(getattr(ops, a)) and not a.startswith('__')]
        
        f.write(f"Total attributes found in openseespy.opensees: {len(all_attrs)}\n")
        f.write(f"Callable functions: {len(functions)}\n")
        f.write(f"Non-callable attributes: {len(others)}\n")
        if others:
            f.write(f"Non-callable attributes list: {others}\n")

        # 2. Model Setup (Simple Truss based on merged examples)
        f.write("\n--- Model Setup & Return Types ---\n")
        try:
            ops.wipe()
            ops.model('basic', '-ndm', 2, '-ndf', 2)
            f.write("Initialized model('basic', '-ndm', 2, '-ndf', 2)\n")
            
            # Nodes
            # node(tag, x, y)
            res_node = ops.node(1, 0.0, 0.0)
            f.write(f"  - node(1, 0.0, 0.0) return: {res_node} (Type: {type(res_node).__name__})\n")
            ops.node(2, 144.0, 0.0)
            ops.node(3, 168.0, 0.0)
            ops.node(4, 72.0, 96.0)
            
            # Add mass for eigen analysis
            ops.mass(4, 1.0, 1.0)
            
            # Fix
            res_fix = ops.fix(1, 1, 1)
            f.write(f"  - fix(1, 1, 1) return: {res_fix} (Type: {type(res_fix).__name__})\n")
            ops.fix(2, 1, 1)
            ops.fix(3, 1, 1)
            
            # Material
            res_mat = ops.uniaxialMaterial("Elastic", 1, 3000.0)
            f.write(f"  - uniaxialMaterial('Elastic', 1, 3000.0) return: {res_mat} (Type: {type(res_mat).__name__})\n")
            
            # Elements
            # element('Truss', eleTag, iNode, jNode, A, matTag)
            res_ele = ops.element("Truss", 1, 1, 4, 10.0, 1)
            f.write(f"  - element('Truss', ...) return: {res_ele} (Type: {type(res_ele).__name__})\n")
            ops.element("Truss", 2, 2, 4, 5.0, 1)
            ops.element("Truss", 3, 3, 4, 5.0, 1)
            
            # Load
            ops.timeSeries("Linear", 1)
            ops.pattern("Plain", 1, 1)
            res_load = ops.load(4, 100.0, -50.0)
            f.write(f"  - load(4, ...) return: {res_load} (Type: {type(res_load).__name__})\n")
            
            # Analysis Setup
            ops.system("BandSPD")
            ops.numberer("RCM")
            ops.constraints("Plain")
            ops.integrator("LoadControl", 1.0)
            ops.algorithm("Linear")
            ops.analysis("Static")
            
            # Analyze
            res_analyze = ops.analyze(1)
            f.write(f"  - analyze(1) return: {res_analyze} (Type: {type(res_analyze).__name__}) (0=OK)\n")
            
            # 3. Result Inspection
            f.write("\n--- Result Inspection ---\n")
            
            # nodeDisp
            disp = ops.nodeDisp(4)
            f.write(f"  - nodeDisp(4) return: {disp} (Type: {type(disp).__name__})\n")

            # nodeCoord & nodeMass
            try:
                coord = ops.nodeCoord(4)
                f.write(f"  - nodeCoord(4) return: {coord} (Type: {type(coord).__name__})\n")
                mass_val = ops.nodeMass(4)
                f.write(f"  - nodeMass(4) return: {mass_val} (Type: {type(mass_val).__name__})\n")
            except Exception as e: f.write(f"  - nodeCoord/Mass failed: {e}\n")
            
            # eleNodes
            try:
                enodes = ops.eleNodes(1)
                f.write(f"  - eleNodes(1) return: {enodes} (Type: {type(enodes).__name__})\n")
            except Exception as e: f.write(f"  - eleNodes failed: {e}\n")

            # Reactions
            ops.reactions()
            reac = ops.nodeReaction(1)
            f.write(f"  - nodeReaction(1) [after ops.reactions()]: {reac} (Type: {type(reac).__name__})\n")
            
            # eleResponse
            # Probe for available response types on the Truss element
            f.write("  - eleResponse Probing (Truss Element 1):\n")
            response_keywords = ['forces', 'force', 'globalForce', 'localForce', 'basicForce', 
                                 'deformations', 'basicDeformation', 'plasticDeformation',
                                 'stresses', 'stress', 'strain', 'stiff', 'tangent', 'material']
            forces = None
            for key in response_keywords:
                try:
                    val = ops.eleResponse(1, key)
                    if val and val != 0.0: # OpenSees sometimes returns 0.0 or empty list for invalid
                        f.write(f"    - '{key}': {val} (Type: {type(val).__name__})\n")
                        if key == 'forces': forces = val
                    else:
                        f.write(f"    - '{key}': returned empty/zero ({val})\n")
                except Exception:
                    f.write(f"    - '{key}': failed/invalid\n")
            
            # Eigen
            try:
                # Need to set up for eigen? Usually works on existing model
                # Note: eigen command might return list or numpy array depending on version
                eigen_vals = ops.eigen(1)
                f.write(f"  - eigen(1) return: {eigen_vals} (Type: {type(eigen_vals).__name__})\n")
            except Exception as e:
                f.write(f"  - eigen() failed: {e}\n")
                eigen_vals = None

            # 4. Query Functions
            f.write("\n--- Query Functions ---\n")
            queries = [
                ('getNodeTags', []),
                ('getEleTags', []),
                ('getParamTags', []),
                ('getTime', []),
                ('getLoadFactor', [1]),
                ('getNP', []),
                ('getPID', []),
                ('getNumElements', []),
                ('getFixedNodes', []),
                ('getPatterns', []),
                ('getEleClassTags', []),
            ]
            
            for func_name, args in queries:
                if hasattr(ops, func_name):
                    try:
                        val = getattr(ops, func_name)(*args)
                        f.write(f"  - {func_name}{tuple(args)}: {val} (Type: {type(val).__name__})\n")
                    except Exception as e:
                        f.write(f"  - {func_name} failed: {e}\n")
                else:
                    f.write(f"  - {func_name} NOT found in ops module.\n")

            # Specific Getter Tests with arguments
            f.write("\n--- Specific Getter Tests ---\n")
            
            if hasattr(ops, 'getFixedDOFs'):
                try:
                    # Get DOFs for fixed node 1
                    val = ops.getFixedDOFs(1)
                    f.write(f"  - getFixedDOFs(1): {val}\n")
                except Exception as e: f.write(f"  - getFixedDOFs(1) failed: {e}\n")

            if hasattr(ops, 'getNodeLoadTags'):
                try:
                    # Node 4, Pattern 1
                    val = ops.getNodeLoadTags(4, 1)
                    f.write(f"  - getNodeLoadTags(4, 1): {val}\n")
                except Exception as e: f.write(f"  - getNodeLoadTags(4, 1) failed: {e}\n")

            # List all 'get' functions available in the module for discovery
            f.write("\n  - All available 'get*' functions in ops module:\n")
            get_funcs = [f for f in dir(ops) if f.startswith('get') and callable(getattr(ops, f))]
            f.write(f"    {', '.join(sorted(get_funcs))}\n")

            # 5. JSON Serialization Test
            f.write("\n--- JSON Serialization Test ---\n")
            results_dict = {
                "displacement": disp,
                "forces": forces,
                "eigen": eigen_vals
            }
            
            try:
                json.dumps(results_dict)
                f.write("  - Standard json.dumps() successful.\n")
            except TypeError as e:
                f.write(f"  - Standard json.dumps() failed: {e}\n")
                # Verify if it is numpy types causing the issue
                try:
                    import numpy as np
                    class NumpyEncoder(json.JSONEncoder):
                        def default(self, obj):
                            if isinstance(obj, (np.int_, np.intc, np.intp, np.float64)): return float(obj)
                            return super().default(obj)
                    json.dumps(results_dict, cls=NumpyEncoder)
                    f.write("  - Serialization successful using NumpyEncoder.\n")
                except Exception as e2:
                    f.write(f"  - Even with NumpyEncoder, serialization failed: {e2}\n")

            # 6. Model Dump Test
            f.write("\n--- Model Dump Test ---\n")
            try:
                dump_file = os.path.join(output_dir, "model_dump.json")
                ops.printModel("-JSON", "-file", dump_file)
                f.write(f"  - printModel('-JSON') executed. Output at {dump_file}\n")
            except Exception as e:
                f.write(f"  - printModel('-JSON') failed: {e}\n")

        except Exception as e:
            f.write(f"Error during model investigation: {e}\n")
            f.write(traceback.format_exc())

        f.write("\n--- End of Log ---\n")
    
    print(f"Investigation complete. Results written to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    investigate()
