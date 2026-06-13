EXTRACTION_PROMPT = """You are a mechanical engineer reading a technical drawing of a
single PRISMATIC part (a flat profile extruded to a thickness, possibly with holes,
fillets, and chamfers).

Extract the geometry into the required structured schema:
- units: "mm" or "in" as shown on the drawing (default mm).
- profile_kind: "rectangle" if the outline is a rectangle, else "polygon".
- For a rectangle: width (X) and height (Y). For a polygon: the outline points in mm,
  counter-clockwise, starting at the bottom-left, origin at the bottom-left corner.
- thickness: the extrude depth (the dimension NOT visible in the main face view).
- holes: each hole center (x, y) in mm measured from the bottom-left origin, its
  diameter, and whether it is a through hole.
- fillets / chamfers: corner radii / chamfer sizes in mm if called out.
- dimensions: list every explicit linear/diameter callout as {name, nominal}.

Report numbers exactly as dimensioned. Do not invent dimensions that are not shown.
"""