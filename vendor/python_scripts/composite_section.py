# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/composite_section.html

import numpy as np
from sectionproperties.pre.library import (
    circular_section_by_area,
    concrete_circular_section,
    i_section,
    rectangular_section,
)

import concreteproperties.results as res
from concreteproperties import (
    Concrete,
    ConcreteLinearNoTension,
    ConcreteSection,
    RectangularStressBlock,
    Steel,
    SteelBar,
    SteelElasticPlastic,
    add_bar_circular_array,
    add_bar_rectangular_array,
)
from concreteproperties.post import si_kn_m, si_n_mm


concrete = Concrete(
    name="50 MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=ConcreteLinearNoTension(
        elastic_modulus=34.8e3,
        ultimate_strain=0.003,
        compressive_strength=0.9 * 50,
    ),
    ultimate_stress_strain_profile=RectangularStressBlock(
        compressive_strength=50,
        alpha=0.775,
        gamma=0.845,
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=4.2,
    colour="lightgrey",
)

steel_300 = Steel(
    name="300 MPa Structural Steel",
    density=7.85e-6,
    stress_strain_profile=SteelElasticPlastic(
        yield_strength=300,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="tan",
)

steel_bar = SteelBar(
    name="500 MPa Steel Bar",
    density=7.85e-6,
    stress_strain_profile=SteelElasticPlastic(
        yield_strength=500,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="grey",
)


# create 500 square concrete
conc = rectangular_section(d=500, b=500, material=concrete)

# create 310UC97 and centre to column
uc = i_section(
    d=308,
    b=305,
    t_f=15.4,
    t_w=9.9,
    r=16.5,
    n_r=3,
    material=steel_300,
).align_center(align_to=conc)

# cut hole in concrete for UC then add UC
geom = conc - uc + uc

# add 12N20 reinforcing bars
geom = add_bar_rectangular_array(
    geometry=geom,
    area=310,
    material=steel_bar,
    n_x=4,
    x_s=132,
    n_y=4,
    y_s=132,
    anchor=(52, 52),
    exterior_only=True,
)

# create concrete section and plot
conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


el_stress = conc_sec.calculate_uncracked_stress(m_x=100e6)
el_stress.plot_stress(units=si_n_mm)


cr_res = conc_sec.calculate_cracked_properties()
cr_stress = conc_sec.calculate_cracked_stress(cracked_results=cr_res, m=500e6)
cr_stress.plot_stress(units=si_n_mm)


mk_res = conc_sec.moment_curvature_analysis(kappa_inc=2.5e-6, progress_bar=False)


mk_res.plot_results(fmt="kx-", eng=True, units=si_kn_m)


serv_stress = conc_sec.calculate_service_stress(
    moment_curvature_results=mk_res, m=None, kappa=2e-5
)
serv_stress.plot_stress(units=si_n_mm)


ult_res_x = conc_sec.ultimate_bending_capacity()
ult_res_y = conc_sec.ultimate_bending_capacity(theta=np.pi / 2)
ult_res_x.print_results(units=si_kn_m)
ult_res_y.print_results(units=si_kn_m)


mi_res = conc_sec.moment_interaction_diagram(progress_bar=False)
mi_res.plot_diagram(units=si_kn_m)


bb_res = conc_sec.biaxial_bending_diagram(n_points=24, progress_bar=False)
bb_res.plot_diagram(units=si_kn_m)


ult_stress_x = conc_sec.calculate_ultimate_stress(ult_res_x)
ult_stress_y = conc_sec.calculate_ultimate_stress(ult_res_y)
ult_stress_x.plot_stress(units=si_n_mm)
ult_stress_y.plot_stress(units=si_n_mm)


steel_350 = Steel(
    name="350 MPa Structural Steel",
    density=7.85e-6,
    stress_strain_profile=SteelElasticPlastic(
        yield_strength=350,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="tan",
)


# create outer diameter of steel column
steel_col = circular_section_by_area(
    area=np.pi * 323.9**2 / 4,
    n=24,
    material=steel_350,
)

# create inner diameter of steel column, concrete filled
inner_conc = circular_section_by_area(
    area=np.pi * (323.9 - 2 * 12.7) ** 2 / 4,
    n=32,
    material=concrete,
)

# create composite geometry
geom_comp = steel_col - inner_conc + inner_conc

# add reinforcement
r_bars = 323.9 / 2 - 12.7 - 30 - 10  # 30 mm cover from inside of steel

geom_comp = add_bar_circular_array(
    geometry=geom_comp,
    area=310,
    material=steel_bar,
    n_bar=6,
    r_array=r_bars,
)

# create concrete section and plot
conc_sec_comp = ConcreteSection(geom_comp)
conc_sec_comp.plot_section()

# create 350 diameter column for comparison
geom_conc = concrete_circular_section(
    d=350,
    area_conc=np.pi * 350**2 / 4,
    n_conc=24,
    dia_bar=20,
    area_bar=310,
    n_bar=6,
    cover=30 + 12,  # 30 mm cover + 12 mm tie
    conc_mat=concrete,
    steel_mat=steel_bar,
)

# create concrete section and plot
conc_sec_conc = ConcreteSection(geom_conc)
conc_sec_conc.plot_section()


el_stress_comp = conc_sec_comp.calculate_uncracked_stress(m_x=10e6)
el_stress_conc = conc_sec_conc.calculate_uncracked_stress(m_x=10e6)
el_stress_comp.plot_stress(units=si_n_mm)
el_stress_conc.plot_stress(units=si_n_mm)


cr_res_comp = conc_sec_comp.calculate_cracked_properties()
cr_res_conc = conc_sec_conc.calculate_cracked_properties()

cr_stress_comp = conc_sec_comp.calculate_cracked_stress(
    cracked_results=cr_res_comp, m=50e6
)
cr_stress_conc = conc_sec_conc.calculate_cracked_stress(
    cracked_results=cr_res_conc, m=50e6
)
cr_stress_comp.plot_stress(units=si_n_mm)
cr_stress_conc.plot_stress(units=si_n_mm)


mk_res_comp = conc_sec_comp.moment_curvature_analysis(
    kappa_inc=2.5e-6, progress_bar=False
)
mk_res_conc = conc_sec_conc.moment_curvature_analysis(
    kappa_inc=2.5e-6, progress_bar=False
)


res.MomentCurvatureResults.plot_multiple_results(
    moment_curvature_results=[mk_res_comp, mk_res_conc],
    labels=["Composite", "Concrete"],
    fmt="x-",
    eng=True,
    units=si_kn_m,
)


mi_res_comp = conc_sec_comp.moment_interaction_diagram(progress_bar=False)
mi_res_conc = conc_sec_conc.moment_interaction_diagram(progress_bar=False)
res.MomentInteractionResults.plot_multiple_diagrams(
    moment_interaction_results=[mi_res_comp, mi_res_conc],
    labels=["Composite", "Concrete"],
    fmt="x-",
    units=si_kn_m,
)


concrete = Concrete(
    name="32 MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=ConcreteLinearNoTension(
        elastic_modulus=30.1e3,
        ultimate_strain=0.003,
        compressive_strength=0.9 * 32,
    ),
    ultimate_stress_strain_profile=RectangularStressBlock(
        compressive_strength=32,
        alpha=0.802,
        gamma=0.89,
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=3.4,
    colour="lightgrey",
)


# create 530UB92
ub = i_section(
    d=533,
    b=209,
    t_f=15.6,
    t_w=10.2,
    r=14,
    n_r=3,
    material=steel_300,
)

# create concrete slab, centre on top of UB
conc_slab = (
    rectangular_section(
        d=120,
        b=1200,
        material=concrete,
    )
    .align_center(align_to=ub)
    .align_to(other=ub, on="top")
)

# as there is no overlapping geometry, we can simply add the two sections together
geom = ub + conc_slab

# create concrete section and plot
conc_sec = ConcreteSection(geom, geometric_centroid_override=True)
conc_sec.plot_section()


cx_geom = conc_sec.moment_centroid[0]
cy_geom = conc_sec.moment_centroid[1]
cx_gross = conc_sec.gross_properties.cx_gross
cy_gross = conc_sec.gross_properties.cy_gross
print(f"cx_geom = {cx_geom:.2f}; cy_geom = {cy_geom:.2f}")
print(f"cx_gross = {cx_gross:.2f}; cy_gross = {cy_gross:.2f}")


mk_res = conc_sec.moment_curvature_analysis(kappa_inc=1e-6, progress_bar=False)


mk_res.plot_results(eng=True, units=si_kn_m)


el_stress = conc_sec.calculate_service_stress(moment_curvature_results=mk_res, m=500e6)
yield_stress = conc_sec.calculate_service_stress(
    moment_curvature_results=mk_res, m=900e6
)
ult_stress = conc_sec.calculate_service_stress(
    moment_curvature_results=mk_res, m=1150e6
)


el_stress.plot_stress(units=si_n_mm)
yield_stress.plot_stress(units=si_n_mm)
ult_stress.plot_stress(units=si_n_mm)


ult_res = conc_sec.ultimate_bending_capacity()
ult_res.print_results(units=si_kn_m)
