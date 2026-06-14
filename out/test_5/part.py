import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').box(116.0, 105.0, 3.0, centered=(False, False, False)).translate((0.0, 0.0, 97.0))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XY').box(43.0, 3.0, 100.0, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add1 if result is None else result.union(add1)
add2 = cq.Workplane('XY').box(43.0, 3.0, 100.0, centered=(False, False, False)).translate((73.0, 0.0, 0.0))
result = add2 if result is None else result.union(add2)
add3 = cq.Workplane('YZ').workplane(offset=0.0).polyline([(0.0, 0.0), (0.0, 100.0), (105.0, 100.0), (88.0, 72.0), (64.0, 45.0), (42.0, 20.0), (30.0, 0.0)]).close().extrude(3.0)
result = add3 if result is None else result.union(add3)
add4 = cq.Workplane('YZ').workplane(offset=113.0).polyline([(0.0, 0.0), (0.0, 100.0), (105.0, 100.0), (88.0, 72.0), (64.0, 45.0), (42.0, 20.0), (30.0, 0.0)]).close().extrude(3.0)
result = add4 if result is None else result.union(add4)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(41.0, 8.02, cq.Vector(58.0, 55.0, 94.99), cq.Vector(0, 0, 1)))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 6.02, cq.Vector(35.0, -1.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut1)
cut2 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 6.02, cq.Vector(81.0, -1.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut2)
