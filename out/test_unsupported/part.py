import cadquery as cq

# --- APPROXIMATION: unsupported part built as its bounding block ---
# reason: Bent sheet metal bracket with side plates and multi-plane holes.
envelope_width = 116.0
envelope_height = 105.0
envelope_depth = 100.0
result = cq.Workplane('XY').box(envelope_width, envelope_height, envelope_depth, centered=(False, False, False))
