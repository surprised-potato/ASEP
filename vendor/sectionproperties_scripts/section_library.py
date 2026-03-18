# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/section_library.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import circular_section


geom = circular_section(d=50, n=64)
geom.plot_geometry()


geom.create_mesh(mesh_sizes=[2.5])
sec = Section(geometry=geom)
sec.display_mesh_info()
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()
sec.calculate_plastic_properties()


sec.display_results()


ixx_c, iyy_c, ixy_c = sec.get_ic()
j = sec.get_j()
print(f"Ixx + Iyy + Ixy = {ixx_c + iyy_c + ixy_c:.3f}")
print(f"J = {j:.3f}")


from sectionproperties.pre.library import tapered_flange_channel


geom = tapered_flange_channel(
    d=10,
    b=3.5,
    t_f=0.575,
    t_w=0.475,
    r_r=0.575,
    r_f=0.4,
    alpha=8,
    n_r=16,
)


geom.create_mesh(mesh_sizes=0.05)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


sec.plot_centroids()


from sectionproperties.analysis import Section
from sectionproperties.pre import Material
from sectionproperties.pre.library import clt_rectangular_section


timber0 = Material(
    name="Timber0",
    elastic_modulus=9.5e3,
    poissons_ratio=0.35,
    density=4.4e-7,
    yield_strength=5.5,
    color="burlywood",
)

timber90 = Material(
    name="Timber90",
    elastic_modulus=317,
    poissons_ratio=0.35,
    density=4.4e-7,
    yield_strength=5.5,
    color="orange",
)


geom_maj = clt_rectangular_section(
    d=[40, 40, 40], layer_mat=[timber0, timber90, timber0], b=1000
)


geom_maj.create_mesh(mesh_sizes=[200])
sec_maj = Section(geometry=geom_maj)
sec_maj.plot_mesh()


sec_maj.calculate_geometric_properties()


ei_maj = sec_maj.get_eic(e_ref=timber0)
print(f"I_eff,x,major = {ei_maj[0]:.3e} mm4")


geom_min = clt_rectangular_section(
    d=[40, 40, 40], layer_mat=[timber90, timber0, timber90], b=1000
)


geom_min.create_mesh(mesh_sizes=[200])
sec_min = Section(geometry=geom_min)
sec_min.plot_mesh()


sec_min.calculate_geometric_properties()


ei_min = sec_min.get_eic(e_ref=timber0)
print(f"I_eff,x,minor = {ei_min[0]:.3e} mm4")


from sectionproperties.pre import Material
from sectionproperties.pre.library import concrete_rectangular_section


# define the concrete material
concrete = Material(
    name="Concrete",
    elastic_modulus=30.1e3,
    poissons_ratio=0.2,
    density=2.4e-6,
    yield_strength=32,
    color="lightgrey",
)

# define the steel material
steel = Material(
    name="Steel",
    elastic_modulus=200e3,
    poissons_ratio=0.3,
    yield_strength=500,
    density=7.85e-6,
    color="grey",
)

# create the geometry
geom = concrete_rectangular_section(
    d=600,
    b=300,
    dia_top=16,
    area_top=200,
    n_top=3,
    c_top=32,
    dia_bot=20,
    area_bot=310,
    n_bot=3,
    c_bot=42,
    dia_side=12,
    area_side=110,
    n_side=3,
    c_side=57,
    n_circle=16,
    conc_mat=concrete,
    steel_mat=steel,
)


geom.create_mesh(mesh_sizes=[200])
sec = Section(geometry=geom)
sec.plot_mesh()


sec.calculate_geometric_properties()


ei = sec.get_eic(e_ref=concrete)
print(f"I_eff = {ei[0]:.3e} mm4")
print(f"I_rec = {(300 * 600**3 / 12):.3e} mm4")
