# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/validation/pilkey_arc.html

from IPython.display import Image

display(Image(filename="images/arc-geom.png"))


import numpy as np
from shapely import LineString, buffer

from sectionproperties.pre import Geometry, Material

r = 16  # radius
t = 0.5  # thickness
alpha = 2 * np.pi / 3  # arc angle
n = 128  # number of points definining LineString
# steel material
mat = Material(
    name="Steel",
    elastic_modulus=2.1e8,
    poissons_ratio=0.33333,
    yield_strength=1.0,
    density=1.0,
    color="lightgrey",
)

# define points on the LineString
pts = []
for idx in range(n):
    theta = -alpha / 2 + idx / (n - 1) * alpha
    x = r * np.sin(theta)
    y = r * np.cos(theta)
    pts.append((x, y))

# create LineString
line = LineString(coordinates=pts)

# create Polygon by buffering the LineString
poly = buffer(geometry=line, distance=0.5 * t, cap_style="flat", join_style="mitre")

# create sectionproperties Geometry object
geom = Geometry(geom=poly, material=mat)

# plot geometry
geom.plot_geometry()


display(Image(filename="images/arc-mesh.png"))


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=0.1)
sec = Section(geometry=geom)
sec.plot_mesh()


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


pilkey = {
    "area": 16.75516,
    "qx": 221.72054,
    "qy": 0.0,
    "cx": 0.0,
    "cy": 13.23297,
    "x_sc": 0.0,
    "y_sc": 17.83662,
    "ixx_g": 3032.21070,
    "iyy_g": 1258.15764,
    "ixy_g": 0.0,
    "ixx_c": 98.18931,
    "iyy_c": 1258.15764,
    "ixy_c": 0.0,
    "zxx": 18.32584,
    "zyy": 89.40279,
    "rx": 2.42079,
    "ry": 8.66549,
    "phi": -90.0,
    "alpha_x": 1.50823,
    "alpha_y": 4.60034,
    "alpha_xy": 0.0,
    "j": 1.38355,
    "gamma": 1046.49221,
}


sectionproperties = {
    "area": sec.get_area(),
    "qx": sec.get_eq(e_ref=mat)[0],
    "qy": sec.get_eq(e_ref=mat)[1],
    "cx": sec.get_c()[0],
    "cy": sec.get_c()[1],
    "x_sc": sec.get_sc()[0],
    "y_sc": sec.get_sc()[1],
    "ixx_g": sec.get_eig(e_ref=mat)[0],
    "iyy_g": sec.get_eig(e_ref=mat)[1],
    "ixy_g": sec.get_eig(e_ref=mat)[2],
    "ixx_c": sec.get_eic(e_ref=mat)[0],
    "iyy_c": sec.get_eic(e_ref=mat)[1],
    "ixy_c": sec.get_eic(e_ref=mat)[2],
    "zxx": min(sec.get_ez(e_ref=mat)[:2]),
    "zyy": min(sec.get_ez(e_ref=mat)[2:]),
    "rx": sec.get_rc()[0],
    "ry": sec.get_rc()[1],
    "phi": sec.get_phi(),
    "alpha_x": sec.get_area() / sec.get_eas(e_ref=mat)[0],
    "alpha_y": sec.get_area() / sec.get_eas(e_ref=mat)[1],
    "alpha_xy": sec.get_area() / sec.section_props.a_sxy,
    "j": sec.get_ej(e_ref=mat),
    "gamma": sec.get_egamma(e_ref=mat),
}


from rich.console import Console
from rich.table import Table
from rich.text import Text

# setup table
table = Table(title="Comparison of Results")
table.add_column("Property", justify="left", style="cyan", no_wrap=True)
table.add_column(Text("Pilkey", justify="center"), justify="right", style="green")
table.add_column(Text("sectionproperties", style="i"), justify="right", style="green")
table.add_column(Text("Error", justify="center"), justify="right", style="green")

# create a row for each property
for key in pilkey:
    # get results
    p_res = pilkey[key]
    sp_res = sectionproperties[key]

    # calculate relative error
    rel_error = (sp_res - p_res) / p_res if p_res != 0 else sp_res

    # print row
    table.add_row(key, f"{p_res:.4e}", f"{sp_res:.4e}", f"{rel_error:.2e}")

console = Console()
console.print(table)


err = (sectionproperties["j"] - pilkey["j"]) / pilkey["j"]
print(f"Torsion Constant Relative Error: {err:.6f}")
