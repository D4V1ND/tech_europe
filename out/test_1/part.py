import cadquery as cq

# --- parameters (editable) ---
diameter = 76.0
radius = diameter / 2
thickness = 26.0
hole0_x = 38.0
hole0_y = 38.0
hole0_dia = 38.0
hole0_depth = 16.0
hole1_x = 38.0
hole1_y = 38.0
hole1_dia = 28.0
hole2_x = 38.0
hole2_y = 66.0
hole2_dia = 5.3
hole3_x = 38.0
hole3_y = 10.0
hole3_dia = 5.3
hole4_x = 10.0
hole4_y = 38.0
hole4_dia = 5.3
hole5_x = 66.0
hole5_y = 38.0
hole5_dia = 5.3
hole6_x = 38.0
hole6_y = 66.0
hole6_dia = 7.8
hole6_depth = 4.0
hole7_x = 38.0
hole7_y = 10.0
hole7_dia = 7.8
hole7_depth = 4.0
hole8_x = 10.0
hole8_y = 38.0
hole8_dia = 7.8
hole8_depth = 4.0
hole9_x = 66.0
hole9_y = 38.0
hole9_dia = 7.8
hole9_depth = 4.0

# --- build: bbox corner at origin, so model coords == profile coords ---
result = cq.Workplane('XY').center(radius, radius).circle(radius).extrude(thickness)
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(hole0_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole1_x, hole1_y)]).circle(hole1_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole2_x, hole2_y)]).circle(hole2_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole3_x, hole3_y)]).circle(hole3_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole4_x, hole4_y)]).circle(hole4_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole5_x, hole5_y)]).circle(hole5_dia / 2).extrude(-(thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole6_x, hole6_y)]).circle(hole6_dia / 2).extrude(-(hole6_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole7_x, hole7_y)]).circle(hole7_dia / 2).extrude(-(hole7_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole8_x, hole8_y)]).circle(hole8_dia / 2).extrude(-(hole8_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=thickness + 0.01).pushPoints([(hole9_x, hole9_y)]).circle(hole9_dia / 2).extrude(-(hole9_depth + 0.01)))
