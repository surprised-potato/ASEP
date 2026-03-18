# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/stress_analysis.html

import numpy as np
from rich.pretty import pprint
from sectionproperties.pre.library import concrete_circular_section

from concreteproperties import (
    Concrete,
    ConcreteSection,
    EurocodeNonLinear,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
)
from concreteproperties.post import si_kn_m, si_n_mm


concrete = Concrete(
    name="40 MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=EurocodeNonLinear(
        elastic_modulus=32.8e3,
        ultimate_strain=0.0035,
        compressive_strength=40,
        compressive_strain=0.0023,
        tensile_strength=3.8,
        tension_softening_stiffness=10e3,
    ),
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


geom = concrete_circular_section(
    d=600,
    area_conc=np.pi * 600 * 600 / 4,
    n_conc=24,
    dia_bar=20,
    area_bar=310,
    n_bar=10,
    cover=45,
    conc_mat=concrete,
    steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


uncr_stress_res_1 = conc_sec.calculate_uncracked_stress(m_x=50e6)
uncr_stress_res_2 = conc_sec.calculate_uncracked_stress(m_x=25e6, m_y=35e6, n=200e3)


uncr_stress_res_1.plot_stress(units=si_n_mm)


uncr_stress_res_2.plot_stress(eng=True, units=si_kn_m)


cracked_res = conc_sec.calculate_cracked_properties(theta=0)
print(f"M_cr = {cracked_res.m_cr / 1e6:.2f} kN.m")
print(f"d_n,c = {cracked_res.d_nc:.2f} mm")


m_ext = 150e6
cracked_stress_res = conc_sec.calculate_cracked_stress(
    cracked_results=cracked_res, m=m_ext
)
cracked_stress_res.plot_stress()


for idx, an_sec in enumerate(cracked_stress_res.concrete_analysis_sections):
    # Label section and plot section mesh
    print(f"Analysis Section {idx + 1}")
    an_sec.plot_mesh()

    # get concrete results
    sigs_conc = cracked_stress_res.concrete_stresses[idx]
    f_conc = cracked_stress_res.concrete_forces[idx][0]
    d_x_conc = cracked_stress_res.concrete_forces[idx][1]
    d_y_conc = cracked_stress_res.concrete_forces[idx][2]
    m_x_conc = f_conc * d_y_conc
    m_y_conc = f_conc * d_x_conc
    m_conc = np.sqrt(m_x_conc * m_x_conc + m_y_conc * m_y_conc)

    # print results
    print("Concrete Stresses:")
    pprint(sigs_conc)
    print("Concrete Net Force & Lever Arm:")
    print(f"F_c = {f_conc / 1e3:.2f} kN")
    print(f"d_x_n = {d_x_conc:.2f} mm")
    print(f"d_y_n = {d_y_conc:.2f} mm")
    print(f"M_x_c = {m_x_conc / 1e6:.2f} kN.m")
    print(f"M_y_c = {m_y_conc / 1e6:.2f} kN.m")
    print(f"M_c = {m_conc / 1e6:.2f} kN.m")


from rich.console import Console
from rich.table import Table

# store forces & moments for later
forces = []
moments_x = []

# create a Rich table for pretty printing
table = Table(title="Reinforcement Results")
table.add_column("Bar No.", justify="center", style="cyan", no_wrap=True)
table.add_column("Location (x, y) (mm)", justify="center", style="green")
table.add_column("Stress (MPa)", justify="center", style="green")
table.add_column("Force (kN)", justify="center", style="green")
table.add_column("Lever Arm (mm)", justify="center", style="green")
table.add_column("Moment (kN.m)", justify="center", style="green")

for idx, reinf_geom in enumerate(cracked_stress_res.lumped_reinforcement_geometries):
    # get the reinforcement results
    centroid = reinf_geom.calculate_centroid()
    stress = cracked_stress_res.lumped_reinforcement_stresses[idx]
    strain = cracked_stress_res.lumped_reinforcement_strains[idx]
    force, d_x, d_y = cracked_stress_res.lumped_reinforcement_forces[idx]

    # calculate the moment each bar creates and store the results
    moment_x = force * d_y
    forces.append(force)
    moments_x.append(moment_x)

    # print compression or tension
    t_or_c = "C" if strain > 0 else "T"

    table.add_row(
        f"{idx + 1}",
        f"({centroid[0]:.1f}, {centroid[1]:.1f})",
        f"{abs(stress):.1f} ({t_or_c})",
        f"{abs(force) / 1e3:.1f}",
        f"{d_y:.1f}",
        f"{moment_x / 1e6:.2f}",
    )

console = Console()
console.print(table)


# sum of forces
int_force = sum(forces) + f_conc
print(f"Sum of Internal Forces: {int_force / 1e3:.0f} kN")

# sum of moments
int_moment = sum(moments_x) + m_conc
print(f"Sum of Internal Moments: {int_moment / 1e6:.0f} kN.m")
print(f"External Moment: {m_ext / 1e6:.0f} kN.m")


mk_res = conc_sec.moment_curvature_analysis(kappa_inc=2.5e-7, progress_bar=False)


mk_res.plot_results(eng=True, units=si_kn_m)


# create a list of inputs (either moments [m] or curvatures [k])
stress_inputs = [
    {"m_or_k": "m", "val": 50e6},
    {"m_or_k": "m", "val": cracked_res.m_cr},
    {"m_or_k": "k", "val": 7.5e-07},
    {"m_or_k": "k", "val": 1.15e-06},
    {"m_or_k": "k", "val": 2.15e-06},
    {"m_or_k": "m", "val": 250e6},
    {"m_or_k": "m", "val": 300e6},
    {"m_or_k": "m", "val": 360e6},
]


# loop through each input
for s_in in stress_inputs:
    # determine if the input is a moment or curvature
    if s_in["m_or_k"] == "m":
        m_stress = s_in["val"]
        service_stress_res = conc_sec.calculate_service_stress(
            moment_curvature_results=mk_res, m=m_stress
        )
    elif s_in["m_or_k"] == "k":
        service_stress_res = conc_sec.calculate_service_stress(
            moment_curvature_results=mk_res, m=None, kappa=s_in["val"]
        )
        m_stress = service_stress_res.sum_moments()[2]

    # create plot title and plot stress
    label = f"Moment = {m_stress / 1e6:.0f} kN.m"
    service_stress_res.plot_stress(title=label, units=si_n_mm)


mi_res = conc_sec.moment_interaction_diagram(progress_bar=False)
mi_res.plot_diagram(units=si_kn_m)


ultimate_res_pure = conc_sec.ultimate_bending_capacity()
ultimate_res_bal = conc_sec.ultimate_bending_capacity(n=3500e3)
ultimate_res_decomp = conc_sec.ultimate_bending_capacity(n=9000e3)


ultimate_stress_pure = conc_sec.calculate_ultimate_stress(
    ultimate_results=ultimate_res_pure
)
ultimate_stress_bal = conc_sec.calculate_ultimate_stress(
    ultimate_results=ultimate_res_bal
)
ultimate_stress_decomp = conc_sec.calculate_ultimate_stress(
    ultimate_results=ultimate_res_decomp
)


ultimate_stress_pure.plot_stress(title="Pure Bending", units=si_n_mm)
ultimate_stress_bal.plot_stress(title="Balanced", units=si_n_mm)
ultimate_stress_decomp.plot_stress(title="Decompression", units=si_n_mm)
