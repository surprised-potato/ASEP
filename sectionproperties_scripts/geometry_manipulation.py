# Script content scraped from: https://sectionproperties.readthedocs.io/en/stable/examples/geometry/geometry_manipulation.html

from sectionproperties.pre.library import (
    channel_section,
    rectangular_hollow_section,
    rectangular_section,
)


# create a central rectangle
rect_centre = rectangular_section(d=150, b=100)

# align a square to the central rectangle's right side
sq_right = rectangular_section(d=20, b=20).align_to(other=rect_centre, on="left")

# combine two geometries and plot
geom = rect_centre + sq_right
geom.plot_geometry()


# align a square to the middle of the central rectangle's top side
sq_center = (
    rectangular_section(d=20, b=20)
    .align_center(align_to=rect_centre)
    .align_to(other=rect_centre, on="top")
)

# combine with the previous geometry and plot
geom += sq_center
geom.plot_geometry()


# align a square to the centre of the central rectangle's right inner side
sq_right = (
    rectangular_section(d=20, b=20)
    .align_center(align_to=rect_centre)
    .align_to(other=rect_centre, on="right", inner=True)
)

# combine with the previous geometry and plot
geom = geom - sq_right + sq_right  # note we first subtract to avoid overlapping regions
geom.plot_geometry()


# create RHS PFC
pfc_right = channel_section(d=200, b=75, t_f=12, t_w=6, r=12, n_r=8)

# create LHS PFC by mirroring the RHS PFC
pfc_left = pfc_right.mirror_section(axis="y", mirror_point=(0, 0))

# combine the two PFCs into one geometry and plot the geometry
geom = pfc_right + pfc_left
geom.plot_geometry()


geom = geom.rotate_section(angle=10)
geom.plot_geometry()


x_min, _, y_min, _ = geom.calculate_extents()
geom_t = geom.shift_section(x_offset=-x_min, y_offset=-y_min)
geom_t.plot_geometry()


from sectionproperties.pre import CompoundGeometry

right_geoms, left_geoms = geom.split_section(point_i=(102, 0), vector=(0, 1))

# combine resultant geometries into a CompoundGeometry object
geom = CompoundGeometry(geoms=left_geoms + right_geoms)
geom.plot_geometry()


rhs_base = rectangular_hollow_section(d=100, b=50, t=6, r_out=15, n_r=8)
rhs_base.plot_geometry(title="RHS Base")
rhs_base.offset_perimeter(amount=-2.0).plot_geometry(title="RHS 1")
rhs_base.offset_perimeter(amount=1.0).plot_geometry(title="RHS 2")
rhs_base.offset_perimeter(amount=-1.5, where="all").plot_geometry(title="RHS 3")
