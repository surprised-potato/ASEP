# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/moment_interaction.html

import numpy as np
from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties import (
    Concrete,
    ConcreteLinear,
    ConcreteSection,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
)
from concreteproperties.post import si_kn_m, si_n_mm
from concreteproperties.results import MomentInteractionResults


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


geom = concrete_rectangular_section(
    b=400,
    d=600,
    dia_top=20,
    area_top=310,
    n_top=3,
    c_top=30,
    dia_bot=24,
    area_bot=450,
    n_bot=3,
    c_bot=30,
    conc_mat=concrete,
    steel_mat=steel,
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


mi_res = conc_sec.moment_interaction_diagram(progress_bar=False)


mi_res.plot_diagram(eng=True, units=si_n_mm)


mi_res = conc_sec.moment_interaction_diagram(theta=np.pi / 2, progress_bar=False)
mi_res.plot_diagram(moment="m_y", units=si_kn_m)


# create lists to hold results and labels
mi_results = []
labels = []

# create four different sections with increasing reinforcement
# and peform a moment interaction analysis
for idx in range(4):
    geom = concrete_rectangular_section(
        b=400,
        d=600,
        dia_top=16,
        area_top=200 * (idx + 1),
        n_top=6,
        c_top=66,
        dia_bot=16,
        area_bot=200 * (idx + 1),
        n_bot=6,
        c_bot=66,
        conc_mat=concrete,
        steel_mat=steel,
    )

    conc_sec = ConcreteSection(geom)
    mi_results.append(conc_sec.moment_interaction_diagram(progress_bar=False))
    labels.append(f"p = {0.01 * (idx + 1)}")


# plot all the diagrams on one image
MomentInteractionResults.plot_multiple_diagrams(
    moment_interaction_results=mi_results,
    labels=labels,
    fmt="-",
    units=si_kn_m,
)


geom = concrete_rectangular_section(
    b=400,
    d=600,
    dia_top=20,
    area_top=310,
    n_top=3,
    c_top=30,
    dia_bot=24,
    area_bot=450,
    n_bot=3,
    c_bot=30,
    conc_mat=concrete,
    steel_mat=steel,
)
conc_sec = ConcreteSection(geom)

mi_res_pos = conc_sec.moment_interaction_diagram(progress_bar=False)
mi_res_neg = conc_sec.moment_interaction_diagram(theta=np.pi, progress_bar=False)

MomentInteractionResults.plot_multiple_diagrams(
    moment_interaction_results=[mi_res_pos, mi_res_neg],
    labels=["Positive", "Negative"],
    fmt="-",
    eng=True,
    units=si_n_mm,
)


mi_res = conc_sec.moment_interaction_diagram(
    limits=[
        ("kappa0", 0.0),
        ("d_n", 1e-6),
    ],
    control_points=[
        ("D", 1.0),
        ("fy", 0.0),
        ("fy", 0.5),
        ("fy", 1.0),
        ("d_n", 200.0),
        ("N", 0.0),
    ],
    labels=["NA", "I", "C", "D", "E", "F", "G", "H"],
    n_spacing=36,
    max_comp=6.8e6,
    max_comp_labels=["A", "B"],
    progress_bar=False,
)


import matplotlib.pyplot as plt

ax = mi_res.plot_diagram(
    fmt="-kx",
    labels=True,
    label_offset=True,
    units=si_kn_m,
    render=False,
)

# reset axis limits to ensure labels are within plot
ax.set_xlim(-20, 850)
ax.set_ylim(-3000, 9000)
plt.show()
