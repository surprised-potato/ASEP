# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/biaxial_bending.html

import numpy as np
from sectionproperties.pre.library import rectangular_section

from concreteproperties import (
    Concrete,
    ConcreteLinear,
    ConcreteSection,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
    add_bar_rectangular_array,
)
from concreteproperties.post import si_kn_m
from concreteproperties.results import BiaxialBendingResults


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


col = rectangular_section(d=350, b=600, material=concrete)

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

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


bb_res = conc_sec.biaxial_bending_diagram(n_points=24, progress_bar=False)


bb_res.plot_diagram(eng=True, units=si_kn_m)


bb_res = conc_sec.biaxial_bending_diagram(n=1000e3, n_points=24, progress_bar=False)
bb_res.plot_diagram(eng=True, units=si_kn_m)


mi_x = conc_sec.moment_interaction_diagram(progress_bar=False)
mi_y = conc_sec.moment_interaction_diagram(theta=np.pi / 2, progress_bar=False)
mi_x.plot_diagram(eng=True)
mi_y.plot_diagram(moment="m_y", eng=True)
print(f"Decompression point for M_x is N = {mi_x.results[1].n / 1e3:.2f} kN")
print(f"Decompression point for M_y is N = {mi_y.results[1].n / 1e3:.2f} kN")


n_list = np.linspace(0, 7400e3, 5)
biaxial_results = [
    conc_sec.biaxial_bending_diagram(n=n, n_points=24, progress_bar=False)
    for n in n_list
]


BiaxialBendingResults.plot_multiple_diagrams_3d(
    biaxial_results,
    eng=True,
    units=si_kn_m,
)


BiaxialBendingResults.plot_multiple_diagrams_2d(
    biaxial_results,
    fmt="o-",
    eng=True,
    units=si_kn_m,
)


labels = [f"N = {bb_res.n / 1e3:.0f} kN" for bb_res in biaxial_results[::2]]

ax = BiaxialBendingResults.plot_multiple_diagrams_2d(
    biaxial_results[::2],
    fmt="-",
    labels=labels,
    units=si_kn_m,
)
