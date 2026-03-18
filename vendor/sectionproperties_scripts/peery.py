# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/validation/peery.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import nastran_sections


geom = nastran_sections.nastran_i(dim_1=6, dim_2=3, dim_3=3, dim_4=1, dim_5=1, dim_6=1)
geom = geom.shift_section(y_offset=-3)
geom.create_mesh(mesh_sizes=0.25)
sec = Section(geometry=geom)
sec.plot_mesh(materials=False)


sec.calculate_geometric_properties()
sec.plot_centroids()


print(f"Ix = {sec.section_props.ixx_g:.2f} in4")


stress = sec.calculate_stress(mxx=8e5)


numerical_result = max(stress.get_stress()[0]["sig_zz"])
print(f"Numerical Result = {numerical_result:.1f} psi")
stress.plot_stress(stress="zz")


stress_ref = 8e5 * 3 / 43.3
stress_theory = 8e5 * 3 / (43 + 1 / 3)
print(stress_ref)
print(stress_theory)


geom = nastran_sections.nastran_zed(dim_1=4, dim_2=2, dim_3=8, dim_4=12)
geom = geom.shift_section(x_offset=-5, y_offset=-6)
geom = geom.create_mesh(mesh_sizes=0.25)
sec = Section(geometry=geom)


sec.calculate_geometric_properties()
sec.plot_centroids()


props = sec.section_props
print("    Property | Theoretical | Numerical")
print(f"    ixx_g    | {693.3:<12.1f}| {props.ixx_g:<.1f}")
print(f"    iyy_g    | {173.3:<12.1f}| {props.iyy_g:<.1f}")
print(f"    ixy_g    | {-240:<12.1f}| {props.ixy_g:<.1f}")
print(f"    i11_c    | {787:<12.1f}| {props.i11_c:<.1f}")
print(f"    i22_c    | {79.5:<12.1f}| {props.i22_c:<.1f}")


pt_a = (-5, 4)
pt_b = (-5, 6)
pt_c = (1, 6)

stresses = sec.get_stress_at_points(pts=[pt_a, pt_b, pt_c], mxx=-1e5, myy=1e4)


text_result_a = 1210
numerical_result_a = stresses[0]
print(f"Text Result (A) = {text_result_a:.2f} psi")
print(f"Numerical Result (A) = {numerical_result_a[0]:.2f} psi")


text_result_b = 580
numerical_result_b = stresses[1]
print(f"Text Result (B) = {text_result_b:.2f} psi")
print(f"Numerical Result (B) = {numerical_result_b[0]:.2f} psi")


text_result_c = -2384
numerical_result_c = stresses[2]
print(f"Text Result (C) = {text_result_c:.2f} psi")
print(f"Numerical Result (C) = {numerical_result_c[0]:.2f} psi")


stress = sec.calculate_stress(mxx=-1e5, myy=1e4)
stress.plot_stress(stress="zz")
