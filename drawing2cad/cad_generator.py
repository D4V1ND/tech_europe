from pathlib import Path

import cadquery as cq

from .partspec import (
    Dimension,
    ExtrudedGeometry,
    MultiBodyGeometry,
    PartSpec,
    RevolvedGeometry,
    UnsupportedGeometry,
)

_EPS = 0.01


def run_code(code: str, out_dir) -> cq.Workplane:
    """Execute generated CadQuery code and export its source, STEP, and STL files."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    namespace: dict = {}
    exec(code, namespace)
    if "result" not in namespace:
        raise ValueError("Generated code did not define a `result` variable.")
    result = namespace["result"]
    (out_dir / "part.py").write_text(code, encoding="utf-8")
    cq.exporters.export(result, str(out_dir / "part.step"))
    cq.exporters.export(result, str(out_dir / "part.stl"))
    return result


def normalize_to_mm(spec: PartSpec) -> PartSpec:
    """Return a deep copy with every dimensional value converted to millimetres."""
    if spec.units == "mm":
        return spec
    scale = 25.4
    geometry = spec.geometry
    if isinstance(geometry, ExtrudedGeometry):
        geometry = geometry.model_copy(update={
            "width": None if geometry.width is None else geometry.width * scale,
            "height": None if geometry.height is None else geometry.height * scale,
            "diameter": None if geometry.diameter is None else geometry.diameter * scale,
            "profile_points": [
                point.model_copy(update={"x": point.x * scale, "y": point.y * scale})
                for point in geometry.profile_points
            ],
            "thickness": geometry.thickness * scale,
            "corner_radius": geometry.corner_radius * scale,
        })
    elif isinstance(geometry, RevolvedGeometry):
        geometry = geometry.model_copy(update={
            "segments": [segment.model_copy(update={
                "z_start": segment.z_start * scale,
                "z_end": segment.z_end * scale,
                "outer_diameter": segment.outer_diameter * scale,
                "inner_diameter": segment.inner_diameter * scale,
            }) for segment in geometry.segments]
        })
    elif isinstance(geometry, MultiBodyGeometry):
        geometry = geometry.model_copy(update={
            "bodies": [b.model_copy(update={
                "x": b.x * scale, "y": b.y * scale, "z": b.z * scale,
                "dx": None if b.dx is None else b.dx * scale,
                "dy": None if b.dy is None else b.dy * scale,
                "dz": None if b.dz is None else b.dz * scale,
                "diameter": None if b.diameter is None else b.diameter * scale,
                "length": None if b.length is None else b.length * scale,
            }) for b in geometry.bodies]
        })
    elif isinstance(geometry, UnsupportedGeometry):
        geometry = geometry.model_copy(update={
            "envelope_width": None if geometry.envelope_width is None else geometry.envelope_width * scale,
            "envelope_height": None if geometry.envelope_height is None else geometry.envelope_height * scale,
            "envelope_depth": None if geometry.envelope_depth is None else geometry.envelope_depth * scale,
        })
    return spec.model_copy(update={
        "units": "mm",
        "geometry": geometry,
        "holes": [hole.model_copy(update={
            "x": hole.x * scale,
            "y": hole.y * scale,
            "diameter": hole.diameter * scale,
            "depth": None if hole.depth is None else hole.depth * scale,
            "counterbore_diameter": (
                None if hole.counterbore_diameter is None
                else hole.counterbore_diameter * scale
            ),
            "counterbore_depth": (
                None if hole.counterbore_depth is None else hole.counterbore_depth * scale
            ),
            "countersink_diameter": (
                None if hole.countersink_diameter is None
                else hole.countersink_diameter * scale
            ),
        }) for hole in spec.holes],
        "cuts": [cut.model_copy(update={
            "x": cut.x * scale, "y": cut.y * scale, "z": cut.z * scale,
            "dx": cut.dx * scale, "dy": cut.dy * scale, "dz": cut.dz * scale,
            "corner_radius": cut.corner_radius * scale,
        }) for cut in spec.cuts],
        "fillets": [radius * scale for radius in spec.fillets],
        "chamfers": [distance * scale for distance in spec.chamfers],
        "dimensions": [Dimension(
            name=dimension.name,
            nominal=dimension.nominal * scale,
            tol_plus=dimension.tol_plus * scale,
            tol_minus=dimension.tol_minus * scale,
        ) for dimension in spec.dimensions],
    })


def _append_hole_parameters(lines: list[str], spec: PartSpec) -> None:
    for index, hole in enumerate(spec.holes):
        lines.extend([
            f"hole{index}_x = {float(hole.x)}",
            f"hole{index}_y = {float(hole.y)}",
            f"hole{index}_dia = {float(hole.diameter)}",
        ])
        if hole.depth is not None:
            lines.append(f"hole{index}_depth = {float(hole.depth)}")
        if hole.counterbore_diameter is not None:
            lines.append(f"hole{index}_cbore_dia = {float(hole.counterbore_diameter)}")
        if hole.counterbore_depth is not None:
            lines.append(f"hole{index}_cbore_depth = {float(hole.counterbore_depth)}")
        if hole.countersink_diameter is not None:
            lines.append(f"hole{index}_csink_dia = {float(hole.countersink_diameter)}")
        if hole.countersink_angle is not None:
            lines.append(f"hole{index}_csink_angle = {float(hole.countersink_angle)}")


def _append_hole_cuts(lines: list[str], spec: PartSpec, thickness: float) -> None:
    for index, hole in enumerate(spec.holes):
        is_blind = hole.hole_type in ("blind", "threaded") and hole.depth is not None
        if is_blind or (hole.hole_type in ("counterbore", "countersink") and hole.depth):
            length = f"hole{index}_depth + {_EPS}"
        else:
            length = f"part_thickness + {2 * _EPS}"
        lines.append(
            f"result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + {_EPS})"
            f".pushPoints([(hole{index}_x, hole{index}_y)]).circle(hole{index}_dia / 2)"
            f".extrude(-({length})))"
        )
        if hole.hole_type == "counterbore":
            lines.append(
                f"result = result.cut(cq.Workplane('XY').workplane(offset=part_thickness + {_EPS})"
                f".pushPoints([(hole{index}_x, hole{index}_y)])"
                f".circle(hole{index}_cbore_dia / 2)"
                f".extrude(-(hole{index}_cbore_depth + {_EPS})))"
            )
        elif hole.hole_type == "countersink":
            lines.append(
                f"hole{index}_csink_depth = ((hole{index}_csink_dia - hole{index}_dia) / 2) "
                f"/ math.tan(math.radians(hole{index}_csink_angle / 2))"
            )
            lines.append(
                f"hole{index}_csink = (cq.Workplane('XY')"
                f".workplane(offset=part_thickness + {_EPS})"
                f".center(hole{index}_x, hole{index}_y).circle(hole{index}_csink_dia / 2)"
                f".workplane(offset=-(hole{index}_csink_depth + {_EPS}))"
                f".circle(hole{index}_dia / 2).loft(combine=True))"
            )
            lines.append(f"result = result.cut(hole{index}_csink)")


_AXIS_DIR = {"x": "(1, 0, 0)", "y": "(0, 1, 0)", "z": "(0, 0, 1)"}


def _body_expr(body) -> str:
    """CadQuery expression for one multi-body Body (box or oriented cylinder)."""
    if body.shape == "box":
        return (
            f"cq.Workplane('XY').box({float(body.dx)}, {float(body.dy)}, "
            f"{float(body.dz)}, centered=(False, False, False))"
            f".translate(({float(body.x)}, {float(body.y)}, {float(body.z)}))"
        )
    radius = (body.diameter or 0.0) / 2.0
    length = body.length or 0.0
    x, y, z = body.x, body.y, body.z
    if body.operation == "cut":           # overshoot through the wall for a clean cut
        length += 2 * _EPS
        if body.axis == "x":
            x -= _EPS
        elif body.axis == "y":
            y -= _EPS
        else:
            z -= _EPS
    return (
        f"cq.Workplane('XY').add(cq.Solid.makeCylinder({float(radius)}, {float(length)}, "
        f"cq.Vector({float(x)}, {float(y)}, {float(z)}), cq.Vector{_AXIS_DIR[body.axis]}))"
    )


def spec_to_code(spec: PartSpec) -> str:
    """Generate deterministic CadQuery source for supported PartSpec geometry."""
    spec = normalize_to_mm(spec)
    errors = spec.sanity_check()
    if errors:
        raise ValueError("invalid PartSpec: " + "; ".join(errors))
    geometry = spec.geometry
    if isinstance(geometry, UnsupportedGeometry):
        # Best-effort: approximate an un-encodable part (e.g. bent sheet metal) as a solid
        # bounding block so it still earns overall-size credit. Holes/cuts are skipped --
        # on such parts they lie in faces the axial model can't place reliably.
        if not geometry.has_envelope():
            raise ValueError(f"unsupported geometry (no envelope): {geometry.reason}")
        ew, eh, ed = geometry.bbox()
        return (
            "import cadquery as cq\n\n"
            "# --- APPROXIMATION: unsupported part built as its bounding block ---\n"
            f"# reason: {geometry.reason}\n"
            f"envelope_width = {float(ew)}\n"
            f"envelope_height = {float(eh)}\n"
            f"envelope_depth = {float(ed)}\n"
            "result = cq.Workplane('XY').box(envelope_width, envelope_height, "
            "envelope_depth, centered=(False, False, False))\n"
        )

    if isinstance(geometry, MultiBodyGeometry):
        # Union every 'add' body, then subtract every 'cut' body (cut cylinders = holes
        # in any face). Approximates brackets/weldments/bent sheet metal as oriented plates.
        blines = ["import cadquery as cq", "", "# --- multi-body assembly ---", "result = None"]
        for i, body in enumerate(b for b in geometry.bodies if b.operation == "add"):
            blines.append(f"add{i} = {_body_expr(body)}")
            blines.append(f"result = add{i} if result is None else result.union(add{i})")
        for j, body in enumerate(b for b in geometry.bodies if b.operation == "cut"):
            blines.append(f"cut{j} = {_body_expr(body)}")
            blines.append(f"result = result.cut(cut{j})")
        return "\n".join(blines) + "\n"

    lines = ["import math", "import cadquery as cq", "", "# --- parameters ---"]
    if isinstance(geometry, ExtrudedGeometry):
        if geometry.profile_kind == "rectangle":
            lines.extend([f"width = {float(geometry.width)}", f"height = {float(geometry.height)}"])
        elif geometry.profile_kind == "circle":
            lines.extend([f"diameter = {float(geometry.diameter)}", "radius = diameter / 2"])
        else:
            points = ", ".join(
                f"({float(point.x)}, {float(point.y)})" for point in geometry.profile_points
            )
            lines.append(f"profile_points = [{points}]")
        lines.append(f"part_thickness = {float(geometry.thickness)}")
    else:
        _, _, thickness = geometry.bbox()
        diameter = max(segment.outer_diameter for segment in geometry.segments)
        lines.extend([
            f"part_diameter = {float(diameter)}",
            "part_radius = part_diameter / 2",
            f"part_thickness = {float(thickness)}",
        ])
        for index, segment in enumerate(geometry.segments):
            lines.extend([
                f"segment{index}_z = {float(segment.z_start)}",
                f"segment{index}_length = {float(segment.z_end - segment.z_start)}",
                f"segment{index}_outer_dia = {float(segment.outer_diameter)}",
                f"segment{index}_inner_dia = {float(segment.inner_diameter)}",
            ])
    _append_hole_parameters(lines, spec)
    for index, cut in enumerate(spec.cuts):
        lines.extend([
            f"cut{index}_x = {float(cut.x)}", f"cut{index}_y = {float(cut.y)}",
            f"cut{index}_z = {float(cut.z)}", f"cut{index}_dx = {float(cut.dx)}",
            f"cut{index}_dy = {float(cut.dy)}", f"cut{index}_dz = {float(cut.dz)}",
        ])
        if cut.corner_radius > 0:
            lines.append(f"cut{index}_radius = {float(cut.corner_radius)}")

    lines.extend(["", "# --- base geometry ---"])
    if isinstance(geometry, ExtrudedGeometry):
        if geometry.profile_kind == "rectangle":
            lines.append("result = cq.Workplane('XY').box(width, height, part_thickness, centered=(False, False, False))")
        elif geometry.profile_kind == "circle":
            lines.append("result = cq.Workplane('XY').center(radius, radius).circle(radius).extrude(part_thickness)")
        else:
            lines.append("result = cq.Workplane('XY').polyline(profile_points).close().extrude(part_thickness)")
        if geometry.profile_kind != "circle":
            if geometry.profile_kind == "rectangle" and geometry.corner_radius > 0:
                if geometry.corner_style == "round":
                    lines.append(
                        f"result = result.edges('|Z').fillet({float(geometry.corner_radius)})"
                    )
                else:
                    # scallop: cut a quarter-cylinder notch out of each of the 4 corners.
                    cw, ch, _ = geometry.bbox()
                    lines.append(f"corner_radius = {float(geometry.corner_radius)}")
                    for cx, cy in ((0.0, 0.0), (cw, 0.0), (0.0, ch), (cw, ch)):
                        lines.append(
                            f"result = result.cut(cq.Workplane('XY')"
                            f".pushPoints([({float(cx)}, {float(cy)})]).circle(corner_radius)"
                            f".extrude(part_thickness + {2 * _EPS}).translate((0, 0, -{_EPS})))"
                        )
            elif spec.fillets:
                lines.append(f"result = result.edges('|Z').fillet({float(max(spec.fillets))})")
            # skip |Z chamfer when corner_radius already consumed those edges
            if spec.chamfers and not (geometry.profile_kind == "rectangle" and geometry.corner_radius > 0):
                lines.append(f"result = result.edges('|Z').chamfer({float(max(spec.chamfers))})")
    else:
        lines.append("result = None")
        for index, segment in enumerate(geometry.segments):
            lines.append(
                f"segment{index} = (cq.Workplane('XY').center(part_radius, part_radius)"
                f".circle(segment{index}_outer_dia / 2).extrude(segment{index}_length)"
                f".translate((0, 0, segment{index}_z)))"
            )
            if segment.inner_diameter > 0:
                lines.append(
                    f"segment{index} = segment{index}.cut(cq.Workplane('XY')"
                    f".center(part_radius, part_radius).circle(segment{index}_inner_dia / 2)"
                    f".extrude(segment{index}_length + {2 * _EPS})"
                    f".translate((0, 0, segment{index}_z - {_EPS})))"
                )
            lines.append(f"result = segment{index} if result is None else result.union(segment{index})")

    _append_hole_cuts(lines, spec, spec.bbox()[2])

    if isinstance(geometry, ExtrudedGeometry):
        width, height, thickness = geometry.bbox()
        for index, cut in enumerate(spec.cuts):
            ox = _EPS if cut.x <= 1e-6 else 0.0
            ex = _EPS if cut.x + cut.dx >= width - 1e-6 else 0.0
            oy = _EPS if cut.y <= 1e-6 else 0.0
            ey = _EPS if cut.y + cut.dy >= height - 1e-6 else 0.0
            oz = _EPS if cut.z <= 1e-6 else 0.0
            ez = _EPS if cut.z + cut.dz >= thickness - 1e-6 else 0.0
            lines.append(
                f"cut{index}_solid = (cq.Workplane('XY')"
                f".box(cut{index}_dx + {ox + ex}, cut{index}_dy + {oy + ey}, "
                f"cut{index}_dz + {oz + ez}, centered=(False, False, False)))"
            )
            if cut.corner_radius > 0:
                # Round the pocket's 4 vertical corners so the wall stays continuous
                # around the matching outer fillet (tray/pocket case).
                lines.append(
                    f"cut{index}_solid = cut{index}_solid.edges('|Z').fillet(cut{index}_radius)"
                )
            lines.append(
                f"result = result.cut(cut{index}_solid"
                f".translate((cut{index}_x - {ox}, cut{index}_y - {oy}, cut{index}_z - {oz})))"
            )
    return "\n".join(lines) + "\n"


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:text.rfind("```")]
    return text.strip()


def _generate_code_llm(spec: PartSpec, feedback: str | None, *, model) -> str:
    from drawing2cad.prompts import GEN_SYSTEM

    user = f"PartSpec JSON:\n{spec.model_dump_json(indent=2)}"
    if feedback:
        user += f"\n\nThe previous attempt failed. Fix these checks:\n{feedback}"
    response = model.invoke([("system", GEN_SYSTEM), ("user", user)])
    return _strip_fences(response.content)


def generate_code(spec: PartSpec, feedback: str | None = None, *, model=None, use_llm: bool = False) -> str:
    if use_llm:
        if model is None:
            raise ValueError("use_llm=True requires a model")
        return _generate_code_llm(spec, feedback, model=model)
    return spec_to_code(spec)


if __name__ == "__main__":
    import sys

    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("drawing2cad/outputs/test_5.json")
    loaded_spec = PartSpec.model_validate_json(json_path.read_text(encoding="utf-8"))
    generated_code = generate_code(loaded_spec)
    output_dir = Path("out") / json_path.stem
    run_code(generated_code, output_dir)
    print(f"Output written to {output_dir}")
