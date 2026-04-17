# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/analysis/plastic_analysis.html

from sectionproperties.pre.library import mono_i_section

geom = mono_i_section(d=200, b_t=50, b_b=100, t_ft=12, t_fb=8, t_w=6, r=8, n_r=8)


from sectionproperties.analysis import Section

geom.create_mesh(mesh_sizes=0)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_plastic_properties()


sec.calculate_geometric_properties()
sec.calculate_plastic_properties()


sec.plot_centroids()


fy = 250  # yield stress in MPa

# calculate yield moment for the top & bottom flanges
my_t = fy * sec.get_z()[0]
my_b = fy * sec.get_z()[1]

# calculate plastic moment about x-axis
mp = fy * sec.get_s()[0]

# print results
print(f"My_t = {my_t / 1e6:.1f} kN.m")
print(f"My_b = {my_b / 1e6:.1f} kN.m")
print(f"Mp = {mp / 1e6:.1f} kN.m")


print(f"SF_t = {sec.get_sf()[0]:.2f}")
print(f"SF_b = {sec.get_sf()[1]:.2f}")


from sectionproperties.pre.library import angle_section

geom = angle_section(d=150, b=90, t=12, r_r=10, r_t=5, n_r=8)
geom.create_mesh(mesh_sizes=0)
sec = Section(geometry=geom)
sec.calculate_geometric_properties()
sec.calculate_plastic_properties()
sec.plot_centroids()


print(f"Sxx = {sec.get_s()[0]:.3e} mm3")
print(f"S11 = {sec.get_sp()[0]:.3e} mm3")
print(f"Syy = {sec.get_s()[1]:.3e} mm3")
print(f"S22 = {sec.get_sp()[1]:.3e} mm3")
