# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/materials/assign_materials.html

from sectionproperties.pre import Material


steel = Material(
    name="Steel",
    elastic_modulus=200e3,  # N/mm^2 (MPa)
    poissons_ratio=0.3,  # unitless
    density=7.85e-6,  # kg/mm^3
    yield_strength=500,  # N/mm^2 (MPa)
    color="grey",
)


from shapely import Polygon

from sectionproperties.analysis import Section
from sectionproperties.pre import Geometry

# assign steel to a shapely polygon
poly = Polygon([(0, 0), (5, 2), (3, 7), (1, 6)])
geom = Geometry(geom=poly, material=steel)
geom.create_mesh(mesh_sizes=1)
Section(geometry=geom).plot_mesh()


# create list of points, facets and holes
points = [(0, 0), (10, 5), (15, 15), (5, 10), (6, 6), (9, 7), (7, 9)]
facets = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 4)]
control_points = [(4, 4)]
holes = [(7, 7)]

# create geometry object, specifying material
geom = Geometry.from_points(
    points=points,
    facets=facets,
    control_points=control_points,
    holes=holes,
    material=steel,
)
geom.create_mesh(mesh_sizes=1)
Section(geometry=geom).plot_mesh()


from sectionproperties.pre.library import polygon_hollow_section

geom = polygon_hollow_section(d=200, t=6, n_sides=8, r_in=20, n_r=12, material=steel)
geom.create_mesh(mesh_sizes=10)
Section(geometry=geom).plot_mesh()


from sectionproperties.pre.library import rectangular_section

# create a rectangular section with the default material
geom = rectangular_section(d=16, b=100)
geom.create_mesh(mesh_sizes=10)
Section(geometry=geom).plot_mesh()

# assign steel to the geometry, remesh and recreate the Section object
geom.material = steel
geom.create_mesh(mesh_sizes=10)
Section(geometry=geom).plot_mesh()


# create a timber material
timber = Material(
    name="Timber",
    elastic_modulus=8e3,
    poissons_ratio=0.35,
    density=6.5e-7,
    yield_strength=20,
    color="burlywood",
)

# create individual geometries with material properties applied
beam = rectangular_section(d=35, b=170, material=timber)
plate1 = rectangular_section(d=35, b=16, material=steel)
plate2 = rectangular_section(d=35, b=16, material=steel)

# combine geometries, maintaining assigned materials
geom = (
    beam
    + plate1.align_to(other=beam, on="left")
    + plate2.align_to(other=beam, on="right")
)

# mesh and plot
geom.create_mesh(mesh_sizes=[20, 10, 10])
Section(geometry=geom).plot_mesh()


# create CompoundGeometry without materials
rect1 = rectangular_section(d=10, b=10)
rect2 = rectangular_section(d=20, b=20).align_to(other=rect1, on="right")
geom = rect1 + rect2
geom.create_mesh(mesh_sizes=[1])
Section(geometry=geom).plot_mesh()

# create list of materials
mat_list = [steel, timber]

# loop through Geometry objects in CompoundGeometry to change materials
for geometry, mat in zip(geom.geoms, mat_list, strict=False):
    geometry.material = mat

# remesh and recreate Section object
geom.create_mesh(mesh_sizes=[1])
Section(geometry=geom).plot_mesh()
