import cadquery as cq

# --- parameters (editable) ---
profile_pts = [(0.0, 0.0), (50.0, 0.0), (50.0, 20.0), (20.0, 20.0), (20.0, 40.0), (0.0, 40.0)]
thickness = 10.0
hole0_x = 10.0
hole0_y = 10.0
hole0_dia = 6.0

# --- build: bbox corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').polyline(profile_pts).close().extrude(thickness)
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(thickness + 0.02)))
