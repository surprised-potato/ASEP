# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/as3600.html

import matplotlib.pyplot as plt
import numpy as np
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties import (
    BilinearStressStrain,
    ConcreteSection,
    EurocodeParabolicUltimate,
    RectangularStressBlock,
)
from concreteproperties.design_codes import AS3600
from concreteproperties.post import si_kn_m, si_n_mm
from concreteproperties.results import BiaxialBendingResults, MomentInteractionResults


design_code = AS3600()
concrete = design_code.create_concrete_material(compressive_strength=40)
steel = design_code.create_steel_material()


print(concrete.name)
print(f"Density = {concrete.density} kg/mm^3")
concrete.stress_strain_profile.plot_stress_strain(
    title="Service Profile", eng=True, units=si_n_mm
)
concrete.ultimate_stress_strain_profile.plot_stress_strain(
    title="Ultimate Profile", eng=True, units=si_n_mm
)
print(
    f"Concrete Flexural Tensile Strength: {concrete.flexural_tensile_strength:.2f} MPa"
)


print(steel.name)
print(f"Density = {steel.density} kg/mm^3")
steel.stress_strain_profile.plot_stress_strain(eng=True, units=si_n_mm)


geom = concrete_rectangular_section(
    b=450,
    d=600,
    dia_top=20,
    area_top=310,
    n_top=5,
    c_top=30,
    dia_bot=20,
    area_bot=310,
    n_bot=5,
    c_bot=30,
    conc_mat=concrete,
    steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()
design_code.assign_concrete_section(concrete_section=conc_sec)


gross_props = design_code.get_gross_properties()
transformed_props = design_code.get_transformed_gross_properties(
    elastic_modulus=concrete.stress_strain_profile.elastic_modulus
)
cracked_props = design_code.calculate_cracked_properties()

gross_props.print_results()
cracked_props.print_results()


f_ult_res, ult_res, phi = design_code.ultimate_bending_capacity()
print(f"Muo = {ult_res.m_xy / 1e6:.2f} kN.m")
print(f"kuo = {ult_res.k_u:.4f}")
print(f"phi = {phi:.3f}")
print(f"phi.Muo = {f_ult_res.m_xy / 1e6:.2f} kN.m")


n_star = 1000e3
f_ult_res, ult_res, phi = design_code.ultimate_bending_capacity(n_design=n_star)
print(f"N* = {n_star / 1e3:.0f} kN")
print(f"Nu = {ult_res.n / 1e3:.2f} kN")
print(f"Mu = {ult_res.m_xy / 1e6:.2f} kN.m")
print(f"phi = {phi:.3f}")
print(f"phi.Nu = {f_ult_res.n / 1e3:.0f} kN")
print(f"phi.Mu = {f_ult_res.m_xy / 1e6:.2f} kN.m")


f_mi_res, mi_res, phis = design_code.moment_interaction_diagram(progress_bar=False)


MomentInteractionResults.plot_multiple_diagrams(
    [mi_res, f_mi_res],
    ["Unfactored", "Factored"],
    fmt="-",
    units=si_kn_m,
)


fig, ax = plt.subplots()
n_list, _ = mi_res.get_results_lists(moment="m_x")  # get list of axial loads
ax.plot(np.array(n_list) / 1e3, phis, "-x")
plt.xlabel("Axial Force [kN]")
plt.ylabel(r"$\phi$")
plt.grid()
plt.show()


# design load cases
n_stars = [4000e3, 5000e3, -500e3, 1000e3]
m_stars = [200e6, 400e6, 100e6, 551e6]
marker_styles = ["x", "+", "o", "*"]
n_cases = len(n_stars)

# plot moment interaction diagram
ax = f_mi_res.plot_diagram(
    fmt="k-",
    units=si_kn_m,
    render=False,
)

# check to see if combination is within diagram and plot result
for idx in range(n_cases):
    case = f_mi_res.point_in_diagram(n=n_stars[idx], m=m_stars[idx])
    print("Case {num}: {status}".format(num=idx + 1, status="OK" if case else "FAIL"))
    ax.plot(
        m_stars[idx] / 1e6,
        n_stars[idx] / 1e3,
        "k" + marker_styles[idx],
        markersize=10,
        label=f"Case {idx + 1}",
    )

ax.legend()
plt.show()


# bilinear
concrete.ultimate_stress_strain_profile = BilinearStressStrain(
    compressive_strength=0.9 * 40,
    compressive_strain=0.0015,
    ultimate_strain=0.003,
)
f_mi_res_bil, _, _ = design_code.moment_interaction_diagram(progress_bar=False)

# parabolic
concrete.ultimate_stress_strain_profile = EurocodeParabolicUltimate(
    compressive_strength=0.9 * 40,
    compressive_strain=0.0015,
    ultimate_strain=0.003,
    n=2,
)
f_mi_res_par, _, _ = design_code.moment_interaction_diagram(progress_bar=False)


MomentInteractionResults.plot_multiple_diagrams(
    [f_mi_res, f_mi_res_bil, f_mi_res_par],
    ["Rectangular", "Bilinear", "Parabolic"],
    fmt="-",
    units=si_kn_m,
)


# reset concrete ultimate profile
concrete.ultimate_stress_strain_profile = RectangularStressBlock(
    compressive_strength=40,
    alpha=0.79,
    gamma=0.87,
    ultimate_strain=0.003,
)

# create biaxial bending diagram
f_bb_res1, phis1 = design_code.biaxial_bending_diagram(n_points=24, progress_bar=False)
bb_res1 = conc_sec.biaxial_bending_diagram(n_points=24, progress_bar=False)
f_bb_res2, phis2 = design_code.biaxial_bending_diagram(
    n_design=2000e3, n_points=24, progress_bar=False
)
bb_res2 = conc_sec.biaxial_bending_diagram(n=2000e3, n_points=24, progress_bar=False)


# plot case 1
BiaxialBendingResults.plot_multiple_diagrams_2d(
    [bb_res1, f_bb_res1],
    labels=["Unfactored", "Factored"],
    units=si_kn_m,
)
print(f"Average phi = {np.mean(phis1):.3f}")

# plot case 2
BiaxialBendingResults.plot_multiple_diagrams_2d(
    [bb_res2, f_bb_res2],
    labels=["Unfactored", "Factored"],
    units=si_kn_m,
)
print(f"Average phi = {np.mean(phis2):.3f}")
