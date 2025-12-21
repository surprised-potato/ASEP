# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/plot_stress.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import elliptical_section

geom = elliptical_section(d_x=75, d_y=150, n=64)
geom.create_mesh(mesh_sizes=20)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


stress = sec.calculate_stress(
    n=100e3,
    mxx=10e6,
    myy=5e6,
    vx=25e3,
    vy=50e3,
    mzz=3e6,
)


stress.plot_stress(stress="myy_zz")


stress.plot_stress(stress="vy_zx", fmt="{x:.2f}")


stress.plot_stress(stress="vy_zy")


stress.plot_stress(stress="vy_zy", normalize=False)


stress.plot_stress(stress="vy_zy", cmap="viridis", normalize=False)


stress.plot_stress(stress="zz", title="Normal Stress", alpha=0.2)


stress.plot_stress(stress="zxy", cmap="viridis", normalize=False)


stress.plot_stress(
    stress="11",
    cmap="viridis",
    stress_limits=(0, 80),
    normalize=False,
    fmt="{x:.2f}",
    colorbar_label="Principal Stress [MPa]",
)


stress.plot_stress(stress="33", cmap="viridis", normalize=False)


stress.plot_stress(stress="vm", cmap="viridis", normalize=False)


stress.plot_stress_vector(stress="mzz_zxy", cmap="viridis", normalize=False)


stress.plot_stress_vector(
    stress="vy_zxy",
    cmap="viridis",
    normalize=False,
    fmt="{x:.2f}",
)


stress.plot_stress_vector(
    stress="zxy",
    cmap="viridis",
    normalize=False,
    colorbar_label="Stress [MPa]",
)


stress.plot_mohrs_circles(x=0, y=0)


from sectionproperties.pre import Material
from sectionproperties.pre.library import rectangular_section

mat_a = Material("a", 1, 0, 1, 1, color="b")
mat_b = Material("b", 10, 0, 1, 1, color="g")
mat_c = Material("c", 5, 0, 1, 1, color="r")
mat_d = Material("d", 2, 0, 1, 1, color="y")

a = rectangular_section(20, 20, mat_a)
b = rectangular_section(20, 20, mat_b).align_to(a, "right")
c = rectangular_section(20, 20, mat_c).align_to(a, "top")
d = rectangular_section(20, 20, mat_d).align_to(a, "top").align_to(a, "right")
geom = a + b + c + d
geom.create_mesh(10)
sec = Section(geom)
sec.plot_mesh()


sec.calculate_geometric_properties()
stress = sec.calculate_stress(n=10e3, mxx=1e6)


stress.plot_stress(stress="m_zz")


stress.plot_stress(stress="m_zz", material_list=[mat_a])


stress.plot_stress(stress="m_zz", material_list=[mat_a, mat_c])
