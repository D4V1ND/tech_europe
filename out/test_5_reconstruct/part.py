import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').box(116.0, 105.0, 3.0, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XY').box(3.0, 105.0, 100.0, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add1 if result is None else result.union(add1)
add2 = cq.Workplane('XY').box(3.0, 105.0, 100.0, centered=(False, False, False)).translate((113.0, 0.0, 0.0))
result = add2 if result is None else result.union(add2)
add3 = cq.Workplane('XY').box(116.0, 3.0, 100.0, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add3 if result is None else result.union(add3)
add4 = cq.Workplane('XY').box(116.0, 105.0, 3.0, centered=(False, False, False)).translate((0.0, 0.0, 97.0))
result = add4 if result is None else result.union(add4)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(41.0, 5.02, cq.Vector(58.0, 50.0, -1.01), cq.Vector(0, 0, 1)))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 5.02, cq.Vector(35.0, -0.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut1)
cut2 = cq.Workplane('XY').add(cq.Solid.makeCylinder(6.0, 5.02, cq.Vector(81.0, -0.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut2)
