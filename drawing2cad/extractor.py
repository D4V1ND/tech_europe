from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from drawing2cad.drawing_loader import load_image_part
from drawing2cad.models import model_gemini, model_openai
from drawing2cad.partspec import PartSpec
from drawing2cad.prompts import EXTRACTION_PROMPT

load_dotenv()

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def extract(image_part: dict, model=model_gemini) -> PartSpec:
    """Read a drawing image (LangChain image part) into a PartSpec via a vision LLM."""
    message = HumanMessage(content=[
        {"type": "text", "text": EXTRACTION_PROMPT},
        image_part,
    ])
    if isinstance(model, ChatOpenAI):
        # OpenAI strict JSON Schema rejects the geometry union's `oneOf`.
        structured = model.with_structured_output(
            PartSpec,
            method="function_calling",
        )
    else:
        structured = model.with_structured_output(PartSpec)
    return structured.invoke([message])


def save_part_spec(spec: PartSpec, output_path: str | Path) -> Path:
    """Save an extracted PartSpec as formatted JSON and return its path."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    return destination


def extract_drawing_info(
    path: str | Path,
    model=model_gemini,
    output_path: str | Path | None = None,
) -> PartSpec:
    """Load a drawing, extract its PartSpec, and optionally save it as JSON."""
    image_part = load_image_part(path)
    spec = extract(image_part, model=model)
    if output_path is not None:
        save_part_spec(spec, output_path)
    return spec


if __name__ == "__main__":
    drawing_path = Path("tests/images/test_5.png")
    json_path = DEFAULT_OUTPUT_DIR / f"{drawing_path.stem}.json"
    spec = extract_drawing_info(drawing_path, model=model_openai, output_path=json_path)
    print(spec.model_dump_json(indent=2))
    print(f"Saved extraction to {json_path}")   