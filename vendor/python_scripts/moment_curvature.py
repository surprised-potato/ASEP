# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/moment_curvature.html

import numpy as np
from sectionproperties.pre.library import circular_section, rectangular_section

import concreteproperties.stress_strain_profile as ssp
from concreteproperties import (
    Concrete,
    ConcreteSection,
    SteelBar,
    add_bar_rectangular_array,
)
from concreteproperties.post import si_kn_m, si_n_mm
from concreteproperties.results import MomentCurvatureResults


conc_linear = Concrete(
    name="Linear Concrete",
    density=2.4e-6,
    stress_strain_profile=ssp.ConcreteLinear(
        elastic_modulus=35e3, ultimate_strain=0.0035
    ),
    ultimate_stress_strain_profile=ssp.BilinearStressStrain(
        compressive_strength=40,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=3.5,
    colour="lightgrey",
)

conc_linear_no_tension = Concrete(
    name="Linear Concrete (No T)",
    density=2.4e-6,
    stress_strain_profile=ssp.ConcreteLinearNoTension(
        elastic_modulus=35e3, ultimate_strain=0.0035
    ),
    ultimate_stress_strain_profile=ssp.BilinearStressStrain(
        compressive_strength=40,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=3.5,
    colour="lightgrey",
)


conc_nonlinear = Concrete(
    name="Non-Linear Concrete",
    density=2.4e-6,
    stress_strain_profile=ssp.EurocodeNonLinear(
        elastic_modulus=35e3,
        ultimate_strain=0.0035,
        compressive_strength=40,
        compressive_strain=0.0023,
        tensile_strength=3.5,
        tension_softening_stiffness=10e3,
    ),
    ultimate_stress_strain_profile=ssp.BilinearStressStrain(
        compressive_strength=40,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=3.5,
    colour="lightgrey",
)

conc_material_list = [
    conc_linear,
    conc_linear_no_tension,
    conc_nonlinear,
]

steel = SteelBar(
    name="Steel - Elastic-Plastic",
    density=7.85e-6,
    stress_strain_profile=ssp.SteelElasticPlastic(
        yield_strength=500,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="grey",
)


for conc in conc_material_list:
    conc.stress_strain_profile.plot_stress_strain(
        title=conc.name, eng=True, units=si_n_mm
    )


steel.stress_strain_profile.plot_stress_strain(
    title=steel.name, eng=True, units=si_n_mm
)


col = rectangular_section(d=350, b=600)
void = circular_section(d=125, n=12).align_center(align_to=col)
col = col - void  # subtract void from column

# add bars to column
geom = add_bar_rectangular_array(
    geometry=col,
    area=450,
    material=steel,
    n_x=6,
    x_s=492 / 5,
    n_y=3,
    y_s=121,
    anchor=(54, 54),
    exterior_only=True,
)

geom.plot_geometry(labels=[], cp=False, legend=False)


# initialise list to store results and list to store labels
moment_curvature_results = []
labels = []

# loop through each concrete material
for idx, conc in enumerate(conc_material_list):
    # assign concrete material to first geometry in CompoundGeometry object
    geom.geoms[0].material = conc

    # create ConcreteSection object
    conc_sec = ConcreteSection(geom)

    # plot section first time only
    if idx == 0:
        conc_sec.plot_section()

    # perform moment curvature analysis and store results
    # bending about major axis so theta = pi/2
    res = conc_sec.moment_curvature_analysis(
        theta=np.pi / 2, kappa_inc=2.5e-7, progress_bar=False
    )
    moment_curvature_results.append(res)

    # create plot label
    labels.append(conc.name)


MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=moment_curvature_results,
    labels=labels,
    fmt="-",
    eng=True,
    units=si_kn_m,
)


print(moment_curvature_results[0].failure_geometry.material.name)


MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=moment_curvature_results[1:],
    labels=labels[1:],
    fmt="-",
    eng=True,
    units=si_kn_m,
)


m_cr = conc_sec.calculate_cracked_properties(theta=np.pi / 2).m_cr / 1e6
print(f"M_cr = {m_cr:.2f} kN.m")


import matplotlib.pyplot as plt

fix, ax = plt.subplots()
kappa = np.array(moment_curvature_results[-1].kappa)
moment = np.array(moment_curvature_results[-1].m_xy) / 1e6
ax.plot(kappa[:12], moment[:12], "x-")
plt.show()


concrete = Concrete(
    name="Concrete (No Tension)",
    density=2.4e-6,
    stress_strain_profile=ssp.ConcreteLinearNoTension(
        elastic_modulus=35e3,
        ultimate_strain=0.003,
        compressive_strength=40,
    ),
    ultimate_stress_strain_profile=ssp.BilinearStressStrain(
        compressive_strength=40,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=3.5,
    colour="lightgrey",
)

geom = rectangular_section(d=600, b=400, material=concrete)

geom = add_bar_rectangular_array(
    geometry=geom,
    area=450,
    material=steel,
    n_x=3,
    x_s=158,
    n_y=3,
    y_s=258,
    anchor=(42, 42),
    exterior_only=True,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


res1 = conc_sec.moment_curvature_analysis(progress_bar=False)


res1.plot_results()
print(f"Number of calculations = {len(res1.kappa)}")
print(f"Failure curvature = {res1.kappa[-1]:.4e}")


res2 = conc_sec.moment_curvature_analysis(kappa_inc=5e-6, progress_bar=False)


res2.plot_results()
print(f"Number of calculations = {len(res2.kappa)}")
print(f"Failure curvature = {res2.kappa[-1]:.4e}")


res3 = conc_sec.moment_curvature_analysis(
    kappa_inc=1e-6,
    kappa_mult=1.25,
    delta_m_min=0.1,
    kappa_inc_max=2e-5,
    progress_bar=False,
)


res3.plot_results()
print(f"Number of calculations = {len(res3.kappa)}")
print(f"Failure curvature = {res3.kappa[-1]:.4e}")


MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=[res2, res3],
    labels=["Coarse", "Refined"],
    fmt="-",
)


concrete = Concrete(
    name="Concrete (No Tension)",
    density=2.4e-6,
    stress_strain_profile=ssp.ConcreteLinearNoTension(
        elastic_modulus=35e3,
        ultimate_strain=0.003,
        compressive_strength=31,
    ),
    ultimate_stress_strain_profile=ssp.BilinearStressStrain(
        compressive_strength=31,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=3.5,
    colour="lightgrey",
)

steel = SteelBar(
    name="Steel - Elastic-Plastic",
    density=7.85e-6,
    stress_strain_profile=ssp.SteelElasticPlastic(
        yield_strength=320,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="grey",
)

geom = rectangular_section(d=600, b=600, material=concrete)
geom = add_bar_rectangular_array(
    geometry=geom,
    area=610,
    material=steel,
    n_x=3,
    x_s=236,
    n_y=3,
    y_s=236,
    anchor=(64, 64),
    exterior_only=True,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


res_n0 = conc_sec.moment_curvature_analysis(n=0, kappa_inc=1e-6, progress_bar=False)
res_n1 = conc_sec.moment_curvature_analysis(
    n=0.2 * 600 * 600 * 31, kappa_inc=1e-6, progress_bar=False
)
res_nt = conc_sec.moment_curvature_analysis(
    n=-1000e3, kappa_inc=1e-6, progress_bar=False
)


MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=[res_n0, res_n1, res_nt],
    labels=["$N=0$ kN", "$N=0.2f'cA_g$", "$N=-1000$ kN"],
    fmt="-",
    eng=True,
    units=si_kn_m,
)
