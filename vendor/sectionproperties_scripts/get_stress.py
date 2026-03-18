# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/get_stress.html

from sectionproperties.analysis import Section
from sectionproperties.pre.library import rectangular_hollow_section

geom = rectangular_hollow_section(d=100, b=150, t=6, r_out=15, n_r=8)
geom.create_mesh(mesh_sizes=3)
sec = Section(geometry=geom)


import numpy as np

pt = (144, 6)
x1 = [3] * 10
y1 = np.linspace(20, 80, 10)
x2 = np.linspace(0, 150, 50)
y2 = [3] * 50


import matplotlib.pyplot as plt

ax = sec.plot_mesh(materials=False, render=False)
ax.plot(pt[0], pt[1], "r*", label="Point")
ax.plot(x1, y1, "bo-", label="Line 1")
ax.plot(x2, y2, "go-", label="Line 2")
ax.legend()
plt.show()


sec.calculate_geometric_properties()
sec.calculate_warping_properties()


load_case = {
    "n": -50e3,
    "mxx": 5e6,
    "myy": 10e6,
    "vx": 5e3,
    "vy": 15e3,
    "mzz": 5e6,
}

stress = sec.calculate_stress(**load_case)
stress.plot_stress(stress="vm", cmap="viridis", normalize=False)


sig = sec.get_stress_at_points(pts=[pt], **load_case)[0]
print(f"sig_zz = {sig[0]:.2f} MPa")
print(f"tau_xz = {sig[1]:.2f} MPa")
print(f"tau_yz = {sig[2]:.2f} MPa")


sig_vm = np.sqrt(sig[0] ** 2 + 3 * (np.sqrt(sig[1] ** 2 + sig[2] ** 2)) ** 2)
print(f"sig_vm = {sig_vm:.2f} MPa")


# zip points into a list of tuples
pts = list(zip(x1, y1, strict=False))

# extract stresses along the line
sigs = sec.get_stress_at_points(pts=pts, mxx=10e6)

# we are only interested in the first of three stresses (normal stress)
sig_zz = [x[0] for x in sigs]


fig, ax = plt.subplots()
ax.plot(sig_zz, y1, "kx-")
ax.set_xlabel("Normal Stress [MPa]")
ax.set_ylabel("y-coordinate [mm]")
plt.show()


# zip points into a list of tuples
pts = list(zip(x2, y2, strict=False))

# extract stresses along the line
sigs = sec.get_stress_at_points(pts=pts, vx=100e3)

# we are only interested in the second of three stresses (x-shear stress)
# note we also ignore None results (outside geometry)
tau_xz = [x[1] for x in sigs if x is not None]


fig, ax = plt.subplots()
ax.plot(x2[2:-2], tau_xz, "kx-")
ax.set_xlabel("x-coordinate [mm]")
ax.set_ylabel("Shear Stress [MPa]")
plt.show()


from sectionproperties.pre.library import rectangular_section

geom = rectangular_section(d=100, b=100)
geom.create_mesh(mesh_sizes=50)
sec = Section(geometry=geom)


sec.calculate_geometric_properties()
sec.calculate_warping_properties()
s = sec.calculate_stress(mzz=1e6, vx=10e3, vy=10e3)


s.plot_stress_vector(stress="zxy", cmap="viridis", normalize=False)


s.plot_stress(stress="zxy", cmap="viridis", normalize=False)


xs = [50] * 50
ys = np.linspace(0, 100, 50)
sigs = sec.get_stress_at_points(
    pts=list(zip(xs, ys, strict=False)),
    mzz=1e6,
    vx=10e3,
    vy=10e3,
)
tau_xz = [x[1] for x in sigs]
tau_yz = [x[2] for x in sigs]


fig, ax = plt.subplots()
ax.plot(ys, tau_xz, "k-", label="$\\tau_{xz}$")
ax.plot(ys, tau_yz, "k--", label="$\\tau_{yz}$")
ax.set_xlabel("y-coordinate [mm]")
ax.set_ylabel("Stress [MPa]")
ax.set_ylim(-4, 8)
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
ax.grid()
plt.show()
