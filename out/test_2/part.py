import cadquery as cq

# --- multi-body assembly ---
result = None
add0 = cq.Workplane('XY').box(44.449999999999996, 12.7, 31.75, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add0 if result is None else result.union(add0)
add1 = cq.Workplane('XY').box(12.7, 31.75, 31.75, centered=(False, False, False)).translate((0.0, 0.0, 0.0))
result = add1 if result is None else result.union(add1)
cut0 = cq.Workplane('XY').box(25.4, 12.7, 6.35, centered=(False, False, False)).translate((19.049999999999997, 0.0, 12.7))
result = result.cut(cut0)
cut1 = cq.Workplane('XY').box(12.7, 6.35, 19.049999999999997, centered=(False, False, False)).translate((0.0, 25.4, 6.35))
result = result.cut(cut1)
