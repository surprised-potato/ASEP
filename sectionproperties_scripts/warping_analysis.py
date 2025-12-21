# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/analysis/warping_analysis.html

from sectionproperties.pre.library import channel_section

geom = channel_section(d=250, b=90, t_f=15, t_w=8, r=12, n_r=8)


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=7)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


import time

sec.calculate_geometric_properties()

# direct solver
start = time.time()
sec.calculate_warping_properties(solver_type="direct")
end = time.time()
print(f"Direct Solver Time = {end - start:.4f} secs")

# cgs solver
start = time.time()
sec.calculate_warping_properties(solver_type="cgs")
end = time.time()
print(f"CGS Solver Time = {end - start:.4f} secs")


sec.plot_centroids()


print(f"J = {sec.get_j():.3e} mm4")
print(f"Iw = {sec.get_gamma():.3e} mm6")
print(f"As_y = {sec.get_as()[1]:.1f} mm2")


from sectionproperties.pre.library import rectangular_section

# create an unconnected mesh
rect = rectangular_section(d=10, b=10)
geom = rect + rect.shift_section(x_offset=20)
geom.create_mesh(mesh_sizes=1)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


# geometric and plastic analyses can be conducted
sec.calculate_geometric_properties()
sec.calculate_plastic_properties()


# warping analysis will fail
sec.calculate_warping_properties()
