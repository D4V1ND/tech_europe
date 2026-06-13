from drawing2cad.partspec import PartSpec, Hole


def test_partspec_roundtrip():
    spec = PartSpec(
        width=50, height=30, thickness=5,
        holes=[Hole(x=25, y=15, diameter=10)],
    )
    data = spec.model_dump_json()
    again = PartSpec.model_validate_json(data)
    assert again.width == 50
    assert again.holes[0].diameter == 10
    assert again.units == "mm"
    assert again.profile_kind == "rectangle"
