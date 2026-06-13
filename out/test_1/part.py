import math
import cadquery as cq

# --- parameters ---
part_diameter = 76.0
part_radius = part_diameter / 2
part_thickness = 26.0
segment0_z = 0.0
segment0_length = 16.0
segment0_outer_dia = 76.0
segment0_inner_dia = 38.0
segment1_z = 16.0
segment1_length = 2.0
segment1_outer_dia = 76.0
segment1_inner_dia = 28.0
segment2_z = 18.0
segment2_length = 8.0
segment2_outer_dia = 48.0
segment2_inner_dia = 28.0
hole0_x = 38.0
hole0_y = 67.0
hole0_dia = 5.3
hole0_depth = 18.0
hole0_cbore_dia = 7.8
hole0_cbore_depth = 4.0
hole1_x = 67.0
hole1_y = 38.0
hole1_dia = 5.3
hole1_depth = 18.0
hole1_cbore_dia = 7.8
hole1_cbore_depth = 4.0
hole2_x = 38.0
hole2_y = 9.0
hole2_dia = 5.3
hole2_depth = 18.0
hole2_cbore_dia = 7.8
hole2_cbore_depth = 4.0
hole3_x = 9.0
hole3_y = 38.0
hole3_dia = 5.3
hole3_depth = 18.0
hole3_cbore_dia = 7.8
hole3_cbore_depth = 4.0

# --- base geometry ---
result = None
segment0 = (cq.Workplane('XY').center(part_radius, part_radius).circle(segment0_outer_dia / 2).extrude(segment0_length).translate((0, 0, segment0_z)))
segment0 = segment0.cut(cq.Workplane('XY').center(part_radius, part_radius).circle(segment0_inner_dia / 2).extrude(segment0_length + 0.02).translate((0, 0, segment0_z - 0.01)))
result = segment0 if result is None else result.union(segment0)
segment1 = (cq.Workplane('XY').center(part_radius, part_radius).circle(segment1_outer_dia / 2).extrude(segment1_length).translate((0, 0, segment1_z)))
segment1 = segment1.cut(cq.Workplane('XY').center(part_radius, part_radius).circle(segment1_inner_dia / 2).extrude(segment1_length + 0.02).translate((0, 0, segment1_z - 0.01)))
result = segment1 if result is None else result.union(segment1)
segment2 = (cq.Workplane('XY').center(part_radius, part_radius).circle(segment2_outer_dia / 2).extrude(segment2_length).translate((0, 0, segment2_z)))
segment2 = segment2.cut(cq.Workplane('XY').center(part_radius, part_radius).circle(segment2_inner_dia / 2).extrude(segment2_length + 0.02).translate((0, 0, segment2_z - 0.01)))
result = segment2 if result is None else result.union(segment2)
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_dia / 2).extrude(-(hole0_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole0_x, hole0_y)]).circle(hole0_cbore_dia / 2).extrude(-(hole0_cbore_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole1_x, hole1_y)]).circle(hole1_dia / 2).extrude(-(hole1_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole1_x, hole1_y)]).circle(hole1_cbore_dia / 2).extrude(-(hole1_cbore_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole2_x, hole2_y)]).circle(hole2_dia / 2).extrude(-(hole2_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole2_x, hole2_y)]).circle(hole2_cbore_dia / 2).extrude(-(hole2_cbore_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole3_x, hole3_y)]).circle(hole3_dia / 2).extrude(-(hole3_depth + 0.01)))
result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + 0.01).pushPoints([(hole3_x, hole3_y)]).circle(hole3_cbore_dia / 2).extrude(-(hole3_cbore_depth + 0.01)))
