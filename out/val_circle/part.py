import cadquery as cq

# --- parameters (editable) ---
diameter = 80.0
radius = diameter / 2
thickness = 12.0
hole0_x = 40.0
hole0_y = 40.0
hole0_dia = 30.0

# --- build: bbox corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').center(radius, radius).circle(radius).extrude(thickness)
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(thickness + 0.02)))
