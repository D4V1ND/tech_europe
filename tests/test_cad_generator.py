import pytest

from drawing2cad.cad_generator import spec_to_code
from drawing2cad.partspec import (
    ExtrudedGeometry,
    Hole,
    PartSpec,
    RevolvedGeometry,
    RevolvedSegment,
    UnsupportedGeometry,
)


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


def test_unsupported_geometry_is_not_generated():
    spec = PartSpec(geometry=UnsupportedGeometry(reason="bent sheet metal"))
    with pytest.raises(ValueError, match="unsupported geometry"):
        spec_to_code(spec)
