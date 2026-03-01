import os
import datetime
import inspect
import sys
import json
import traceback

# Delay imports to allow for graceful failure logging
concreteproperties = None
sectionproperties = None
Concrete = None
SteelBar = None
ConcreteSection = None
concrete_rectangular_section = None
RectangularStressBlock = None
ConcreteLinear = None
SteelElasticPlastic = None


def investigate():
    # Setup output directory and file
    output_dir = "investigation_logs"
    output_file = os.path.join(output_dir, "concreteproperties_attributes.txt")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*60}\n")
        f.write(f"concrete-properties Investigation Run: {timestamp}\n")
        f.write(f"{'='*60}\n")
        
        try:
            global concreteproperties, sectionproperties, Concrete, SteelBar, ConcreteSection, concrete_rectangular_section, RectangularStressBlock, ConcreteLinear, SteelElasticPlastic
            import concreteproperties as cp_pkg
            concreteproperties = cp_pkg
            import sectionproperties as sp_pkg
            sectionproperties = sp_pkg
            
            from concreteproperties import (
                Concrete,
                ConcreteLinear,
                ConcreteSection,
                RectangularStressBlock,
                SteelBar,
                SteelElasticPlastic,
            )
            from sectionproperties.pre.library import concrete_rectangular_section

            f.write(f"concrete-properties Version: {getattr(concreteproperties, '__version__', 'Unknown')}\n")
            f.write(f"concrete-properties File: {concreteproperties.__file__}\n")
            f.write(f"sectionproperties Version: {getattr(sectionproperties, '__version__', 'Unknown')}\n")
            f.write(f"sectionproperties File: {sectionproperties.__file__}\n\n")

        except ImportError as e:
            f.write(f"ImportError: {e}. concrete-properties or sectionproperties not found.\n\n")
            return

        # 1. Model Setup (based on area_properties.py example)
        f.write("--- Model Setup ---\n")
        try:
            concrete = Concrete(
                name="32 MPa Concrete",
                density=2.4e-6,
                stress_strain_profile=ConcreteLinear(elastic_modulus=30.1e3),
                ultimate_stress_strain_profile=RectangularStressBlock(
                    compressive_strength=32,
                    alpha=0.802,
                    gamma=0.89,
                    ultimate_strain=0.003,
                ),
                flexural_tensile_strength=3.4,
                colour="lightgrey",
            )
            f.write("  - Created Concrete material object.\n")

            steel = SteelBar(
                name="500 MPa Steel",
                density=7.85e-6,
                stress_strain_profile=SteelElasticPlastic(
                    yield_strength=500,
                    elastic_modulus=200e3,
                    fracture_strain=0.05,
                ),
                colour="grey",
            )
            f.write("  - Created SteelBar material object.\n")

            geom = concrete_rectangular_section(
                d=600, b=400, dia_top=20, area_top=310, n_top=3, c_top=30,
                dia_bot=24, area_bot=450, n_bot=3, c_bot=30,
                conc_mat=concrete, steel_mat=steel,
            )
            f.write("  - Created section geometry with reinforcement.\n")

            conc_sec = ConcreteSection(geom)
            f.write("  - Initialized ConcreteSection object.\n")

            # 2. Inspect Initial Object Attributes
            f.write("\n--- Initial ConcreteSection Object Inspection ---\n")
            initial_attrs = [a for a in dir(conc_sec) if not a.startswith('_') and not callable(getattr(conc_sec, a))]
            for attr in sorted(initial_attrs):
                val = getattr(conc_sec, attr)
                f.write(f"  - {attr:<30} | Type: {type(val).__name__}\n")

            # 3. Analysis and Result Object Inspection
            f.write("\n--- Analysis & Result Object Inspection ---\n")
            
            # Gross Properties
            try:
                gross_props = conc_sec.get_gross_properties()
                f.write("  - Called get_gross_properties().\n")
                f.write(f"    - Result object type: {type(gross_props).__name__}\n")
                f.write("    - Attributes on GrossProperties object:\n")
                result_attrs = [a for a in dir(gross_props) if not a.startswith('_') and not callable(getattr(gross_props, a))]
                for attr in sorted(result_attrs):
                    val = getattr(gross_props, attr)
                    f.write(f"      - {attr:<25} | Type: {type(val).__name__}\n")
                
                # JSON Serialization Test for GrossProperties
                f.write("    - JSON Serialization Test (GrossProperties):\n")
                if hasattr(gross_props, '_results'):
                    try:
                        json.dumps(gross_props._results)
                        f.write("      - `_results` dictionary is directly serializable.\n")
                    except TypeError as e:
                        f.write(f"      - `_results` serialization failed: {e}\n")
                        try:
                            import numpy as np
                            class NumpyEncoder(json.JSONEncoder):
                                def default(self, obj):
                                    if isinstance(obj, (np.int_, np.intc, np.intp, np.float64, np.ndarray)):
                                        if isinstance(obj, np.ndarray):
                                            return obj.tolist()
                                        return float(obj)
                                    return super().default(obj)
                            json.dumps(gross_props._results, cls=NumpyEncoder)
                            f.write("      - Serialization successful using NumpyEncoder.\n")
                        except Exception as e2:
                            f.write(f"      - Even with NumpyEncoder, serialization failed: {e2}\n")
                else:
                    f.write("      - `_results` attribute not found on GrossProperties object.\n")

            except Exception as e:
                f.write(f"  - get_gross_properties() failed: {type(e).__name__}: {e}\n")
                f.write(traceback.format_exc())

            # Cracked Properties
            try:
                cracked_props = conc_sec.calculate_cracked_properties()
                f.write("\n  - Called calculate_cracked_properties().\n")
                f.write(f"    - Result object type: {type(cracked_props).__name__}\n")
                f.write("    - Attributes on CrackedProperties object:\n")
                result_attrs = [a for a in dir(cracked_props) if not a.startswith('_') and not callable(getattr(cracked_props, a))]
                for attr in sorted(result_attrs):
                     f.write(f"      - {attr:<25} | Type: {type(getattr(cracked_props, attr)).__name__}\n")

            except Exception as e:
                f.write(f"\n  - calculate_cracked_properties() failed: {type(e).__name__}: {e}\n")
                f.write(traceback.format_exc())

            # Moment Interaction
            try:
                mi_res = conc_sec.moment_interaction_diagram(progress_bar=False)
                f.write("\n  - Called moment_interaction_diagram().\n")
                f.write(f"    - Result object type: {type(mi_res).__name__}\n")
                if hasattr(mi_res, 'results') and mi_res.results:
                    first_res = mi_res.results[0]
                    f.write(f"    - The 'results' list contains objects of type: {type(first_res).__name__}\n")
                    f.write("    - Attributes on the inner UltimateBendingResults object:\n")
                    inner_attrs = [a for a in dir(first_res) if not a.startswith('_') and not callable(getattr(first_res, a))]
                    for attr in sorted(inner_attrs):
                        f.write(f"      - {attr:<25} | Type: {type(getattr(first_res, attr)).__name__}\n")

            except Exception as e:
                f.write(f"\n  - moment_interaction_diagram() failed: {type(e).__name__}: {e}\n")
                f.write(traceback.format_exc())

            # 4. Method Signature Inspection
            f.write("\n--- Method Signatures ---\n")
            methods_to_check = [
                'get_gross_properties', 'get_transformed_gross_properties',
                'calculate_cracked_properties', 'moment_curvature_analysis',
                'ultimate_bending_capacity', 'moment_interaction_diagram',
                'biaxial_bending_diagram', 'calculate_uncracked_stress',
                'calculate_cracked_stress', 'calculate_service_stress',
                'calculate_ultimate_stress',
            ]
            for m_name in methods_to_check:
                if hasattr(conc_sec, m_name):
                    try:
                        sig = inspect.signature(getattr(conc_sec, m_name))
                        f.write(f"{m_name:<35}: {sig}\n")
                    except Exception as e:
                        f.write(f"{m_name:<35}: FAILED to inspect - {e}\n")

        except Exception as e:
            f.write(f"Error during model setup or analysis: {e}\n")
            f.write(traceback.format_exc())

        f.write("\n--- End of Log ---\n")
    
    print(f"Investigation complete. Results written to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    investigate()