import math
import cadquery as cq

# --- parameters ---
width = 44.449999999999996
height = 31.75
part_thickness = 12.7
hole0_x = 6.35
hole0_y = 6.35
hole0_dia = 5.08
hole1_x = 38.099999999999994
hole1_y = 6.35
hole1_dia = 5.08
hole2_x = 6.35
hole2_y = 25.4
hole2_dia = 5.08
hole3_x = 38.099999999999994
hole3_y = 25.4
hole3_dia = 5.08

# --- base geometry ---
result = cq.Workplane('XY').box(width, height, part_thickness, centered=(False, False, False))
result = result.edges('|Z').fillet(2.54)
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(part_thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole1_x, hole1_y)]).circle(hole1_dia / 2).extrude(-(part_thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole2_x, hole2_y)]).circle(hole2_dia / 2).extrude(-(part_thickness + 0.02)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole3_x, hole3_y)]).circle(hole3_dia / 2).extrude(-(part_thickness + 0.02)))
