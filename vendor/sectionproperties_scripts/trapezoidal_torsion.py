# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/advanced/trapezoidal_torsion.html

import matplotlib.pyplot as plt
import numpy as np
from shapely import Polygon

from sectionproperties.analysis import Section
from sectionproperties.pre import Geometry
from sectionproperties.pre.library import rectangular_section, triangular_section


def get_section_j(
    geom: Geometry,
    ms: float,
    plot_geom: bool = False,
) -> float:
    """Retrieve the torsion constant given a geometry (geom) and mesh size (ms)."""
    geom.create_mesh(mesh_sizes=[ms])
    sec = Section(geometry=geom)

    if plot_geom:
        sec.plot_mesh(materials=False)

    sec.calculate_frame_properties()

    return sec.get_j()


n = 100  # mesh density


def do_section(
    b: float,
    s: float,
    d_mid: float = 1.0,
    plot_geom=False,
) -> tuple[float, float, float, float]:
    """Calculates the torsion constant for a trapezoid and rectangle."""
    delta = s * d_mid
    d1 = d_mid - delta
    d2 = d_mid + delta

    # compute mesh size
    ms = d_mid * b / n

    # define the points of the trapezoid
    points = [
        (0, 0),
        (0, d1),
        (b, d2),
        (b, 0),
    ]

    # create geometry
    if s < 1.0:
        trap_geom = Geometry(geom=Polygon(points))
    else:
        trap_geom = triangular_section(h=d2, b=b)

    # calculate torsion constant (trapezoid)
    jt = get_section_j(geom=trap_geom, ms=ms, plot_geom=plot_geom)

    # calculate torsion constant (rectangle)
    rect_geom = rectangular_section(d=(d1 + d2) / 2, b=b)
    jr = get_section_j(geom=rect_geom, ms=ms, plot_geom=plot_geom)

    return jt, jr, d1, d2


b, s = 4.0, 0.3
jt, jr, d1, d2 = do_section(b=b, s=s, plot_geom=True)
print(f"{b=:.1f}; {s=:.1f}; {jr=:.3f}; {jt=:.3f}; {jr/jt=:.3f}")


b_list = np.logspace(0, np.log10(10.0), 10)
s_list = np.linspace(0.0, 1.0, 10)
j_rect = np.zeros((len(b_list), len(s_list)))
j_trap = np.zeros((len(b_list), len(s_list)))


for i, b in enumerate(b_list):
    for j, s in enumerate(s_list):
        jt, jr, d1, d2 = do_section(b=b, s=s)
        j_trap[i][j] = jt
        j_rect[i][j] = jr


j_ratio = j_rect / j_trap


# setup plot
plt.figure(figsize=(12, 6))

# colorbar levels
levels = np.arange(start=0.5, stop=1.5, step=0.05)

# contour line plot
cs = plt.contour(
    s_list,
    b_list,
    j_ratio,
    levels=[0.95, 0.99, 1.00, 1.01, 1.05],
    colors=("k",),
    linestyles=(":",),
    linewidths=(1.2,),
)
plt.clabel(cs, colors="k", fontsize=10)

# filled contour plot
plt.contourf(s_list, b_list, j_ratio, 25, cmap="Wistia", levels=levels)

# plot settings
plt.minorticks_on()
plt.grid(which="both", ls=":")
plt.xlabel(r"Slope $s = (d_2-d_1)/(d_2+d_1); d_2\geq d_1, d_1\geq 0$")
plt.ylabel("Aspect $b/d_{ave}; d_{ave} = (d_1 + d_2)/2$")
plt.colorbar()
title = r"Accuracy of rectangular approximation to trapezoid torsion "
title += r"constant $J_{rect}\, /\, J_{trapz}$"
plt.title(title, multialignment="center")
plt.show()
