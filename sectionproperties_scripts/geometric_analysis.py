# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/analysis/geometric_analysis.html

from sectionproperties.pre.library import i_section

geom = i_section(d=203, b=133, t_f=7.8, t_w=5.8, r=8.9, n_r=8)


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=5)
sec = Section(geometry=geom)


sec.display_mesh_info()


sec.plot_mesh(materials=False)


geom.create_mesh(mesh_sizes=0)
sec = Section(geometry=geom)
sec.display_mesh_info()
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()


sec.display_results(fmt=".0f")


from sectionproperties.pre.library import channel_section

# create 150 pfc geometry
pfc = channel_section(d=150, b=75, t_f=9.5, t_w=6, r=10, n_r=8)
pfc.plot_geometry(legend=False)


pfc.create_mesh(mesh_sizes=0)
sec_pfc = Section(geometry=pfc)
sec_pfc.calculate_geometric_properties()


# create compound geometry
geom = pfc.mirror_section(axis="y", mirror_point=(0, 0)) + pfc.shift_section(
    x_offset=1000,
)
geom.create_mesh(mesh_sizes=0)
sec_truss = Section(geometry=geom)
sec_truss.plot_mesh(materials=False)
sec_truss.calculate_geometric_properties()


area_ratio = sec_truss.get_area() / sec_pfc.get_area()
ixx_ratio = sec_truss.get_ic()[0] / sec_pfc.get_ic()[0]
iyy_ratio = sec_truss.get_ic()[1] / sec_pfc.get_ic()[1]
zyy_ratio = sec_truss.get_z()[2] / sec_pfc.get_z()[2]
ry_ratio = sec_truss.get_rc()[1] / sec_pfc.get_rc()[1]


from rich.console import Console
from rich.table import Table

# setup table
table = Table(title="Section Properties Comparison")
table.add_column("Property", justify="left", style="cyan", no_wrap=True)
table.add_column("PFC", justify="right", style="green")
table.add_column("Truss", justify="right", style="green")
table.add_column("Ratio", justify="right", style="green")

# add data to the table
table.add_row(
    "area",
    f"{sec_pfc.get_area():.0f}",
    f"{sec_truss.get_area():.0f}",
    f"{area_ratio:.2f}",
)
table.add_row(
    "ixx",
    f"{sec_pfc.get_ic()[0]:.3e}",
    f"{sec_truss.get_ic()[0]:.3e}",
    f"{ixx_ratio:.2f}",
)
table.add_row(
    "iyy",
    f"{sec_pfc.get_ic()[1]:.3e}",
    f"{sec_truss.get_ic()[1]:.3e}",
    f"{iyy_ratio:.2f}",
)
table.add_row(
    "zyy",
    f"{sec_pfc.get_z()[2]:.3e}",
    f"{sec_truss.get_z()[2]:.3e}",
    f"{zyy_ratio:.2f}",
)
table.add_row(
    "ry",
    f"{sec_pfc.get_rc()[1]:.0f}",
    f"{sec_truss.get_rc()[1]:.0f}",
    f"{ry_ratio:.2f}",
)

# print table
console = Console()
console.print(table)
