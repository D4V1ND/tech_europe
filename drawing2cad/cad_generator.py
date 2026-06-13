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
