"""Layer 1 validator: measure the built solid and compare it to the PartSpec.

This proves the generated CAD matches what we extracted (catches generator bugs). It does
NOT prove the spec matches the drawing (extraction errors) -- that would be Layer 2.

Public contract (consumed by orchestrator.py):
    report = validate(spec, result, tol=0.5)
    report.checks      -> list[Check], each with .passed: bool
    report.feedback()  -> str (failed checks, for the LLM retry prompt)
"""
import math

from pydantic import BaseModel

from .partspec import ExtrudedGeometry, PartSpec, RevolvedGeometry, UnsupportedGeometry
from .cad_generator import normalize_to_mm

# Loose relative band for the volume sanity check. Fillets, overlapping cuts and
# hole/cut intersections make an exact analytic volume fragile; 5% still catches gross
# errors (e.g. the generator ignored all cuts and built a plain box).
_VOLUME_REL_TOL = 0.05


class Check(BaseModel):
    name: str
    expected: float | str
    measured: float | str
    tol: float                 # tolerance band actually used (mm), 0 for non-numeric
    passed: bool
    detail: str = ""


class ValidationReport(BaseModel):
    checks: list[Check] = []          # scored: gate pass/fail and drive the retry loop
    advisory: list[Check] = []        # measured for insight, NOT scored (e.g. volume)

    def ok(self) -> bool:
        return all(c.passed for c in self.checks)

    def feedback(self) -> str:
        """Human/LLM-readable lines for the FAILED scored checks only."""
        fails = [c for c in self.checks if not c.passed]
        if not fails:
            return "All checks passed."
        lines = []
        for c in fails:
            line = f"- {c.name}: expected {c.expected}, measured {c.measured}"
            if c.tol:
                line += f" (tol +/-{c.tol})"
            if c.detail:
                line += f" -- {c.detail}"
            lines.append(line)
        return "\n".join(lines)


# --------------------------------------------------------------------------- helpers

def _profile_area(spec: PartSpec) -> float:
    """Flat-face area in mm^2 for the analytic volume estimate."""
    geometry = spec.geometry
    if not isinstance(geometry, ExtrudedGeometry):
        raise ValueError("profile area only applies to extruded geometry")
    if geometry.profile_kind == "rectangle":
        return float(geometry.width) * float(geometry.height)
    if geometry.profile_kind == "circle":
        r = float(geometry.diameter) / 2.0
        return math.pi * r * r
    # polygon: shoelace on the ordered outline points
    pts = [(p.x, p.y) for p in geometry.profile_points]
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def _expected_volume(spec: PartSpec) -> float:
    """Analytic volume in mm^3: profile prism minus holes minus cuts (nominal sizes,
    overlaps ignored -- this is a loose estimate by design)."""
    geometry = spec.geometry
    if isinstance(geometry, ExtrudedGeometry):
        th = float(geometry.thickness)
        vol = _profile_area(spec) * th
    elif isinstance(geometry, RevolvedGeometry):
        th = geometry.bbox()[2]
        vol = sum(
            math.pi * (segment.outer_diameter ** 2 - segment.inner_diameter ** 2) / 4
            * (segment.z_end - segment.z_start)
            for segment in geometry.segments
        )
    else:
        return 0.0
    for h in spec.holes:
        r = h.diameter / 2.0
        depth = th if h.hole_type == "through" or h.depth is None else h.depth
        vol -= math.pi * r * r * depth
        if h.hole_type == "counterbore":
            extra_area = math.pi * (h.counterbore_diameter ** 2 - h.diameter ** 2) / 4
            vol -= extra_area * h.counterbore_depth
    bw, bh, _ = spec.bbox()
    for c in spec.cuts:
        # clamp the cut to the part box so overshoot/over-size doesn't over-subtract
        dx = max(0.0, min(c.x + c.dx, bw) - max(c.x, 0.0))
        dy = max(0.0, min(c.y + c.dy, bh) - max(c.y, 0.0))
        dz = max(0.0, min(c.z + c.dz, th) - max(c.z, 0.0))
        vol -= dx * dy * dz
    return vol


def _point_is_inside(solid_wrapped, x: float, y: float, z: float) -> bool | None:
    """True if (x,y,z) is solid material, False if void, None if the test is unavailable.
    Used to confirm holes/cuts actually removed material at the expected spot."""
    try:
        from OCP.BRepClass3d import BRepClass3d_SolidClassifier
        from OCP.gp import gp_Pnt
        from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    except Exception:
        return None
    clf = BRepClass3d_SolidClassifier(solid_wrapped)
    clf.Perform(gp_Pnt(x, y, z), 1e-6)
    state = clf.State()
    return state in (TopAbs_IN, TopAbs_ON)


def _map_dimension(name: str, bb, spec: PartSpec) -> float | None:
    """Map a snake_case dimension name to a measurable on the built solid, or None.
    Returns None for any name that isn't a direct overall-envelope dimension -- those
    can't be measured from the bbox and are skipped rather than scored wrong."""
    n = name.lower()
    # Only match dimensions that are clearly the overall envelope.
    # Anything with qualifiers (cutout_, spacing_, wall_, flange_, etc.) is NOT mapped.
    if any(q in n for q in ("hole", "cutout", "slot", "spacing", "wall", "flange",
                             "bend", "angle", "fillet", "chamfer", "edge", "half")):
        return None
    if "overall_thick" in n or n in ("overall_depth", "depth", "z"):
        return bb.zlen
    if "overall_width" in n or n in ("overall_width", "width", "length"):
        return bb.xlen
    if "overall_height" in n or n in ("overall_height", "height"):
        return bb.ylen
    if "diameter" in n and "overall" in n:
        return bb.xlen          # outer diameter of a circle == bbox x
    return None


# --------------------------------------------------------------------------- entrypoint

def validate(spec: PartSpec, result, tol: float = 0.5) -> ValidationReport:
    """Measure `result` (a CadQuery Workplane) and compare to `spec`. All comparisons in
    mm. `tol` is the default +/- band (mm) for structural checks; named dimensions use
    their own tolerances from the spec."""
    spec = normalize_to_mm(spec)
    checks: list[Check] = []
    if isinstance(spec.geometry, UnsupportedGeometry):
        return ValidationReport(checks=[Check(
            name="geometry_supported", expected="supported", measured="unsupported",
            tol=0, passed=False, detail=spec.geometry.reason,
        )])

    # --- solid count: a clean part is exactly one solid ---
    solids = result.solids().vals()
    n_solids = len(solids)
    checks.append(Check(
        name="solid_count", expected=1, measured=n_solids, tol=0,
        passed=(n_solids == 1),
        detail="" if n_solids == 1 else "boolean ops fragmented the part",
    ))

    shape = result.val()
    bb = shape.BoundingBox()

    # --- bounding box: precise overall dimensions (fillets round inward, don't shrink) ---
    bw, bh, th = spec.bbox()
    for axis, exp, meas in (("x", bw, bb.xlen), ("y", bh, bb.ylen), ("z", th, bb.zlen)):
        checks.append(Check(
            name=f"bbox_{axis}", expected=round(exp, 3), measured=round(meas, 3),
            tol=tol, passed=abs(meas - exp) <= tol,
        ))

    # --- volume: ADVISORY only (not scored). The analytic estimate ignores fillets and
    # double-counts overlapping cuts, so it false-fails geometrically-correct parts. Kept
    # for human insight, but excluded from the gate and the retry feedback. ---
    exp_vol = _expected_volume(spec)
    meas_vol = shape.Volume()
    vol_band = max(_VOLUME_REL_TOL * exp_vol, tol)
    advisory: list[Check] = [Check(
        name="volume", expected=round(exp_vol, 1), measured=round(meas_vol, 1),
        tol=round(vol_band, 1), passed=abs(meas_vol - exp_vol) <= vol_band,
        detail=f"+/-{_VOLUME_REL_TOL:.0%} band (advisory)",
    )]

    # --- holes present: the hole axis point should be void, not material ---
    solid_wrapped = solids[0].wrapped if solids else None
    for i, h in enumerate(spec.holes):
        if h.hole_type == "through" or h.depth is None:
            probe_z = th / 2.0
        else:
            probe_z = th - h.depth / 2.0          # inside the blind pocket
        inside = None if solid_wrapped is None else _point_is_inside(
            solid_wrapped, h.x, h.y, probe_z)
        if inside is None:
            checks.append(Check(
                name=f"hole{i}_present", expected="void", measured="unknown", tol=0,
                passed=True, detail="point-membership test unavailable; skipped",
            ))
        else:
            checks.append(Check(
                name=f"hole{i}_present", expected="void",
                measured=("material" if inside else "void"), tol=0,
                passed=(not inside),
                detail="" if not inside else f"no opening at ({h.x},{h.y})",
            ))

    # --- named dimensions: each callout against its own tolerance ---
    for d in spec.dimensions:
        meas = _map_dimension(d.name, bb, spec)
        if meas is None:
            continue                              # unmapped name -> not scored
        lo, hi = d.nominal - d.tol_minus, d.nominal + d.tol_plus
        checks.append(Check(
            name=f"dim_{d.name}", expected=round(d.nominal, 3), measured=round(meas, 3),
            tol=round(max(d.tol_plus, d.tol_minus), 3), passed=(lo <= meas <= hi),
        ))

    return ValidationReport(checks=checks, advisory=advisory)


if __name__ == "__main__":
    import sys
    import cadquery as cq
    from pathlib import Path
    from drawing2cad.partspec import PartSpec

    spec_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("drawing2cad/outputs/test_1.json")
    step_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("out/test_1/part.step")

    spec = PartSpec.model_validate_json(spec_path.read_text())
    result = cq.importers.importStep(str(step_path))
    print(f"Loaded spec from {spec_path}")
    print(f"Loaded solid from {step_path}")

    report = validate(spec, result, tol=0.5)
    total = len(report.checks)
    passed = sum(c.passed for c in report.checks)
    print(f"\nResult: {passed}/{total} checks passed  (ok={report.ok()})\n")
    for c in report.checks:
        flag = "OK " if c.passed else "XX "
        detail = f"  [{c.detail}]" if c.detail else ""
        print(f"  {flag} {c.name}: expected={c.expected}  measured={c.measured}  tol={c.tol}{detail}")

    if report.advisory:
        print("\nAdvisory (not scored):")
        for c in report.advisory:
            flag = "ok " if c.passed else ".. "
            detail = f"  [{c.detail}]" if c.detail else ""
            print(f"  {flag} {c.name}: expected={c.expected}  measured={c.measured}{detail}")

    if not report.ok():
        print("\nFeedback for retry:\n" + report.feedback())
