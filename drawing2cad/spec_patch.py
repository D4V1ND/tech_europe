"""Apply a single looked-up value (e.g. a Tavily suggestion) into a PartSpec.

Returns a patched copy -- the caller regenerates and re-validates. Deterministic and
LLM-free: it only sets the one field the user accepted, so it's fast and safe to run
synchronously. Where the field maps to the extruded envelope (thickness/width/height/
diameter) the geometry actually changes; otherwise the value is recorded as a named
dimension so the parameter table and validation reflect it.
"""
from drawing2cad.partspec import Dimension, ExtrudedGeometry, PartSpec

# field name (lowercased) -> ExtrudedGeometry attribute it drives
_ENVELOPE = {
    "thickness": "thickness", "overall_thickness": "thickness",
    "width": "width", "overall_width": "width",
    "height": "height", "overall_height": "height",
    "diameter": "diameter", "overall_diameter": "diameter",
}


def apply_field(spec: PartSpec, field: str, value: float) -> PartSpec:
    spec = spec.model_copy(deep=True)
    geo = spec.geometry
    key = field.lower()

    target = _ENVELOPE.get(key)
    if isinstance(geo, ExtrudedGeometry) and target is not None:
        spec.geometry = geo.model_copy(update={target: value})
    elif key in ("hole_diameter", "hole_dia", "diameter") and len(spec.holes) == 1:
        spec.holes = [spec.holes[0].model_copy(update={"diameter": value})]

    # Always record the accepted value as a named dimension so it shows in the spec.
    dims = list(spec.dimensions)
    for i, d in enumerate(dims):
        if d.name.lower() == key:
            dims[i] = d.model_copy(update={"nominal": value})
            break
    else:
        dims.append(Dimension(name=field, nominal=value))
    spec.dimensions = dims
    return spec
