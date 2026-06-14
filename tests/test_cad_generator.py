from pathlib import Path

import pytest

from drawing2cad.cad_generator import run_code, spec_to_code
from drawing2cad.partspec import (
    Body,
    ExtrudedGeometry,
    Hole,
    MultiBodyGeometry,
    PartSpec,
    Point,
    ProfileSegment,
    RevolvedGeometry,
    RevolvedSegment,
    UnsupportedGeometry,
)
from drawing2cad.validator import validate


def _build(code: str):
    namespace = {}
    exec(code, namespace)
    return namespace["result"]


def test_generates_stepped_revolved_part_with_counterbore():
    spec = PartSpec(
        geometry=RevolvedGeometry(segments=[
            RevolvedSegment(z_start=0, z_end=8, outer_diameter=76, inner_diameter=28),
            RevolvedSegment(z_start=8, z_end=26, outer_diameter=48, inner_diameter=28),
        ]),
        holes=[Hole(
            x=38, y=66, diameter=5.3, hole_type="counterbore",
            counterbore_diameter=7.8, counterbore_depth=4,
        )],
    )
    result = _build(spec_to_code(spec))
    bbox = result.val().BoundingBox()
    assert bbox.xlen == pytest.approx(76)
    assert bbox.ylen == pytest.approx(76)
    assert bbox.zlen == pytest.approx(26)
    assert len(result.solids().vals()) == 1


def test_legacy_extruded_part_still_generates():
    spec = PartSpec(
        geometry=ExtrudedGeometry(
            profile_kind="rectangle", width=50, height=30, thickness=5
        ),
        holes=[Hole(x=25, y=15, diameter=10)],
    )
    bbox = _build(spec_to_code(spec)).val().BoundingBox()
    assert (bbox.xlen, bbox.ylen, bbox.zlen) == pytest.approx((50, 30, 5))


def test_rectangle_rounded_corners_keep_bbox_and_single_solid():
    spec = PartSpec(geometry=ExtrudedGeometry(
        profile_kind="rectangle", width=50, height=30, thickness=5,
        corner_radius=5, corner_style="round",
    ))
    result = _build(spec_to_code(spec))
    bbox = result.val().BoundingBox()
    assert (bbox.xlen, bbox.ylen, bbox.zlen) == pytest.approx((50, 30, 5))
    assert len(result.solids().vals()) == 1
    # rounding the corners removes material from the plain prism
    assert result.val().Volume() < 50 * 30 * 5


def test_rectangle_scalloped_corners_remove_corner_material():
    spec = PartSpec(geometry=ExtrudedGeometry(
        profile_kind="rectangle", width=50, height=30, thickness=5,
        corner_radius=5, corner_style="scallop",
    ))
    result = _build(spec_to_code(spec))
    bbox = result.val().BoundingBox()
    # a corner notch leaves the overall envelope intact (edges still span full size)
    assert (bbox.xlen, bbox.ylen, bbox.zlen) == pytest.approx((50, 30, 5))
    assert len(result.solids().vals()) == 1
    assert result.val().Volume() < 50 * 30 * 5


def test_corner_radius_too_large_fails_sanity():
    spec = PartSpec(geometry=ExtrudedGeometry(
        profile_kind="rectangle", width=50, height=30, thickness=5, corner_radius=20,
    ))
    assert any("corner_radius" in e for e in spec.sanity_check())


def test_multibody_prism_plate_builds_sloped_profile():
    # right-triangle side wall (in y,z), 8 mm thick along x at x=0
    wall = Body(
        shape="prism", operation="add", axis="x", x=0.0, length=8.0,
        profile_points=[Point(x=0, y=0), Point(x=0, y=100), Point(x=80, y=100)],
    )
    spec = PartSpec(geometry=MultiBodyGeometry(bodies=[wall]))
    result = _build(spec_to_code(spec))
    bb = result.val().BoundingBox()
    assert (bb.xlen, bb.ylen, bb.zlen) == pytest.approx((8, 80, 100))
    assert len(result.solids().vals()) == 1
    # triangular profile => half the volume of its bounding prism
    assert result.val().Volume() == pytest.approx(0.5 * 80 * 100 * 8, rel=1e-3)


def test_multibody_prism_supports_circular_profile_arcs():
    plate = Body(
        shape="prism", operation="add", axis="z", length=3,
        profile_start=Point(x=0, y=5),
        profile_segments=[
            ProfileSegment(kind="arc", mid=Point(x=1.465, y=1.465), end=Point(x=5, y=0)),
            ProfileSegment(end=Point(x=20, y=0)),
            ProfileSegment(end=Point(x=20, y=20)),
            ProfileSegment(end=Point(x=0, y=20)),
        ],
    )
    result = _build(spec_to_code(PartSpec(geometry=MultiBodyGeometry(bodies=[plate]))))
    bb = result.val().BoundingBox()
    assert (bb.xlen, bb.ylen, bb.zlen) == pytest.approx((20, 20, 3))
    assert result.val().Volume() < 20 * 20 * 3


def test_run_code_persists_the_exact_source_spec(tmp_path):
    spec = PartSpec(geometry=ExtrudedGeometry(
        profile_kind="rectangle", width=10, height=8, thickness=2
    ))
    run_code(spec_to_code(spec), tmp_path, spec=spec)
    persisted = PartSpec.model_validate_json((tmp_path / "partspec.json").read_text())
    assert persisted == spec


def test_multibody_box_with_diameter_is_coerced_to_cylinder():
    # LLM mislabels a round hole as a "box" but fills diameter/length
    spec = PartSpec(geometry=MultiBodyGeometry(bodies=[
        Body(shape="box", operation="add", dx=40, dy=40, dz=10),
        Body(shape="box", operation="cut", axis="z", x=20, y=20, z=-1,
             diameter=10, length=12),
    ]))
    assert spec.geometry.bodies[1].shape == "cylinder"
    assert spec.sanity_check() == []
    assert len(_build(spec_to_code(spec)).solids().vals()) == 1


def test_multibody_validator_checks_cut_cylinder_on_its_actual_axis():
    spec = PartSpec(geometry=MultiBodyGeometry(bodies=[
        Body(shape="box", operation="add", dx=20, dy=4, dz=20),
        Body(shape="cylinder", operation="cut", axis="y", x=10, y=-1, z=10,
             diameter=6, length=6),
    ]))
    report = validate(spec, _build(spec_to_code(spec)))
    cut_check = next(check for check in report.checks if check.name == "body1_cut_present")
    assert cut_check.passed


def test_reviewed_test_5_spec_builds_expected_bracket():
    spec_path = Path("drawing2cad/outputs/test_5_corrected.json")
    spec = PartSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
    assert spec.sanity_check() == []
    result = _build(spec_to_code(spec))
    bb = result.val().BoundingBox()
    assert (bb.xlen, bb.ylen, bb.zlen) == pytest.approx((116, 105, 100))
    report = validate(spec, result)
    assert report.ok()


def test_unsupported_geometry_is_not_generated():
    spec = PartSpec(geometry=UnsupportedGeometry(reason="bent sheet metal"))
    with pytest.raises(ValueError, match="unsupported geometry"):
        spec_to_code(spec)
