import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(25.0, 15.0, cq.Vector(25.0, 0.0, 25.0), cq.Vector(0, 1, 0)))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(25.0, 15.0, cq.Vector(25.0, 35.0, 25.0), cq.Vector(0, 1, 0)))
result = add1 if result is None else result.union(add1)
add2 = cq.Workplane('XY').box(50.0, 50.0, 25.2, centered=(False, False, False)).translate((0.0, 0.0, 24.9))
result = add2 if result is None else result.union(add2)
add3 = cq.Workplane('XY').box(20.0, 50.0, 25.0, centered=(False, False, False)).translate((15.0, 0.0, 50.0))
result = add3 if result is None else result.union(add3)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(10.0, 50.02, cq.Vector(25.0, -0.01, 25.0), cq.Vector(0, 1, 0)))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').box(22.0, 16.0, 16.0, centered=(False, False, False)).translate((14.0, 35.0, 60.0))
result = result.cut(cut1)
