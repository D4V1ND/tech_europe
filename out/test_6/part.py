import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').box(28.0, 60.0, 26.0, centered=(False, False, False)).translate((42.0, 0.0, 54.0))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XZ').workplane(offset=-50.0).polyline([(17.0, 0.0), (42.0, 0.0), (42.0, 54.0), (17.0, 54.0), (5.0, 48.0), (0.0, 38.0), (0.0, 16.0), (5.0, 6.0)]).close().extrude(-10.0)
result = add1 if result is None else result.union(add1)
add2 = cq.Workplane('XZ').workplane(offset=-0.0).polyline([(17.0, 0.0), (42.0, 0.0), (42.0, 54.0), (17.0, 54.0), (5.0, 48.0), (0.0, 38.0), (0.0, 16.0), (5.0, 6.0)]).close().extrude(-10.0)
result = add2 if result is None else result.union(add2)
add3 = cq.Workplane('YZ').workplane(offset=42.0).polyline([(0.0, 0.0), (26.0, 0.0), (26.0, 30.0), (12.0, 48.0), (0.0, 60.0)]).close().extrude(28.0)
result = add3 if result is None else result.union(add3)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(9.0, 12.02, cq.Vector(21.0, 49.99, 27.0), cq.Vector(0, 1, 0)))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(9.0, 12.02, cq.Vector(21.0, -1.01, 27.0), cq.Vector(0, 1, 0)))
result = result.cut(cut1)
