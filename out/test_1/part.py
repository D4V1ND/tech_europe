import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(38.0, 18.0, cq.Vector(38.0, 38.0, 0.0), cq.Vector(0, 0, 1)))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XY').add(cq.Solid.makeCylinder(24.0, 8.0, cq.Vector(38.0, 38.0, 18.0), cq.Vector(0, 0, 1)))
result = add1 if result is None else result.union(add1)
cut0 = cq.Workplane('XY').add(cq.Solid.makeCylinder(2.5, 19.02, cq.Vector(38.0, -0.01, 7.0), cq.Vector(0, 1, 0)))
result = result.cut(cut0)
