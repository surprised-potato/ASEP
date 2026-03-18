# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/create_mesh.html

from sectionproperties.analysis import Section
from sectionproperties.pre import CompoundGeometry
from sectionproperties.pre.library import (
    box_girder_section,
    rectangular_hollow_section,
    rectangular_section,
)


geom = rectangular_section(d=50, b=50)
geom.create_mesh(mesh_sizes=10)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


# initialise maximum area
max_area = 0

# loop through all finite elements
for el in sec.elements:
    res = el.geometric_properties()  # calculate area properties
    el_area = res[0]  # get the area
    max_area = max(max_area, el_area)  # update max_area

print(f"Max. triangular area = {max_area:.2f}")


shs = rectangular_hollow_section(d=100, b=100, t=9, r_out=22.5, n_r=8)


# vertical split at left hand corner
g1, g2 = shs.split_section(point_i=(22.5, 0), vector=(0, 1))
shs = CompoundGeometry(geoms=g1 + g2)  # reform geometry

# vertical split at right hand corner
g1, g2 = shs.split_section(point_i=(77.5, 0), vector=(0, 1))
shs = CompoundGeometry(geoms=g1 + g2)  # reform geometry

# vertical split at bottom corner
g1, g2 = shs.split_section(point_i=(0, 22.5), vector=(1, 0))
shs = CompoundGeometry(geoms=g1 + g2)  # reform geometry

# vertical split at top corner
g1, g2 = shs.split_section(point_i=(0, 77.5), vector=(1, 0))


geom_list = g1 + g2
geom_list.sort(key=lambda x: x.control_points[0][1])
shs = CompoundGeometry(geoms=geom_list)
shs.plot_geometry()


shs.create_mesh(mesh_sizes=5)
Section(geometry=shs).plot_mesh(materials=False)


mesh_sizes = [2.5, 1, 1, 5, 5, 2, 2, 0]

shs.create_mesh(mesh_sizes=mesh_sizes)
Section(geometry=shs).plot_mesh(materials=False)


geom.create_mesh(mesh_sizes=30, min_angle=33)
Section(geom).plot_mesh(materials=False)
geom.create_mesh(mesh_sizes=30, min_angle=5.7)
Section(geom).plot_mesh(materials=False)


box = box_girder_section(d=1200, b_t=1200, b_b=400, t_ft=100, t_fb=80, t_w=50)


box.create_mesh(mesh_sizes=0)
Section(geometry=box).plot_mesh(materials=False)


box.create_mesh(mesh_sizes=0, coarse=True)
Section(geometry=box).plot_mesh(materials=False)
