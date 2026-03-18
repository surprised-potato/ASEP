# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/display_results.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import circular_hollow_section

geom = circular_hollow_section(d=165.1, t=5.4, n=64)
geom.create_mesh(mesh_sizes=10)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.display_results()


sec.calculate_geometric_properties()
sec.display_results()


sec.display_results(fmt=".1f")


sec.calculate_warping_properties()
sec.calculate_plastic_properties()
sec.display_results()


from sectionproperties.pre import Material

# create steel material
steel = Material(
    name="Steel",
    elastic_modulus=200e3,  # N/mm^2 (MPa)
    poissons_ratio=0.3,  # unitless
    density=7.85e-6,  # kg/mm^3
    yield_strength=500,  # N/mm^2 (MPa)
    color="grey",
)
geom.material = steel  # assign steel to the CHS

# remesh and recreate Section object
geom.create_mesh(mesh_sizes=5)
sec = Section(geometry=geom)

# perform analysis and display results
sec.calculate_geometric_properties()
sec.calculate_warping_properties()
sec.calculate_plastic_properties()
sec.display_results(fmt=".3e")
