import cadquery as cq

# --- parameters (editable) ---
width = 100.0
height = 60.0
thickness = 8.0

# --- build: bbox corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').box(width, height, thickness, centered=(False, False, False))
