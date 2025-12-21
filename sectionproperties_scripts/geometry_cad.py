# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/geometry_cad.html

from sectionproperties.analysis import Section
from sectionproperties.pre import CompoundGeometry, Geometry


geom = Geometry.from_dxf(dxf_filepath="../../_static/cad_files/box_section.dxf")


geom.create_mesh(mesh_sizes=[0.5])
Section(geometry=geom).plot_mesh(materials=False)


geom = Geometry.from_3dm(filepath="../../_static/cad_files/rhino.3dm")
geom = geom.rotate_section(angle=90)  # rotate for viewability


geom.create_mesh(mesh_sizes=[0.005])
Section(geometry=geom).plot_mesh(materials=False)


geom = CompoundGeometry.from_3dm(filepath="../../_static/cad_files/rhino_compound.3dm")
geom = geom.rotate_section(angle=90)  # rotate for viewability


geom.create_mesh(mesh_sizes=[0.005])
Section(geometry=geom).plot_mesh(materials=False)
