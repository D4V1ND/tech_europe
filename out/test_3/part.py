import cadquery as cq

# --- parameters (editable) ---
width = 55.0
height = 30.0
thickness = 7.0
cut0_x = 1.6
cut0_y = 1.6
cut0_z = 1.6
cut0_dx = 51.8
cut0_dy = 26.8
cut0_dz = 5.4

# --- build: corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').box(width, height, thickness, centered=(False, False, False))
result = result.cut(cq.Workplane('XY').box(cut0_dx + 0.0, cut0_dy + 0.0, cut0_dz + 0.01, centered=(False, False, False)).translate((cut0_x - 0.0, cut0_y - 0.0, cut0_z - 0.0)))
result = result.edges('|Z').fillet(8.0)
