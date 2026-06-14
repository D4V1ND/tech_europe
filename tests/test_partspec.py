from drawing2cad.partspec import (
    Body,
    Dimension,
    ExtrudedGeometry,
    Hole,
    MultiBodyGeometry,
    PartSpec,
    RevolvedGeometry,
    RevolvedSegment,
    UnsupportedGeometry,
)


def test_partspec_roundtrip():
    spec = PartSpec(
        geometry=ExtrudedGeometry(
            profile_kind="rectangle", width=50, height=30, thickness=5
        ),
        holes=[Hole(x=25, y=15, diameter=10)],
    )
    again = PartSpec.model_validate_json(spec.model_dump_json())
    assert again.geometry.width == 50
    assert again.holes[0].diameter == 10
    assert again.units == "mm"
    assert again.geometry.kind == "extruded"


def test_legacy_partspec_json_is_migrated():
    legacy = {
        "units": "mm",
        "profile_kind": "rectangle",
        "width": 50,
        "height": 30,
        "thickness": 5,
        "holes": [{"x": 25, "y": 15, "diameter": 10, "through": True}],
    }
    spec = PartSpec.model_validate(legacy)
    assert isinstance(spec.geometry, ExtrudedGeometry)
    assert spec.geometry.thickness == 5
    assert spec.holes[0].hole_type == "through"


def test_revolved_and_counterbore_are_valid():
    spec = PartSpec(
        geometry=RevolvedGeometry(segments=[
            RevolvedSegment(z_start=0, z_end=8, outer_diameter=76, inner_diameter=28),
            RevolvedSegment(z_start=8, z_end=26, outer_diameter=48, inner_diameter=28),
        ]),
        holes=[Hole(
            id="mounting_hole",
            x=38,
            y=66,
            diameter=5.3,
            hole_type="counterbore",
            counterbore_diameter=7.8,
            counterbore_depth=4,
        )],
    )
    assert spec.sanity_check() == []
    assert spec.bbox() == (76, 76, 26)


def test_unsupported_geometry_fails_sanity_check():
    spec = PartSpec(geometry=UnsupportedGeometry(
        reason="bent sheet metal is not supported",
        visible_features=["two bends"],
    ))
    assert spec.sanity_check() == [
        "unsupported geometry (no envelope): bent sheet metal is not supported"
    ]


def test_multibody_rejects_placeholder_cylinders_and_excessive_body_counts():
    bodies = [Body(shape="box", dx=10, dy=10, dz=2)]
    bodies.extend(Body(shape="cylinder", operation="cut") for _ in range(129))
    errors = PartSpec(geometry=MultiBodyGeometry(bodies=bodies)).sanity_check()
    assert any("more than 128 bodies" in error for error in errors)
    assert any("cylinder missing positive diameter/length" in error for error in errors)


def test_multibody_rejects_bbox_that_conflicts_with_overall_dimensions():
    spec = PartSpec(
        geometry=MultiBodyGeometry(bodies=[Body(shape="box", dx=116, dy=105, dz=105)]),
        dimensions=[Dimension(name="overall_depth", nominal=100, tol_plus=0.1, tol_minus=0.1)],
    )
    assert any("depth 105.0" in error for error in spec.sanity_check())
