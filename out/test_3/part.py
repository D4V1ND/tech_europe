import math
import cadquery as cq

# --- parameters ---
width = 55.0
height = 30.0
part_thickness = 7.0
cut0_x = 1.6
cut0_y = 1.6
cut0_z = 1.6
cut0_dx = 51.8
cut0_dy = 26.8
cut0_dz = 5.4
cut0_radius = 6.4

# --- base geometry ---
result = cq.Workplane('XY').box(width, height, part_thickness, centered=(False, False, False))
result = result.edges('|Z').fillet(8.0)
cut0_solid = (cq.Workplane('XY').box(cut0_dx + 0.0, cut0_dy + 0.0, cut0_dz + 0.01, centered=(False, False, False)))
cut0_solid = cut0_solid.edges('|Z').fillet(cut0_radius)
result = result.cut(cut0_solid.translate((cut0_x - 0.0, cut0_y - 0.0, cut0_z - 0.0)))
