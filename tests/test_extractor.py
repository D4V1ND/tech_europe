import drawing2cad.extractor as extractor
from drawing2cad.partspec import PartSpec


class FakeStructuredModel:
    def __init__(self):
        self.schema = None
        self.kwargs = None

    def with_structured_output(self, schema, **kwargs):
        self.schema = schema
        self.kwargs = kwargs
        return self

    def invoke(self, _messages):
        return PartSpec.model_validate({
            "geometry": {
                "kind": "extruded",
                "profile_kind": "rectangle",
                "width": 10,
                "height": 5,
                "thickness": 2,
            }
        })


def test_non_openai_model_uses_default_structured_output_method():
    model = FakeStructuredModel()
    result = extractor.extract(
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,"}},
        model,
    )
    assert model.schema is PartSpec
    assert model.kwargs == {}
    assert result.geometry.kind == "extruded"


def test_openai_model_uses_function_calling(monkeypatch):
    model = FakeStructuredModel()
    monkeypatch.setattr(extractor, "ChatOpenAI", FakeStructuredModel)
    extractor.extract(
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,"}},
        model,
    )
    assert model.kwargs == {"method": "function_calling"}
