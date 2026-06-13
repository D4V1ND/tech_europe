import cadquery as cq

# --- parameters (editable) ---
width = 44.449999999999996
height = 31.75
thickness = 31.75
cut0_x = 12.7
cut0_y = 0.0
cut0_z = 12.7
cut0_dx = 31.75
cut0_dy = 31.75
cut0_dz = 19.049999999999997
cut1_x = 0.0
cut1_y = 6.35
cut1_z = 25.4
cut1_dx = 12.7
cut1_dy = 19.049999999999997
cut1_dz = 6.35
cut2_x = 28.575
cut2_y = 12.7
cut2_z = 0.0
cut2_dx = 15.875
cut2_dy = 6.35
cut2_dz = 12.7

# --- build: corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').box(width, height, thickness, centered=(False, False, False))
result = result.cut(cq.Workplane('XY').box(cut0_dx + 0.01, cut0_dy + 0.02, cut0_dz + 0.01, centered=(False, False, False)).translate((cut0_x - 0.0, cut0_y - 0.01, cut0_z - 0.0)))
result = result.cut(cq.Workplane('XY').box(cut1_dx + 0.01, cut1_dy + 0.0, cut1_dz + 0.01, centered=(False, False, False)).translate((cut1_x - 0.01, cut1_y - 0.0, cut1_z - 0.0)))
result = result.cut(cq.Workplane('XY').box(cut2_dx + 0.01, cut2_dy + 0.0, cut2_dz + 0.01, centered=(False, False, False)).translate((cut2_x - 0.0, cut2_y - 0.0, cut2_z - 0.01)))
