# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/validation/pilkey_composite.html

from IPython.display import Image

display(Image(filename="images/comp-geom.png"))


from sectionproperties.pre import Material
from sectionproperties.pre.library import rectangular_section

d = 2  # depth of rectangles
b = 15  # width of each rectangle
# aluminium material
al = Material(
    name="Aluminium",
    elastic_modulus=10.4e6,
    poissons_ratio=0.3,
    yield_strength=1.0,
    density=1.0,
    color="lightgrey",
)
# aluminium material
cu = Material(
    name="Copper",
    elastic_modulus=18.5e6,
    poissons_ratio=0.3,
    yield_strength=1.0,
    density=1.0,
    color="gold",
)

# create two rectangles and add geometry together
geom_al = rectangular_section(d=d, b=b, material=al)
geom_cu = rectangular_section(d=d, b=b, material=cu).align_to(other=geom_al, on="right")
geom = geom_al + geom_cu

# plot geometry
geom.plot_geometry()


display(Image(filename="images/comp-mesh.png"))


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=0.1)
sec = Section(geometry=geom)
sec.plot_mesh()


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


pilkey = {
    "area": 60,
    "ea_ref": 83.36,
    "j_ref": 106.22,
}


sectionproperties = {
    "area": sec.get_area(),
    "ea_ref": sec.get_ea(e_ref=al),
    "j_ref": sec.get_ej(e_ref=al),
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


mu = 18.5 / 10.4
j_an = 1 / 3 * (b + mu * b) * d**3 - 3.361 * (d**4) / (16) * (1 + mu**2) / (1 + mu)
print(f"J_an = {j_an:.4f} mm4")
print(f"J_sp = {sectionproperties['j_ref']:.4f} mm4")
print(f"J_pi = {pilkey['j_ref']:.4f} mm4")
