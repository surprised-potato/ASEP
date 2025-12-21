# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/prestressed_section.html

import matplotlib.pyplot as plt
import numpy as np
from sectionproperties.pre.library import rectangular_section

from concreteproperties import (
    BilinearStressStrain,
    Concrete,
    ConcreteLinearNoTension,
    EurocodeNonLinear,
    PrestressedSection,
    SteelStrand,
    StrandHardening,
    add_bar_rectangular_array,
)
from concreteproperties.post import si_kn_m, si_n_mm
from concreteproperties.results import MomentCurvatureResults


concrete_service = Concrete(
    name="C50/60 Concrete (Service)",
    density=2.4e-6,
    stress_strain_profile=EurocodeNonLinear(
        elastic_modulus=37.0e3,
        ultimate_strain=0.0035,
        compressive_strength=58,
        compressive_strain=0.00245,
        tensile_strength=4.1,
        tension_softening_stiffness=10e3,
    ),
    ultimate_stress_strain_profile=BilinearStressStrain(
        compressive_strength=50 / 1.5,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=4.1,
    colour="lightgrey",
)

concrete_ultimate = Concrete(
    name="C50/60 Concrete (Ultimate)",
    density=2.4e-6,
    stress_strain_profile=ConcreteLinearNoTension(
        elastic_modulus=37.0e3,
        ultimate_strain=0.0035,
        compressive_strength=50 / 1.5,
    ),
    ultimate_stress_strain_profile=BilinearStressStrain(
        compressive_strength=50 / 1.5,
        compressive_strain=0.00175,
        ultimate_strain=0.0035,
    ),
    flexural_tensile_strength=4.1,
    colour="lightgrey",
)

strand_service = SteelStrand(
    name="Y1860S7 Strand (Service)",
    density=7.85e-6,
    stress_strain_profile=StrandHardening(
        yield_strength=1674,
        elastic_modulus=195e3,
        fracture_strain=0.035,
        breaking_strength=1860,
    ),
    colour="grey",
    prestress_stress=1274.4,
)

strand_ultimate = SteelStrand(
    name="Y1860S7 Strand (Ultimate)",
    density=7.85e-6,
    stress_strain_profile=StrandHardening(
        yield_strength=1522,
        elastic_modulus=195e3,
        fracture_strain=0.035,
        breaking_strength=1691,
    ),
    colour="grey",
    prestress_stress=1148.6,
)


# combine both stress-strain profiles on the same plot
ax = concrete_service.stress_strain_profile.plot_stress_strain(
    units=si_n_mm, render=False
)
concrete_service.ultimate_stress_strain_profile.plot_stress_strain(units=si_n_mm, ax=ax)
ax.lines[0].set_label("Service")
ax.lines[1].set_label("Ultimate")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.title("Concrete C50/60")
plt.show()


# combine both stress-strain profiles on the same plot
ax = strand_service.stress_strain_profile.plot_stress_strain(
    eng=True, units=si_kn_m, render=False
)
strand_ultimate.stress_strain_profile.plot_stress_strain(eng=True, units=si_kn_m, ax=ax)
ax.lines[0].set_label("Service")
ax.lines[1].set_label("Ultimate")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.title("Strand Y1860S7")
plt.show()


# box properties
d_box = 1100  # box depth
b_box = 1500  # box width
t_box = 250  # box thickness

# strand properties
strand_area = 140  # area of each strand
duct_diameter = 72  # diameter of the tendon ducts
strand_d1 = 125  # distance from bottom to layer 1
strand_d2 = strand_d1 + 72  # distance from bottom to layer 2
strand_d3 = strand_d2 + 165.4  # distance from bottom to layer 3

# generate a service and ultimate PrestressedConcrete object
conc_secs = []
concrete_props = [concrete_service, concrete_ultimate]
strand_props = [strand_service, strand_ultimate]

for idx, concrete_prop in enumerate(concrete_props):
    # construct concrete hollow box
    box_outer = rectangular_section(d=d_box, b=b_box, material=concrete_prop)
    box_inner = rectangular_section(
        d=d_box - 2 * t_box, b=b_box - 2 * t_box
    ).align_center(align_to=box_outer)
    box = box_outer - box_inner

    # add web strands (6 x 8 strand tendons)
    # lower two sets
    geom = add_bar_rectangular_array(
        geometry=box,
        area=8 * strand_area,
        material=strand_props[idx],
        n_x=2,
        x_s=b_box - t_box,
        n_y=2,
        y_s=strand_d2 - strand_d1,
        anchor=(t_box / 2, strand_d1),
    )

    # top set
    geom = add_bar_rectangular_array(
        geometry=geom,
        area=8 * strand_area,
        material=strand_props[idx],
        n_x=2,
        x_s=b_box - t_box,
        anchor=(t_box / 2, strand_d3),
    )

    # add flange strands (2 x 9 strand tendons)
    geom = add_bar_rectangular_array(
        geometry=geom,
        area=9 * strand_area,
        material=strand_props[idx],
        n_x=2,
        x_s=(b_box - t_box) / 3,
        anchor=(t_box / 2 + (b_box - t_box) / 3, strand_d1),
    )

    # create prestressed section objects
    conc_secs.append(PrestressedSection(geom))

# extract prestressed section objects
conc_sec_serv = conc_secs[0]
conc_sec_ult = conc_secs[1]

# plot each object
conc_sec_serv.plot_section()
conc_sec_ult.plot_section()


gross_props_serv = conc_sec_serv.get_gross_properties()
gross_props_ult = conc_sec_ult.get_gross_properties()
gross_props_serv.print_results(units=si_n_mm)


print(f"P_0 = {gross_props_serv.n_prestress / 1e3:.0f} kN")
print(f"M_0 = {gross_props_serv.m_prestress / 1e6:.0f} kN.m")
print(f"P_inf = {gross_props_ult.n_prestress / 1e3:.0f} kN")
print(f"M_inf = {gross_props_ult.m_prestress / 1e6:.0f} kN.m")


# design actions
L = 35500  # length of girder in [mm]
g_sw = gross_props_serv.mass * 9.81  # self weight in [N/mm]
g_si = 3  # superimposed dead load in [N/mm]
q = 10  # live load in [N/mm]

# calculate moments
m_g_sw = g_sw * L * L / 8  # moment due to self weight
m_g_si = g_si * L * L / 8  # moment due to superimposed dead load
m_q = q * L * L / 8  # moment due to live load
m_ed = 1.2 * (m_g_sw + m_g_si) + 1.5 * m_q

print(f"M_g_sw = {m_g_sw / 1e6:.0f} kN.m")
print(f"M_g_si = {m_g_si / 1e6:.0f} kN.m")
print(f"M_q = {m_q / 1e6:.0f} kN.m")
print(f"M_Ed = {m_ed / 1e6:.0f} kN.m")


# stress due to prestressing only
uncr_stress_p = conc_sec_serv.calculate_uncracked_stress()
uncr_stress_p.plot_stress(units=si_n_mm)


cr_p_serv = conc_sec_serv.calculate_cracked_properties(m_ext=0)
cr_p_ult = conc_sec_ult.calculate_cracked_properties(m_ext=0)
cr_p_serv.print_results(units=si_kn_m)
cr_stress_p_serv = conc_sec_serv.calculate_cracked_stress(cracked_results=cr_p_serv)
cr_stress_p_serv.plot_stress(units=si_n_mm)


print(f"M_cr_pos_s = {cr_p_serv.m_cr[0] / 1e6:.0f} kN.m")
print(f"M_cr_pos_u = {cr_p_ult.m_cr[0] / 1e6:.0f} kN.m")
print(f"M_cr_neg_s = {cr_p_serv.m_cr[1] / 1e6:.0f} kN.m")
print(f"M_cr_neg_u = {cr_p_ult.m_cr[1] / 1e6:.0f} kN.m")


# stress due to G_sw + P at t = 0
uncr_stress_t0 = conc_sec_serv.calculate_uncracked_stress(m=m_g_sw)
uncr_stress_t0.plot_stress(units=si_n_mm)


# stress due to G + Q + P at t = inf
uncr_stress_tinf = conc_sec_ult.calculate_uncracked_stress(m=m_g_sw + m_g_si + m_q)
uncr_stress_tinf.plot_stress(units=si_n_mm)


ult_res = conc_sec_ult.ultimate_bending_capacity()
ult_res.print_results(units=si_kn_m)


print(f"d_n = {ult_res.d_n:.1f} mm")
print(f"M_Rd = {ult_res.m_x / 1e6:.0f} kN.m")
print(f"M_Ed = {m_ed / 1e6:.0f} kN.m")
print("M_Rd >= M_Ed, therefore OK!")


ult_stress = conc_sec_ult.calculate_ultimate_stress(ultimate_results=ult_res)
ult_stress.plot_stress(units=si_n_mm)


mk_serv = conc_sec_serv.moment_curvature_analysis(
    kappa_mult=1.1, kappa_inc=5e-7, progress_bar=False
)


mk_ult = conc_sec_ult.moment_curvature_analysis(
    kappa_mult=1.1, kappa_inc=5e-7, progress_bar=False
)


MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=[mk_serv, mk_ult],
    labels=["Service", "Ultimate"],
    fmt="-",
    eng=True,
    units=si_kn_m,
)


serv_stress_s_1 = conc_sec_serv.calculate_service_stress(
    moment_curvature_results=mk_serv, m=None, kappa=mk_serv.kappa[0]
)
serv_stress_u_1 = conc_sec_ult.calculate_service_stress(
    moment_curvature_results=mk_ult, m=None, kappa=mk_ult.kappa[0]
)
serv_stress_s_1.plot_stress(units=si_n_mm)
serv_stress_u_1.plot_stress(units=si_n_mm)


fix, ax = plt.subplots()  # create plot
m_serv = np.array(mk_serv.m_x[:4]) / 1e6  # get service analysis moments
m_ult = np.array(mk_ult.m_x[:4]) / 1e6  # get ultimate analysis moments
ax.plot(mk_serv.kappa[:4], m_serv, "x-", label="Service")
ax.plot(mk_ult.kappa[:4], m_ult, "x-", label="Ultimate")
ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
plt.grid()
plt.show()


serv_stress_s_2 = conc_sec_serv.calculate_service_stress(
    moment_curvature_results=mk_serv, m=8000e6
)
serv_stress_u_2 = conc_sec_ult.calculate_service_stress(
    moment_curvature_results=mk_ult, m=8000e6
)
serv_stress_s_2.plot_stress(units=si_n_mm)
serv_stress_u_2.plot_stress(units=si_n_mm)
