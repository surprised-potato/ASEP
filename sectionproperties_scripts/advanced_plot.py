# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/advanced/advanced_plot.html

from sectionproperties.pre.library import rectangular_hollow_section

geom = rectangular_hollow_section(d=100, b=100, t=6, r_out=15, n_r=8)


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=[5])
sec = Section(geometry=geom)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()
stress = sec.calculate_stress(mzz=10e6)


import matplotlib.pyplot as plt

# plot the geometry
ax = geom.plot_geometry(
    labels=[],
    nrows=2,
    ncols=2,
    figsize=(12, 7),
    render=False,
)

# get the figure object from the first plot
fig = ax.get_figure()

# plot the mesh
sec.plot_mesh(materials=False, ax=fig.axes[1])

# plot the centroids
sec.plot_centroids(ax=fig.axes[2])

# plot the torsion stress
stress.plot_stress(
    stress="mzz_zxy",
    normalize=False,
    ax=fig.axes[3],
)

# finally display the plot
plt.show()
