import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').workplane(offset=97.0).moveTo(0.0, 8.0).lineTo(116.0, 8.0).lineTo(116.0, 98.0).threePointArc((113.95, 102.95), (109.0, 105.0)).lineTo(7.0, 105.0).threePointArc((2.05, 102.95), (0.0, 98.0)).close().extrude(3.0)
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XZ').workplane(offset=-0.0).moveTo(0.0, 7.0).threePointArc((2.05, 2.05), (7.0, 0.0)).lineTo(39.0, 0.0).threePointArc((43.95, 2.05), (46.0, 7.0)).lineTo(46.0, 100.0).lineTo(0.0, 100.0).close().extrude(-3.0)
result = add1 if result is None else result.union(add1)
add2 = cq.Workplane('XZ').workplane(offset=-0.0).moveTo(70.0, 7.0).threePointArc((72.05, 2.05), (77.0, 0.0)).lineTo(109.0, 0.0).threePointArc((113.95, 2.05), (116.0, 7.0)).lineTo(116.0, 100.0).lineTo(70.0, 100.0).close().extrude(-3.0)
result = add2 if result is None else result.union(add2)
add3 = cq.Workplane('XY').box(116.0, 3.0, 30.0, centered=(False, False, False)).translate((0.0, 0.0, 70.0))
result = add3 if result is None else result.union(add3)
add4 = cq.Workplane('YZ').workplane(offset=0.0).moveTo(0.0, 0.0).lineTo(0.0, 100.0).lineTo(105.0, 100.0).lineTo(38.65, 11.95).threePointArc((28.08, 3.16), (14.69, 0.0)).close().extrude(3.0)
result = add4 if result is None else result.union(add4)
add5 = cq.Workplane('YZ').workplane(offset=113.0).moveTo(0.0, 0.0).lineTo(0.0, 100.0).lineTo(105.0, 100.0).lineTo(38.65, 11.95).threePointArc((28.08, 3.16), (14.69, 0.0)).close().extrude(3.0)
result = add5 if result is None else result.union(add5)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(41.0, 8.02, cq.Vector(58.0, 55.0, 94.99), cq.Vector(0, 0, 1)))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 6.02, cq.Vector(35.0, -1.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut1)
cut2 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 6.02, cq.Vector(81.0, -1.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut2)
