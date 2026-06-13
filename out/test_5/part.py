import cadquery as cq

# --- parameters (editable) ---
width = 116.0
height = 105.0
thickness = 100.0
hole0_x = 58.0
hole0_y = 50.0
hole0_dia = 82.0
cut0_x = 3.0
cut0_y = 11.0
cut0_z = 0.0
cut0_dx = 110.0
cut0_dy = 95.0
cut0_dz = 97.0
cut1_x = 3.0
cut1_y = 0.0
cut1_z = 0.0
cut1_dx = 110.0
cut1_dy = 8.0
cut1_dz = 97.0
cut2_x = 23.0
cut2_y = 0.0
cut2_z = 0.0
cut2_dx = 70.0
cut2_dy = 12.0
cut2_dz = 50.0

# --- build: corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').box(width, height, thickness, centered=(False, False, False))
result = result.edges('|Z').fillet(7.0)
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').box(cut0_dx + 0.0, cut0_dy + 0.01, cut0_dz + 0.01, centered=(False, False, False)).translate((cut0_x - 0.0, cut0_y - 0.0, cut0_z - 0.01)))
result = result.cut(cq.Workplane('XY').box(cut1_dx + 0.0, cut1_dy + 0.01, cut1_dz + 0.01, centered=(False, False, False)).translate((cut1_x - 0.0, cut1_y - 0.01, cut1_z - 0.01)))
result = result.cut(cq.Workplane('XY').box(cut2_dx + 0.0, cut2_dy + 0.01, cut2_dz + 0.01, centered=(False, False, False)).translate((cut2_x - 0.0, cut2_y - 0.01, cut2_z - 0.01)))
