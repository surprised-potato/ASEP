# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/cracked_properties.html

import numpy as np
from sectionproperties.pre.library import concrete_tee_section

from concreteproperties import (
    Concrete,
    ConcreteLinear,
    ConcreteSection,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
)


concrete = Concrete(
    name="40 MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=ConcreteLinear(elastic_modulus=32.8e3),
    ultimate_stress_strain_profile=RectangularStressBlock(
        compressive_strength=40,
        alpha=0.79,
        gamma=0.87,
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=3.8,
    colour="lightgrey",
)

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


geom = concrete_tee_section(
    d=900,
    b=300,
    d_f=200,
    b_f=1200,
    dia_top=16,
    area_top=200,
    n_top=6,
    c_top=30,
    dia_bot=32,
    area_bot=800,
    n_bot=3,
    c_bot=30,
    conc_mat=concrete,
    steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


cracked_res_sag = conc_sec.calculate_cracked_properties()
cracked_res_hog = conc_sec.calculate_cracked_properties(theta=np.pi)


cracked_res_sag.print_results()
cracked_res_hog.print_results()


from concreteproperties.post import si_kn_m, si_n_mm

si_n_mm.radians = False  # show degrees

cracked_res_sag.calculate_transformed_properties(elastic_modulus=32.8e3)
cracked_res_hog.calculate_transformed_properties(elastic_modulus=32.8e3)

cracked_res_sag.print_results(units=si_kn_m)
cracked_res_hog.print_results(units=si_n_mm)


cracking_moment = cracked_res_sag.m_cr
neutral_axis_depth = cracked_res_sag.d_nc
cracked_i = cracked_res_sag.iuu_cr

print(f"M_cr = {cracking_moment / 1e6:.2f} kN.m")
print(f"d_nc = {neutral_axis_depth:.2f} mm")
print(f"I_cr = {cracked_i:.3e} mm^4")


cracked_res_sag.plot_cracked_geometries(labels=[], cp=False, legend=False)


cracked_res_hog.plot_cracked_geometries(labels=[], cp=False, legend=False)
