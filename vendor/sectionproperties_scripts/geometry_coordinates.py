# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/geometry_coordinates.html

from sectionproperties.analysis import Section
from sectionproperties.pre import CompoundGeometry


w_a = 1  # width of angle leg
w_p = 2  # width of bottom plate
d = 2  # depth of section
t = 0.1  # thickness of section


# list of points describing the geometry
points = [
    (w_p * -0.5, 0),  # bottom plate
    (w_p * 0.5, 0),
    (w_p * 0.5, t),
    (w_p * -0.5, t),
    (t * -0.5, t),  # inverted angle section
    (t * 0.5, t),
    (t * 0.5, d - t),
    (w_a - 0.5 * t, d - t),
    (w_a - 0.5 * t, d),
    (t * -0.5, d),
]

# list of facets (edges) describing the geometry connectivity
facets = [
    (0, 1),  # bottom plate
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),  # inverted angle section
    (5, 6),
    (6, 7),
    (7, 8),
    (8, 9),
    (9, 4),
]

# list of control points (points within each region)
control_points = [
    (0, t * 0.5),  # bottom plate
    (0, d - t),  # inverted angle section
]


geom = CompoundGeometry.from_points(
    points=points,
    facets=facets,
    control_points=control_points,
)
geom.plot_geometry()


geom.create_mesh(mesh_sizes=[0.0005, 0.001])

sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()
sec.calculate_plastic_properties()


sec.plot_centroids()
