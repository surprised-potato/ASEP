# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/analysis/frame_analysis.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import polygon_hollow_section

geom = polygon_hollow_section(d=600, t=12, n_sides=12, r_in=20, n_r=8)
geom.create_mesh(mesh_sizes=20)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


import time

start = time.time()
sec.calculate_geometric_properties()
sec.calculate_warping_properties()
end = time.time()
gw_time = end - start


print(f"Geometric/Warping Time = {gw_time:.4f} secs")
print(f"J = {sec.get_j():.3e} mm4")


start = time.time()
sec.calculate_frame_properties()
end = time.time()
f_time = end - start


print(f"Frame Time = {f_time:.4f} secs")
print(f"J = {sec.get_j():.3e} mm4")
