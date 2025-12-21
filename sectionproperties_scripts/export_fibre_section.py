# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/results/export_fibre_section.html

from sectionproperties.post.fibre import to_fibre_section
from sectionproperties.pre.library import i_section

geom = i_section(d=203, b=133, t_f=7.8, t_w=5.8, r=8.9, n_r=8)
geom.create_mesh(mesh_sizes=10)

commands = to_fibre_section(geom, analysis_type="3DOS")

print(commands[:3000])


# write the fibre section to a file
# uncomment below to write file
# with open('200UB25.4.sp', 'w') as f:
#     f.write(commands)

# write the main analysis file
# since we assigned '3DOS' analysis type,
# we need to use compatible elements, for example, 'B31OS'.
model = """# Example torsion analysis
node 1 0 0 0
node 2 1 0 0
material ElasticOS 1 200. .25
file 200UB25.4.sp
orientation B3DOSL 1 0. 0. 1.
element B31OS 1 1 2 1 1 6
fix2 1 E 1
displacement 1 0 1E-1 4 2
plainrecorder 1 Node RF4 2
plainrecorder 2 Element BEAMS 1
step static 1
set ini_step_size 1E-1
set fixed_step_size true
converger RelIncreDisp 1 1E-10 5 1
analyze
save recorder 1 2
exit
"""
# uncomment below to write file
# with open('torsion_analysis.sp', 'w') as f:
#     f.write(model)


geom.plot_geometry()


from sectionproperties.analysis import Section

sec = Section(geom)
sec.calculate_geometric_properties()
x, y = sec.get_c()
geom = geom.shift_section(-x, -y)  # or whatever shift you want
geom.create_mesh(mesh_sizes=5)
geom.plot_geometry()


commands = to_fibre_section(geom, analysis_type="3DOS", material_mapping={"default": 1})
print(commands[:5000])


# from os.path import exists

# write the fibre section to a file with material tag replaced
# uncomment below to write file
# with open('200UB25.4.sp', 'w') as f:
#     f.write(commands)

# run the analysis
# if which("suanpan") is not None:
#     from subprocess import run

#     result_available = True
#     run(["suanpan", "-f", "torsion_analysis.sp"])
# else:
#     result_available = exists("R1-RF42.txt")
#     print("suanPan is not installed.")
result_available = False


if result_available:
    import numpy as np
    from matplotlib import pyplot as plt

    data = np.loadtxt("R1-RF42.txt")
    twist = data[:, 0] * 0.1
    torque = data[:, 1]
    plt.plot(twist, torque)
    plt.xlabel("twist (rad)")
    plt.ylabel("total torque")
    plt.legend(["200UB25.4"])
    plt.tight_layout()
    plt.show()


if result_available:
    data = np.loadtxt("R2-BEAMS1.txt")
    twist = data[:, 0] * 0.1
    torque = data[:, 6]
    ref_torque = twist * 80 * 62.7e3  # G=80, J=62.7
    plt.plot(twist, torque)
    plt.plot(twist, ref_torque)
    plt.xlabel("twist (rad)")
    plt.ylabel("St. Venant torsion")
    plt.legend(["numerical", "theoretical"])
    plt.tight_layout()
    plt.show()
