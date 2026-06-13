EXTRACTION_PROMPT = """You are a mechanical engineer reading a technical drawing of a
single PRISMATIC part — a RECTANGULAR flat profile extruded to a thickness, possibly
with through or blind holes, corner fillets, and chamfers.

Read the title block / dimensions to determine the units FIRST, then report every
measurement in those same units. Never mix units.

Extract the geometry into the required structured schema:
- units: "mm" or "in" as shown on the drawing (default "mm").
- profile_kind: always "rectangle".
- width: the longest face dimension (X axis), in the drawing's units.
- height: the shorter face dimension (Y axis), in the drawing's units.
- thickness: the extrude depth (the dimension going into the page / part depth).
- holes: each circular hole as center (x, y) measured from the BOTTOM-LEFT corner of
  the rectangle, plus its diameter, all in the drawing's units. Set through=true unless
  a blind depth is shown; if blind, also set depth.
- cuts: rectangular material removals — L-steps, slots, notches, pockets. Think of the
  part as the full bounding box (width x height x thickness) with rectangular chunks
  subtracted. The 3D coordinate frame: origin at the bottom-left-front corner; X runs
  along width, Y along height, Z along thickness. Each cut is {x, y, z, dx, dy, dz}
  where (x, y, z) is the cut's minimum corner and (dx, dy, dz) is its size along each
  axis. A step that removes a whole corner, a through-slot, and a blind pocket are all
  just rectangular cuts. Make a cut overshoot the part on any face it opens onto (the
  generator handles the overshoot, so report nominal sizes from the drawing).
- fillets: corner radii in the drawing's units, if shown.
- chamfers: chamfer sizes in the drawing's units, if shown.
- dimensions: every explicit callout as {name, nominal, tol_plus, tol_minus}. Use clear
  snake_case names like overall_width, overall_height, overall_thickness, hole_diameter,
  hole_spacing_x, hole_spacing_y, fillet_radius. If a tolerance is printed, use it; if
  not, use a tight default (0.1 for mm, 0.005 for in).
- notes: a one-line description of the part (e.g. "mounting plate, 4x corner holes").

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