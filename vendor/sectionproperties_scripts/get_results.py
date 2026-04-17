# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/get_results.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import angle_section, rectangular_section

angle = angle_section(d=150, b=100, t=8, r_r=12, r_t=5, n_r=8)
plate = rectangular_section(d=12, b=125)
geom = angle + plate.shift_section(x_offset=-12.5, y_offset=-12)
geom.create_mesh(mesh_sizes=[10, 25])
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_frame_properties()
area = sec.get_area()
ixx_c, iyy_c, ixy_c = sec.get_ic()
phi = sec.get_phi()
j = sec.get_j()


print(f"Area = {area:.1f} mm2")
print(f"Ixx = {ixx_c:.3e} mm4")
print(f"Iyy = {iyy_c:.3e} mm4")
print(f"Ixy = {ixy_c:.3e} mm4")
print(f"Principal axis angle = {phi:.1f} deg")
print(f"Torsion constant = {j:.3e} mm4")


from sectionproperties.pre import Material

concrete = Material(
    name="Concrete",
    elastic_modulus=30.1e3,
    poissons_ratio=0.2,
    yield_strength=32,
    density=2.4e-6,
    color="lightgrey",
)
steel = Material(
    name="Steel",
    elastic_modulus=200e3,
    poissons_ratio=0.3,
    yield_strength=500,
    density=7.85e-6,
    color="grey",
)


from sectionproperties.pre.library import concrete_rectangular_section

geom = concrete_rectangular_section(
    d=600,
    b=300,
    dia_top=16,
    area_top=200,
    n_top=3,
    c_top=20,
    dia_bot=20,
    area_bot=310,
    n_bot=3,
    c_bot=30,
    n_circle=8,
    conc_mat=concrete,
    steel_mat=steel,
)

geom.create_mesh(mesh_sizes=2500)
sec = Section(geometry=geom)
sec.plot_mesh()


props = sec.calculate_frame_properties()


sec.get_ic()


# get relevant modulus weighted properties
eixx, _, _ = sec.get_eic()
ea = sec.get_ea()
ej = sec.get_ej()

# print results
print(f"Axial rigidity (E.A): {ea:.3e} N")
print(f"Flexural rigidity (E.I): {eixx:.3e} N.mm2")

# note we are usually interested in G.J not E.J
# geometric analysis required for effective material properties
sec.calculate_geometric_properties()
gj = sec.get_g_eff() / sec.get_e_eff() * ej
print(f"Torsional rigidity (G.J): {gj:.3e} N.mm2")


print(f"E.I = {eixx:.3e} N.mm2")
print(f"I = {sec.get_eic(e_ref=concrete)[0]:.3e} mm4")
print(f"I = {sec.get_eic(e_ref=30.1e3)[0]:.3e} mm4")


print(f"I_rect = {300 * 600**3 / 12:.3e} mm4")
