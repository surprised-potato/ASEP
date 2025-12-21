# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/advanced_geometry.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import i_section

i_sec1 = i_section(d=250, b=150, t_f=13, t_w=10, r=12, n_r=12)
i_sec2 = i_sec1.rotate_section(angle=45)


i_sec1


i_sec2


from sectionproperties.pre import Material

# just some differing properties
mat1 = Material(
    name="Material_1",
    elastic_modulus=200e3,
    poissons_ratio=0.3,
    yield_strength=100,
    density=400,
    color="gold",
)
mat2 = Material(
    name="Material_2",
    elastic_modulus=150e3,
    poissons_ratio=0.2,
    yield_strength=100,
    density=200,
    color="blue",
)

i_sec1.material = mat1
i_sec2.material = mat2


i_sec1 + i_sec2


(i_sec1 + i_sec2).plot_geometry()


Section(geometry=(i_sec1 + i_sec2).create_mesh(mesh_sizes=[10])).plot_mesh()


i_sec2 | i_sec1


((i_sec2 - i_sec1) + i_sec1).plot_geometry()


cut_2_from_1 = i_sec1 - i_sec2  # locates intersection nodes
sec_1_nodes_added = cut_2_from_1 | i_sec1

# this can also be done in one line
sec_1_nodes_added = (i_sec1 - i_sec2) | i_sec1


sec_1_nodes_added.plot_geometry()


analysis_geom = (i_sec2 - i_sec1) + sec_1_nodes_added
analysis_geom.plot_geometry()


analysis_geom.create_mesh(mesh_sizes=[10])
analysis_sec = Section(geometry=analysis_geom)
analysis_sec.plot_mesh()


from sectionproperties.pre.library import rectangular_section

s1 = rectangular_section(d=1, b=1)
s2 = rectangular_section(d=0.5, b=0.5).shift_section(x_offset=1, y_offset=0.25)
geom = s1 + s2
geom


geom = geom.rotate_section(angle=30)
geom


# this may crash the kernel...
# geom.create_mesh(mesh_sizes=[0.2, 0.1])


geom.plot_geometry(labels=("points", "facets", "control_points"))


(s1 - s2).plot_geometry(labels=("points",))


geom_fixed = (s1 - s2) + s2
geom_fixed_rotated = geom_fixed.rotate_section(angle=30)
geom_fixed_rotated.create_mesh(mesh_sizes=[0.2, 0.1])
geom_fixed_rotated.plot_geometry(
    labels=(
        "points",
        "facets",
    ),
)
sec = Section(geometry=geom_fixed_rotated)
sec.display_mesh_info()


sq1 = rectangular_section(d=80, b=80, material=mat1).align_center()
sq2 = rectangular_section(d=100, b=100, material=mat2).align_center()
sq2 = sq2 - sq1
sq2 = sq2.shift_section(x_offset=-50, y_offset=-50).rotate_section(angle=30)

sq1 + sq2


# note the order in which the geometry is combined
Section(geometry=(sq2 + sq1).create_mesh(mesh_sizes=[5, 10])).plot_mesh()
Section(geometry=(sq1 + sq2).create_mesh(mesh_sizes=[5, 10])).plot_mesh()


mat3 = Material(
    name="Material 3",
    elastic_modulus=100,
    poissons_ratio=0.3,
    yield_strength=10,
    density=1e-6,
    color="red",
)

sq1 = rectangular_section(d=100, b=100, material=mat1).align_center()
sq2 = rectangular_section(d=75, b=75, material=mat2).align_center()
sq3 = rectangular_section(d=50, b=50, material=mat3).align_center()
hole = rectangular_section(d=25, b=25).align_center()

compound = (
    (sq1 - sq2)  # create a big square with a medium hole in it and stack it over...
    + (sq2 - sq3)  # a medium square with a medium-small hole in it and stack it over...
    + (sq3 - hole)  # a medium-small square with a small hole in it.
)

compound


from sectionproperties.pre import CompoundGeometry

# points for four squares are created
points = [
    [-50.0, 50.0],  # square 1
    [50.0, 50.0],
    [50.0, -50.0],
    [-50.0, -50.0],
    [37.5, -37.5],  # square 2
    [37.5, 37.5],
    [-37.5, 37.5],
    [-37.5, -37.5],
    [25.0, -25.0],  # square 3
    [25.0, 25.0],
    [-25.0, 25.0],
    [-25.0, -25.0],
    [12.5, -12.5],  # square 4 (hole)
    [12.5, 12.5],
    [-12.5, 12.5],
    [-12.5, -12.5],
]

# facets trace each of the four squares
facets = [
    [0, 1],  # square 1
    [1, 2],
    [2, 3],
    [3, 0],
    [4, 5],  # square 2
    [5, 6],
    [6, 7],
    [7, 4],
    [8, 9],  # square 3
    [9, 10],
    [10, 11],
    [11, 8],
    [12, 13],  # square 4 (hole)
    [13, 14],
    [14, 15],
    [15, 12],
]

# three squares
control_points = [[-43.75, 0.0], [-31.25, 0.0], [-18.75, 0.0]]
holes = [[0, 0]]

nested_compound = CompoundGeometry.from_points(
    points=points,
    facets=facets,
    control_points=control_points,
    holes=holes,
    materials=[mat1, mat2, mat3],
)

nested_compound


Section(geometry=compound.create_mesh(mesh_sizes=5)).plot_mesh()
Section(geometry=nested_compound.create_mesh(mesh_sizes=5)).plot_mesh()
