import math
import cadquery as cq

# --- parameters ---
width = 44.449999999999996
height = 31.75
part_thickness = 31.75
cut0_x = 12.7
cut0_y = 12.7
cut0_z = 0.0
cut0_dx = 31.75
cut0_dy = 19.049999999999997
cut0_dz = 31.75
cut1_x = 25.4
cut1_y = 0.0
cut1_z = 6.35
cut1_dx = 19.049999999999997
cut1_dy = 12.7
cut1_dz = 6.35
cut2_x = 0.0
cut2_y = 25.4
cut2_z = 6.35
cut2_dx = 44.449999999999996
cut2_dy = 6.35
cut2_dz = 19.049999999999997
cut3_x = 25.4
cut3_y = 12.7
cut3_z = 6.35
cut3_dx = 19.049999999999997
cut3_dy = 6.35
cut3_dz = 19.049999999999997

# --- base geometry ---
result = cq.Workplane('XY').box(width, height, part_thickness, centered=(False, False, False))
result = result.cut(cq.Workplane('XY').box(cut0_dx + 0.01, cut0_dy + 0.01, cut0_dz + 0.02, centered=(False, False, False)).translate((cut0_x - 0.0, cut0_y - 0.0, cut0_z - 0.01)))
result = result.cut(cq.Workplane('XY').box(cut1_dx + 0.01, cut1_dy + 0.01, cut1_dz + 0.0, centered=(False, False, False)).translate((cut1_x - 0.0, cut1_y - 0.01, cut1_z - 0.0)))
result = result.cut(cq.Workplane('XY').box(cut2_dx + 0.02, cut2_dy + 0.01, cut2_dz + 0.0, centered=(False, False, False)).translate((cut2_x - 0.01, cut2_y - 0.0, cut2_z - 0.0)))
result = result.cut(cq.Workplane('XY').box(cut3_dx + 0.01, cut3_dy + 0.0, cut3_dz + 0.0, centered=(False, False, False)).translate((cut3_x - 0.0, cut3_y - 0.0, cut3_z - 0.0)))
