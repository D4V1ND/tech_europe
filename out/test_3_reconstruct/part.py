import math
import cadquery as cq

# --- parameters ---
profile_points = [(0.0, 0.0), (44.449999999999996, 0.0), (44.449999999999996, 12.7), (12.7, 12.7), (12.7, 31.75), (0.0, 31.75)]
part_thickness = 31.75
cut0_x = 0.0
cut0_y = 25.4
cut0_z = 6.35
cut0_dx = 12.7
cut0_dy = 6.35
cut0_dz = 19.049999999999997
cut1_x = 28.575
cut1_y = 0.0
cut1_z = 12.7
cut1_dx = 15.875
cut1_dy = 12.7
cut1_dz = 6.35

# --- base geometry ---
result = cq.Workplane('XY').polyline(profile_points).close().extrude(part_thickness)
cut0_solid = (cq.Workplane('XY').box(cut0_dx + 0.01, cut0_dy + 0.01, cut0_dz + 0.0, centered=(False, False, False)))
result = result.cut(cut0_solid.translate((cut0_x - 0.01, cut0_y - 0.0, cut0_z - 0.0)))
cut1_solid = (cq.Workplane('XY').box(cut1_dx + 0.01, cut1_dy + 0.01, cut1_dz + 0.0, centered=(False, False, False)))
result = result.cut(cut1_solid.translate((cut1_x - 0.0, cut1_y - 0.01, cut1_z - 0.0)))
