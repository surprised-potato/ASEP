# Script content scraped from: https://concrete-properties.readthedocs.io/en/stable/examples/ultimate_bending.html

import numpy as np
from sectionproperties.pre.library import rectangular_section, triangular_section

import concreteproperties.stress_strain_profile as ssp
from concreteproperties import (
    Concrete,
    ConcreteSection,
    SteelBar,
    add_bar_rectangular_array,
)
from concreteproperties.post import si_kn_m, si_n_mm


concrete = Concrete(
    name="50 MPa Concrete",
    density=2.4e-6,
    stress_strain_profile=ssp.ConcreteLinear(elastic_modulus=34.8e3),
    ultimate_stress_strain_profile=ssp.RectangularStressBlock(
        compressive_strength=50,
        alpha=0.775,
        gamma=0.845,
        ultimate_strain=0.003,
    ),
    flexural_tensile_strength=4.2,
    colour="lightgrey",
)

steel = SteelBar(
    name="500 MPa Steel",
    density=7.85e-6,
    stress_strain_profile=ssp.SteelElasticPlastic(
        yield_strength=500,
        elastic_modulus=200e3,
        fracture_strain=0.05,
    ),
    colour="grey",
)


# construct box by subtracting an inner rectangle from an outer rectangle
outer = rectangular_section(d=1200, b=900, material=concrete)
inner = rectangular_section(d=900, b=600).align_center(align_to=outer)
box = outer - inner

# generate four chamfers
chamfer1 = (
    triangular_section(b=50, h=50, material=concrete)
    .align_to(other=inner, on="left", inner=True)
    .align_to(other=inner, on="bottom", inner=True)
)
chamfer2 = chamfer1.mirror_section(axis="y", mirror_point=(450, 600))
chamfer3 = chamfer1.mirror_section(axis="x", mirror_point=(450, 600))
chamfer4 = chamfer2.mirror_section(axis="x", mirror_point=(450, 600))

# add chamfers to box
geom = box + chamfer1 + chamfer2 + chamfer3 + chamfer4

# add bottom bars
geom = add_bar_rectangular_array(
    geometry=geom,
    area=620,
    material=steel,
    n_x=9,
    x_s=750 / 8,
    anchor=(75, 75),
)

# add top bars
geom = add_bar_rectangular_array(
    geometry=geom,
    area=310,
    material=steel,
    n_x=9,
    x_s=750 / 8,
    anchor=(75, 1125),
)

# add side bars
geom = add_bar_rectangular_array(
    geometry=geom,
    area=200,
    material=steel,
    n_x=2,
    x_s=750,
    n_y=6,
    y_s=150,
    anchor=(75, 225),
)

conc_sec = ConcreteSection(geom)
conc_sec.plot_section()


sag_res = conc_sec.ultimate_bending_capacity()
hog_res = conc_sec.ultimate_bending_capacity(theta=np.pi)
weak_res = conc_sec.ultimate_bending_capacity(theta=np.pi / 2)


sag_res.print_results(units=si_kn_m)


si_n_mm.radians = False  # display angles in degrees
hog_res.print_results(units=si_n_mm)


weak_res.print_results()


print(f"M_x+ = {sag_res.m_xy / 1e6:.2f} kN.m")
print(f"M_x- = {hog_res.m_xy / 1e6:.2f} kN.m")
print(f"M_y = {weak_res.m_xy / 1e6:.2f} kN.m")


n = 5000e3
sag_axial_res = conc_sec.ultimate_bending_capacity(n=n)
hog_axial_res = conc_sec.ultimate_bending_capacity(theta=np.pi, n=n)
weak_axial_res = conc_sec.ultimate_bending_capacity(theta=np.pi / 2, n=n)


msg_sag = f"M_x+ = {sag_axial_res.m_xy / 1e6:.1f} kN.m "
msg_sag += f"with N = {sag_axial_res.n / 1e3:.0f} kN"
msg_hog = f"M_x- = {hog_axial_res.m_xy / 1e6:.1f} kN.m "
msg_hog += f"with N = {hog_axial_res.n / 1e3:.0f} kN"
msg_weak = f"M_y = {weak_axial_res.m_xy / 1e6:.1f} kN.m "
msg_weak += f"with N = {weak_axial_res.n / 1e3:.0f} kN"

print(msg_sag)
print(msg_hog)
print(msg_weak)
