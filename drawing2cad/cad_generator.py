from pathlib import Path
import cadquery as cq
from .partspec import PartSpec

# Small overshoot (mm) so hole cuts don't leave coplanar faces that confuse the kernel.
_EPS = 0.01


def run_code(code: str, out_dir) -> cq.Workplane:
    """Execute generated CadQuery code, returning the `result` Workplane and exporting
    part.py / part.step / part.stl into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    namespace: dict = {}
    exec(code, namespace)                       # generated code, sandboxed namespace
    if "result" not in namespace:
        raise ValueError("Generated code did not define a `result` variable.")
    result = namespace["result"]

    (out_dir / "part.py").write_text(code)
    cq.exporters.export(result, str(out_dir / "part.step"))
    cq.exporters.export(result, str(out_dir / "part.stl"))
    return result


def normalize_to_mm(spec: PartSpec) -> PartSpec:
    """Return a copy of the spec with all lengths in mm. CadQuery is unitless and STEP
    defaults to mm, so an inch spec built as-is would be 25.4x too small in every CAD
    tool. Convert once here and work in mm everywhere downstream (incl. the validator)."""
    if spec.units == "mm":
        return spec
    s = 25.4
    return spec.model_copy(update={
        "units": "mm",
        "width": None if spec.width is None else spec.width * s,
        "height": None if spec.height is None else spec.height * s,
        "thickness": spec.thickness * s,
        "holes": [h.model_copy(update={
            "x": h.x * s, "y": h.y * s, "diameter": h.diameter * s,
            "depth": None if h.depth is None else h.depth * s,
        }) for h in spec.holes],
        "cuts": [c.model_copy(update={
            "x": c.x * s, "y": c.y * s, "z": c.z * s,
            "dx": c.dx * s, "dy": c.dy * s, "dz": c.dz * s,
        }) for c in spec.cuts],
        "fillets": [r * s for r in spec.fillets],
        "chamfers": [c * s for c in spec.chamfers],
    })


def spec_to_code(spec: PartSpec) -> str:
    """Deterministic PartSpec -> CadQuery source. Rectangle + through/blind holes.

    Origin convention: part corner at (0,0,0), so model coords == profile coords and the
    validator can use bb.xmin/ymin/zmin == 0. No -width/2 arithmetic. Holes are cut as
    absolute cylinders on the world XY plane, avoiding workplane-origin/axis ambiguity."""
    spec = normalize_to_mm(spec)
    if spec.profile_kind != "rectangle" or spec.width is None or spec.height is None:
        raise ValueError("spec_to_code supports rectangular profiles only.")

    lines = ["import cadquery as cq", ""]
    lines.append("# --- parameters (editable) ---")
    lines.append(f"width = {float(spec.width)}")
    lines.append(f"height = {float(spec.height)}")
    lines.append(f"thickness = {float(spec.thickness)}")
    for i, h in enumerate(spec.holes):
        lines.append(f"hole{i}_x = {float(h.x)}")
        lines.append(f"hole{i}_y = {float(h.y)}")
        lines.append(f"hole{i}_dia = {float(h.diameter)}")
        if not h.through and h.depth is not None:
            lines.append(f"hole{i}_depth = {float(h.depth)}")
    for i, c in enumerate(spec.cuts):
        lines.append(f"cut{i}_x = {float(c.x)}")
        lines.append(f"cut{i}_y = {float(c.y)}")
        lines.append(f"cut{i}_z = {float(c.z)}")
        lines.append(f"cut{i}_dx = {float(c.dx)}")
        lines.append(f"cut{i}_dy = {float(c.dy)}")
        lines.append(f"cut{i}_dz = {float(c.dz)}")
    lines.append("")

    lines.append("# --- build: corner at origin, so model coords == profile coords ---")
    lines.append("result = cq.Workplane('XY').box(width, height, thickness, "
                 "centered=(False, False, False))")

    # Holes: cut absolute cylinders from the top face downward (no workplane ambiguity).
    for i, h in enumerate(spec.holes):
        if h.through or h.depth is None:
            # span the whole thickness with overshoot on both ends
            top = f"thickness + {_EPS}"
            length = f"thickness + {2 * _EPS}"
        else:
            # blind: from the top surface down by depth (overshoot only above the top)
            top = f"thickness + {_EPS}"
            length = f"hole{i}_depth + {_EPS}"
        lines.append(
            f"result = result.cut(cq.Workplane('XY').workplane(offset={top})"
            f".pushPoints([(hole{i}_x, hole{i}_y)]).circle(hole{i}_dia / 2)"
            f".extrude(-({length})))"
        )

    # Rectangular cuts (L-steps, slots, notches). Overshoot only the faces the cut
    # actually reaches, so open slots boolean cleanly while internal pockets stay exact.
    w, ht, th = float(spec.width), float(spec.height), float(spec.thickness)
    _tol = 1e-6
    for i, c in enumerate(spec.cuts):
        ox = _EPS if c.x <= _tol else 0.0                       # reaches left face
        ex = _EPS if c.x + c.dx >= w - _tol else 0.0            # reaches right face
        oy = _EPS if c.y <= _tol else 0.0
        ey = _EPS if c.y + c.dy >= ht - _tol else 0.0
        oz = _EPS if c.z <= _tol else 0.0
        ez = _EPS if c.z + c.dz >= th - _tol else 0.0
        lines.append(
            f"result = result.cut(cq.Workplane('XY')"
            f".box(cut{i}_dx + {ox + ex}, cut{i}_dy + {oy + ey}, cut{i}_dz + {oz + ez}, "
            f"centered=(False, False, False))"
            f".translate((cut{i}_x - {ox}, cut{i}_y - {oy}, cut{i}_z - {oz})))"
        )

    # Fillets/chamfers LAST: a top-edge fillet changes the >Z face, so holes must be
    # cut before this. '|Z' selects the 4 vertical corner edges.
    for r in spec.fillets:
        lines.append(f"result = result.edges('|Z').fillet({float(r)})")
    for c in spec.chamfers:
        lines.append(f"result = result.edges('|Z').chamfer({float(c)})")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Optional LLM fallback (kept behind a flag for the "agentic" story / exotic specs).
# Deterministic spec_to_code is the default and can never die from generator variance.
# ---------------------------------------------------------------------------

def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t        # drop opening ```lang line
        if t.endswith("```"):
            t = t[: t.rfind("```")]
    return t.strip()


def _generate_code_llm(spec: PartSpec, feedback: str | None, *, model) -> str:
    """Turn a PartSpec into CadQuery source via an LLM. `feedback` carries validation
    diffs on retry."""
    from drawing2cad.prompts import GEN_SYSTEM   # lazy import — only when LLM is used
    user = f"PartSpec JSON:\n{spec.model_dump_json(indent=2)}"
    if feedback:
        user += ("\n\nThe previous attempt FAILED these checks. Fix the code so the "
                 f"measured geometry matches:\n{feedback}")
    messages = [("system", GEN_SYSTEM), ("user", user)]
    resp = model.invoke(messages)
    return _strip_fences(resp.content)


def generate_code(spec: PartSpec, feedback: str | None = None, *,
                  model=None, use_llm: bool = False) -> str:
    """Produce CadQuery source for a PartSpec.

    Default (use_llm=False): deterministic spec_to_code -- stable, no API key, the demo
    can't die from model variance. Set use_llm=True (and pass `model`) to use the LLM
    fallback for cases the deterministic path can't express yet."""
    if use_llm:
        if model is None:
            raise ValueError("use_llm=True requires a `model`.")
        return _generate_code_llm(spec, feedback, model=model)
    return spec_to_code(spec)

# generate_code -> spec_to_code -> run_code -> normalize_to_mm

if __name__ == "__main__":
    import json
    import sys

    json_path = sys.argv[1] if len(sys.argv) > 1 else "drawing2cad/outputs/test_2.json"

    # 1. Load PartSpec from JSON file
    spec = PartSpec.model_validate_json(Path(json_path).read_text())
    print(f"Loaded spec from {json_path}")

    # 2. generate_code calls spec_to_code (which calls normalize_to_mm internally)
    code = generate_code(spec)
    print("=== Generated CadQuery code ===")
    print(code)

    # 3. run_code executes the code and writes part.py / part.step / part.stl to out/
    result = run_code(code, out_dir="out")
    print("Output written to out/  (part.py, part.step, part.stl)")
