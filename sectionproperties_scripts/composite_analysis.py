# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/materials/composite_analysis.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import rectangular_section

rect_geom = rectangular_section(d=100, b=50)
rect_geom.material


rect_geom.create_mesh(mesh_sizes=10)  # create mesh
rect_sec = Section(geometry=rect_geom)
rect_sec.calculate_geometric_properties()
ixx, iyy, ixy = rect_sec.get_ic()  # get second moments of area
print(f"Ixx = {ixx:.5e} mm4")


from sectionproperties.pre import Material

# assign steel to the geometry
steel = Material(
    name="Steel",
    elastic_modulus=200e3,
    poissons_ratio=0.3,
    density=7.85e-6,
    yield_strength=500,
    color="grey",
)
rect_geom.material = steel

# recreate mesh and section
rect_geom.create_mesh(mesh_sizes=10)
rect_sec = Section(geometry=rect_geom)
rect_sec.calculate_geometric_properties()


ixx, iyy, ixy = rect_sec.get_ic()  # get second moments of area


# get modulus weighted second moments of area
eixx, eiyy, eixy = rect_sec.get_eic()
print(f"E.Ixx = {eixx:.5e} N.mm2")

# use reference elastic modulus to get transformed properties
ixx, iyy, ixy = rect_sec.get_eic(e_ref=steel)
print(f"Ixx = {ixx:.5e} mm4")


# create the steel material
steel = Material(
    name="Steel",
    elastic_modulus=200e3,
    poissons_ratio=0.3,
    density=7.85e-6,
    yield_strength=500,
    color="grey",
)

# create the timber material
timber = Material(
    name="Timber",
    elastic_modulus=8e3,
    poissons_ratio=0.35,
    yield_strength=20,
    density=0.78e-6,
    color="burlywood",
)


from sectionproperties.pre.library import i_section

# universal steel beam
ub = i_section(d=304, b=165, t_f=10.2, t_w=6.1, r=11.4, n_r=8, material=steel)

# timber floor panel
panel = rectangular_section(d=100, b=600, material=timber)
panel = panel.align_center(align_to=ub).align_to(other=ub, on="top")

# combine geometry
geom = ub + panel


# 10 mm2 mesh for UB, 500 mm2 mesh for timber
geom.create_mesh(mesh_sizes=[10, 500])
sec = Section(geometry=geom)
sec.plot_mesh()


sec.calculate_geometric_properties()
sec.calculate_warping_properties()
sec.calculate_plastic_properties()


sec.plot_centroids()


sec.display_results()


ixx_timber, _, _ = sec.get_eic(e_ref=timber)
ixx_steel, _, _ = sec.get_eic(e_ref=steel)
print(f"Ixx,t = {ixx_timber:.3e} mm4")
print(f"Ixx,s = {ixx_steel:.3e} mm4")


mp_xx, _ = sec.get_mp()
print(f"Mp = {mp_xx / 1e6:.1f} kN.m")


stress = sec.calculate_stress(n=-100e3, mxx=-120e6, vy=-75e3)


stress.plot_stress(stress="m_zz")


stress.plot_stress(stress="vm")


stress.plot_stress(stress="vm", material_list=[timber])
