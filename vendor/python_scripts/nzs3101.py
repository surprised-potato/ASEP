# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/nzs3101.html

import matplotlib.pyplot as plt
import numpy as np
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties import (
    Concrete,
    ConcreteSection,
    ModifiedMander,
    RectangularStressBlock,
)
from concreteproperties.design_codes import NZS3101
from concreteproperties.post import si_kn_m, si_n_mm
from concreteproperties.results import (
    MomentCurvatureResults,
    MomentInteractionResults,
)


design_code = NZS3101()
concrete_40 = design_code.create_concrete_material(compressive_strength=40)
steel_300e = design_code.create_steel_material(steel_grade="300E")


print(concrete_40.name)
ult_flex = concrete_40.flexural_tensile_strength
print(f"Concrete Flexural Tensile Strength: {ult_flex:.2f} MPa")
ult_comp = concrete_40.ultimate_stress_strain_profile.get_ultimate_compressive_strain()
print(f"Ultimate Compressive Strain: {ult_comp:.4f}")
concrete_40.stress_strain_profile.plot_stress_strain(
    title="Concrete Serviceability Stress-Strain Profile",
    fmt="-r",
    eng=True,
    units=si_n_mm,
)
concrete_40.ultimate_stress_strain_profile.plot_stress_strain(
    title="Concrete Ultimate Stress-Strain Profile",
    fmt="-r",
    eng=True,
    units=si_n_mm,
)


print(steel_300e.name)
print(f"Density = {steel_300e.density} kg/mm^3")
ult_strain = steel_300e.stress_strain_profile.get_ultimate_tensile_strain()
print(f"Ultimate Tensile Strain = {ult_strain}")
print(f"Overstrength Factor = {steel_300e.phi_os}")
steel_300e.stress_strain_profile.plot_stress_strain(
    title="Steel Stress-Strain Profile",
    fmt="-r",
    eng=True,
    units=si_n_mm,
)


geom_beam = concrete_rectangular_section(
    b=500,
    d=800,
    dia_top=25,
    area_top=np.pi * 25**2 / 4,
    n_top=5,
    c_top=35 + 12,
    dia_bot=20,
    area_bot=np.pi * 20**2 / 4,
    n_bot=5,
    c_bot=35 + 12,
    n_circle=4,
    conc_mat=concrete_40,
    steel_mat=steel_300e,
)

conc_sec_beam = ConcreteSection(geom_beam)
conc_sec_beam.plot_section()
design_code.assign_concrete_section(
    concrete_section=conc_sec_beam, section_type="column"
)


gross_props = design_code.get_gross_properties()
transformed_props = design_code.get_transformed_gross_properties(
    elastic_modulus=concrete_40.stress_strain_profile.elastic_modulus
)
cracked_props = design_code.calculate_cracked_properties()

gross_props.print_results()
cracked_props.print_results()


M_star_pos = 280.0
M_star_neg = -442.0

f_ult_res_pos, ult_res_pos, phi_pos = design_code.ultimate_bending_capacity(
    theta=0, pphr_class="LDPR", analysis_type="nom_chk"
)
print("Positive flexure capacity:-")
print(f"M_star_pos = {M_star_pos} kN.m")
print(f"Mn_pos = {ult_res_pos.m_x / 1e6:.2f} kN.m")
print(f"phi = {phi_pos:.3f}")
print(f"phi.Mn_pos = {f_ult_res_pos.m_x / 1e6:.2f} kN.m")
dc_ratio_pos = M_star_pos * 1e6 / f_ult_res_pos.m_x
print(f"Demand/Capacity ratio = {abs(dc_ratio_pos):.3f}\n")

f_ult_res_neg, ult_res_neg, phi_neg = design_code.ultimate_bending_capacity(
    theta=np.pi,
    pphr_class="LDPR",
    analysis_type="nom_chk",
)
print("Negative flexure capacity:-")
print(f"M_star_neg = {M_star_neg} kN.m")
print(f"Mn_neg = {ult_res_neg.m_x / 1e6:.2f} kN.m")
print(f"phi = {phi_neg:.3f}")
print(f"phi.Mn_neg = {f_ult_res_neg.m_x / 1e6:.2f} kN.m")
dc_ratio_neg = M_star_neg * 1e6 / f_ult_res_neg.m_x
print(f"Demand/Capacity ratio = {abs(dc_ratio_neg):.3f}")


f_ult_res_pos_os, _, _ = design_code.ultimate_bending_capacity(
    theta=0, pphr_class="LDPR", analysis_type="os_chk"
)
print("Positive overstrength demand:-")
print(f"phi_o.Mo = {f_ult_res_pos_os.m_x / 1e6:.2f} kN.m")
os_ratio_pos = f_ult_res_pos_os.m_x / (M_star_pos * 1e6)
print(f"Actual positive flexure overstrength ratio = {abs(os_ratio_pos):.3f}\n")

f_ult_res_neg_os, _, _ = design_code.ultimate_bending_capacity(
    theta=np.pi, pphr_class="LDPR", analysis_type="os_chk"
)
print("Negative overstrength demand:-")
print(f"phi_o.Mo = {f_ult_res_neg_os.m_x / 1e6:.2f} kN.m")
os_ratio_neg = f_ult_res_neg_os.m_x / (M_star_neg * 1e6)
print(f"Actual negative flexure overstrength ratio = {abs(os_ratio_neg):.3f}")


steel_500e = design_code.create_steel_material(steel_grade="500E")


bar_dia = 20
area = np.pi * bar_dia**2 / 4

geom_col = concrete_rectangular_section(
    b=600,
    d=600,
    dia_top=bar_dia,
    area_top=area,
    n_top=4,
    c_top=35 + 12,
    dia_bot=bar_dia,
    area_bot=area,
    n_bot=4,
    c_bot=35 + 12,
    dia_side=bar_dia,
    area_side=area,
    n_side=2,
    c_side=35 + 12,
    n_circle=4,
    conc_mat=concrete_40,
    steel_mat=steel_500e,
)

conc_sec_col = ConcreteSection(geom_col)
conc_sec_col.plot_section()
design_code.assign_concrete_section(concrete_section=conc_sec_col)


M_o_T = -713.91 / 2
N_o_T = -165
M_o_C = 468.97 / 2
N_o_C = 1100

f_ult_res_t, _, _ = design_code.ultimate_bending_capacity(
    pphr_class="NDPR", analysis_type="cpe_chk", n_design=N_o_T * 1e3
)
print("Tension case capacity:-")
print(f"phi.Mn = {f_ult_res_t.m_x / 1e6:.2f} kN.m at axial load of {N_o_T:.2f} kN")
print(f"Mo = {M_o_T} kN.m")
col_ratio_t = M_o_T * 1e6 / f_ult_res_t.m_x
print(f"Actual design ratio = {abs(col_ratio_t):.3f}\n")

f_ult_res_c, _, _ = design_code.ultimate_bending_capacity(
    pphr_class="NDPR", analysis_type="cpe_chk", n_design=N_o_C * 1e3
)
print("Compression case capacity:-")
print(f"phi.Mn = {f_ult_res_c.m_x / 1e6:.2f} kN.m at axial load of {N_o_C:.2f} kN")
print(f"Mo = {M_o_C} kN.m")
col_ratio_c = M_o_C * 1e6 / f_ult_res_c.m_x
print(f"Actual design ratio = {abs(col_ratio_c):.3f}")


f_mi_res, mi_res, phis = design_code.moment_interaction_diagram(
    pphr_class="NDPR", analysis_type="cpe_chk", n_spacing=36, progress_bar=False
)


MomentInteractionResults.plot_multiple_diagrams(
    [f_mi_res, mi_res],
    ["Factored M/N", "Unfactored M/N"],
    fmt="or",
    render=False,
    moment="m_xy",
    units=si_kn_m,
)
plt.gca().lines[0].set_linestyle("solid")
plt.gca().lines[0].set_marker("")
plt.gca().lines[1].set_markersize(4)
plt.gca().lines[1].set_color("k")
plt.legend()
plt.tight_layout()
plt.show()


# design load cases
n_stars = [N_o_T * 1e3, N_o_C * 1e3]
m_stars = [-M_o_T * 1e6, M_o_C * 1e6]
marker_styles = ["s", "o"]
n_cases = len(n_stars)

# plot moment interaction diagram
ax = f_mi_res.plot_diagram(fmt="-r", render=False, units=si_kn_m)

# check to see if combination is within diagram and plot result
for idx in range(n_cases):
    case = f_mi_res.point_in_diagram(n=n_stars[idx], m=m_stars[idx])
    print("Case {num}: {status}".format(num=idx + 1, status="OK" if case else "FAIL"))
    ax.plot(
        m_stars[idx] / 1e6,
        n_stars[idx] / 1e3,
        "k" + marker_styles[idx],
        markersize=5,
        label=f"Case {idx + 1}",
    )

ax.legend()
plt.show()


# create biaxial bending diagram
f_bb_res1, phis1 = design_code.biaxial_bending_diagram(
    n_design=N_o_T * 1e3, n_points=24, progress_bar=False
)
f_bb_res2, phis2 = design_code.biaxial_bending_diagram(
    n_design=N_o_C * 1e3, n_points=24, progress_bar=False
)


# plot case 1
ax = f_bb_res1.plot_diagram(fmt="-r", render=False, units=si_kn_m)
ax.plot(M_o_T, 0, "sk")
plt.show()

# plot case 2
ax = f_bb_res2.plot_diagram(fmt="-r", render=False, units=si_kn_m)
ax.plot(M_o_C, 0, "ok")
plt.show()


# determine maximum compression load for the column section
max_comp = design_code.max_comp_strength(cpe_design=True)
max_ten = design_code.max_ten_strength()
steps_axial = 8
steps_moment = 12
# generate axial load list
n_design_list = np.linspace(-max_ten + 20000, max_comp, steps_axial)
theta_list = np.linspace(0.0, 2 * np.pi, steps_moment, False)

results_bb = []
results_mi = []
labels = []

for theta in theta_list:
    f_mi_res, _, _ = design_code.moment_interaction_diagram(
        pphr_class="NDPR", analysis_type="cpe_chk", theta=theta, progress_bar=False
    )
    results_mi.append(f_mi_res)

for n_design in n_design_list:
    f_bb_res, _ = design_code.biaxial_bending_diagram(
        pphr_class="NDPR",
        analysis_type="cpe_chk",
        n_design=n_design,
        n_points=24,
        progress_bar=False,
    )
    results_bb.append(f_bb_res)
    labels.append(f"N* = {n_design / 1e3}")

# plot all the M/N and M/M diagrams on one plot
fig = plt.figure(figsize=(16, 10))
ax = plt.axes(projection="3d")
n_scale = 1e-3
m_scale = 1e-6

for mi_res in results_mi:
    n_design, m_x_list = mi_res.get_results_lists(moment="m_x")
    _, m_y_list = mi_res.get_results_lists(moment="m_y")
    n_design = np.array(n_design) * n_scale
    m_x_list = np.array(m_x_list) * m_scale
    m_y_list = np.array(m_y_list) * m_scale

    ax.plot3D(m_x_list, m_y_list, n_design, "-k", linewidth=0.5)

for i, bb_res in enumerate(results_bb):
    m_x_list, m_y_list = bb_res.get_results_lists()
    m_x_list = np.array(m_x_list) * m_scale
    m_y_list = np.array(m_y_list) * m_scale

    n_design = np.array(n_design_list[i]) * n_scale
    ax.plot3D(m_x_list, m_y_list, n_design, "-r", linewidth=0.5)

ax.set_xlabel("Bending Moment $M_x$ (kNm)")
ax.set_ylabel("Bending Moment $M_y$ (kNm)")
ax.set_zlabel("Axial Force $N$ (kN)")

plt.tight_layout(pad=-10)
plt.show()


# create new materials overriding default ultimate strains with values appropriate for
# the moment-curvature analysis
steel_275 = design_code.create_steel_material(
    steel_grade="275", fracture_strain=min(0.06, (15 / 100) * 0.6)
)

# determine the concrete probable strength in compresison and tension
compressive_strength = 25
prob_tensile_strength = design_code.concrete_tensile_strength(
    compressive_strength=compressive_strength, prob_design=True
)
prob_compressive_strength = design_code.prob_compressive_strength(compressive_strength)

# create a probable strength concrete material with properties suitable for a
# moment-curvature analysis
concrete_25_prob = Concrete(
    name="Mander Concrete",
    density=2.3e-6,
    stress_strain_profile=ModifiedMander(
        elastic_modulus=design_code.e_conc(prob_compressive_strength),
        compressive_strength=prob_compressive_strength,
        tensile_strength=prob_tensile_strength,
        conc_tension=True,
        n_points=18,
    ),
    ultimate_stress_strain_profile=RectangularStressBlock(
        compressive_strength=prob_compressive_strength,
        alpha=design_code.alpha_1(prob_compressive_strength),
        gamma=design_code.beta_1(prob_compressive_strength),
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=prob_tensile_strength,
    colour="lightgrey",
)

concrete_25_prob.stress_strain_profile.plot_stress_strain(
    title="Mander Unconfined Stress-Strain Profile",
    fmt="-r",
    eng=True,
    units=si_n_mm,
)


print(steel_275.name)
print(f"Density = {steel_275.density} kg/mm^3")
print(
    f"Probable yield strength = {steel_275.stress_strain_profile.get_yield_strength()}"
    f" MPa"
)
steel_275.stress_strain_profile.plot_stress_strain(
    title="Steel Stress-Strain Profile", fmt="-r"
)


bar_dia = 28
area = np.pi * bar_dia**2 / 4

geom_beam = concrete_rectangular_section(
    b=400,
    d=600,
    dia_top=bar_dia,
    area_top=area,
    n_top=5,
    c_top=30 + 10,
    dia_bot=bar_dia,
    area_bot=area,
    n_bot=5,
    c_bot=30 + 10,
    n_circle=4,
    conc_mat=concrete_25_prob,
    steel_mat=steel_275,
)

conc_sec = ConcreteSection(geom_beam)
conc_sec.plot_section()
design_code.assign_concrete_section(concrete_section=conc_sec)


moment_curvature_results = conc_sec.moment_curvature_analysis(
    theta=0, kappa_inc=2.5e-7, progress_bar=False
)
fail_mat = moment_curvature_results.failure_geometry.material.name
print(f"The failure material is:-\n{fail_mat}")

MomentCurvatureResults.plot_results(
    moment_curvature_results,
    fmt="-r",
    eng=True,
    units=si_kn_m,
)
mcr = conc_sec.calculate_cracked_properties(theta=0).m_cr / 1e6
print(f"Cracking moment is M_cr = {mcr:.2f} kNm")


max_moment = max(moment_curvature_results.m_xy) * 1e-6
max_curvature = max(moment_curvature_results.kappa)
print(f"Maximum Moment = {max_moment:.2f} kN.m")
print(f"Maximum Curvature = {max_curvature:.8f} rads")


concrete_25 = design_code.create_concrete_material(compressive_strength=25)
steel_275 = design_code.create_steel_material(steel_grade="275")

bar_dia = 28
area = np.pi * bar_dia**2 / 4

geom_beam = concrete_rectangular_section(
    b=400,
    d=600,
    dia_top=bar_dia,
    area_top=area,
    n_top=5,
    c_top=30 + 10,
    dia_bot=bar_dia,
    area_bot=area,
    n_bot=5,
    c_bot=30 + 10,
    n_circle=4,
    conc_mat=concrete_25,
    steel_mat=steel_275,
)

conc_sec = ConcreteSection(geom_beam)
conc_sec.plot_section()
design_code.assign_concrete_section(concrete_section=conc_sec)


n_design = 0 * 1e3
f_ult_res, _, _ = design_code.ultimate_bending_capacity(
    pphr_class="NDPR", analysis_type="prob_chk", n_design=n_design
)

print("Probable Moment Capacity from ultimate strength check: -")
print(
    f"Mp = {f_ult_res.m_x / 1e6:.2f} kN.m at an axial load of {n_design / 1e3:.2f} kN\n"
)
print("Maximum Moment Capacity from moment-curvature analysis: -")
print(f"Maximum Moment = {max_moment:.2f} kN.m")


# section depth
h = 600

# determine neutral access depth at the probable moment capacity
c_prob = f_ult_res.d_n

# determine stress results for the reinforcement based on the probable strength
stress_res = design_code.concrete_section.calculate_ultimate_stress(
    f_ult_res
).lumped_reinforcement_forces

sum_force = 0
sum_force_lever = 0

# determine the effective depth d from extreme compressive fibre of the section
for bar in stress_res:
    force, d_x, d_y = bar
    if force <= 0:
        sum_force += force
        sum_force_lever += force * (h / 2 - d_y)

eff_depth = sum_force_lever / sum_force

# determine the probable curvature capacity
phi_cap = min(0.004 / c_prob, min(0.06, (15 / 100) * 0.6) / (eff_depth - c_prob))

print(f"Neutral axis depth at the probable capacity = {c_prob:.2f} mm")
print(f"Effective depth of tension reinforcement = {eff_depth:.2f} mm")
print(f"Probable Curvature Capacity = {phi_cap:.8f} rads")
print(f"Maximum Curvature from moment-curvature analysis = {max_curvature:.8f} rads")
print(f"Ratio of results = {phi_cap / max_curvature:.2f}")
