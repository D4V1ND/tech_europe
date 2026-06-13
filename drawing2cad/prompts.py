EXTRACTION_PROMPT = """You are a mechanical engineer reading a technical drawing of a
single PRISMATIC part — a RECTANGULAR flat profile extruded to a thickness, possibly
with through or blind holes, corner fillets, and chamfers.

Extract the geometry into the required structured schema:
- units: "mm" or "in" as shown on the drawing (default mm).
- profile_kind: always "rectangle".
- width: the longest face dimension (X axis) in the given units.
- height: the shorter face dimension (Y axis) in the given units.
- thickness: the extrude depth (the dimension going into the page / part depth).
- holes: each circular hole as center (x, y) measured from the bottom-left corner of
  the rectangle, plus its diameter. Mark through=true unless a depth is shown.
- fillets: corner radii in mm if shown.
- chamfers: chamfer sizes in mm if shown.
- dimensions: every explicit linear or diameter callout as {name, nominal}.

Only extract what is explicitly shown. Do not invent values. If the drawing shows a
round or revolved part rather than a flat rectangular plate, extract the best
rectangular approximation using the overall envelope dimensions.
"""

GEN_SYSTEM = """You are a CAD engineer. Given a PartSpec as JSON, write a CadQuery
(Python) script that reconstructs the part. Requirements:
- Put EVERY dimension as a named variable at the top of the script.
- Build the solid into a variable named exactly `result`.
- Origin convention: build the box with centered=(False, False, False) so its corner is
  at (0,0,0). The PartSpec hole coordinates (x, y) are then ABSOLUTE world coordinates.
- Cut holes as cylinders on the world XY plane at the absolute (x, y); do NOT use
  .faces('>Z').workplane() (its local origin/axes are ambiguous).
- Through holes span the full thickness; blind holes go down by `depth` from the top.
- Apply corner fillets/chamfers via .edges('|Z') AFTER cutting all holes.
- Output ONLY Python code, no prose, no markdown fences.
"""