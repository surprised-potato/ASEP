# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/advanced/rectangle_torsion.html

import numpy as np

# list of aspect ratios to analyse (10^0 = 1 to 10^1.301 = 20)
# logspace used to concentrate data near aspect ratio = 1
aspect_ratios = np.logspace(0, 1.301, 50)
torsion_constants = []  # list of torsion constant results
area = 1  # cross-section area
n = 100  # approximate number of finite elements in each analysis


from sectionproperties.analysis import Section
from sectionproperties.pre.library import rectangular_section

for ar in aspect_ratios:
    # calculate rectangle dimensions
    d = np.sqrt(ar)
    b = 1 / d
    geom = rectangular_section(d=d, b=b)

    # create mesh and Section object
    ms = d * b / n
    geom.create_mesh(mesh_sizes=[ms])
    sec = Section(geometry=geom)

    # perform analysis
    sec.calculate_frame_properties()

    # save the torsion constant
    torsion_constants.append(sec.get_j())


import matplotlib.pyplot as plt

_, ax = plt.subplots()
ax.plot(aspect_ratios, torsion_constants, "k-")
ax.set_xlim(0, 21)
ax.set_ylim(0, 0.15)
ax.set_xlabel("Aspect Ratio [d/b]")
ax.set_ylabel("Torsion Constant [J]")
ax.set_title("Rectangular Section Torsion Constant")
ax.grid()
plt.show()
