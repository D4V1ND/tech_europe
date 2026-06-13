import cadquery as cq

# --- parameters (editable) ---
width = 44.449999999999996
height = 31.75
thickness = 31.75

# --- build: corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').box(width, height, thickness, centered=(False, False, False))
