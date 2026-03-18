# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/plot_centroids.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import bulb_section

geom = bulb_section(d=200, b=50, t=12, r=10, n_r=8)
geom.create_mesh(mesh_sizes=20)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.plot_centroids()


sec.calculate_warping_properties()
sec.plot_centroids(title="Geometric & Warping Centroids", alpha=0.2)


sec.calculate_plastic_properties()
sec.plot_centroids()
