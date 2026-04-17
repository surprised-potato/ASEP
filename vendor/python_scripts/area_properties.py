# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/area_properties.html

from sectionproperties.pre.library import concrete_rectangular_section

from concreteproperties import (
    Concrete,
    ConcreteLinear,
    ConcreteSection,
    RectangularStressBlock,
    SteelBar,
    SteelElasticPlastic,
)


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
    d=600,
    b=400,
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


gross_props = conc_sec.get_gross_properties()
gross_props.print_results()


transformed_props = conc_sec.get_transformed_gross_properties(elastic_modulus=30.1e3)
transformed_props.print_results()
