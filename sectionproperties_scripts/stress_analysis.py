# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/analysis/stress_analysis.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import rectangular_hollow_section

geom = rectangular_hollow_section(d=100, b=150, t=6, r_out=15, n_r=8)
geom.create_mesh(mesh_sizes=[2])
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


case1 = sec.calculate_stress(mxx=5e6, vy=-10e3, mzz=3e6)
case2 = sec.calculate_stress(myy=15e6, vx=30e3, mzz=1.5e6)


# bending stress
case1.plot_stress(stress="m_zz")


# torsion stress vectors
case1.plot_stress_vector(stress="mzz_zxy")


# von mises stress
case1.plot_stress(stress="vm", cmap="YlOrRd", normalize=False)


# shear stress
case2.plot_stress(stress="v_zxy")


# von mises stress
case2.plot_stress(stress="vm", cmap="YlOrRd", normalize=False)
