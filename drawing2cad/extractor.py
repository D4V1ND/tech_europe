from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from drawing2cad.drawing_loader import load_image_part
from drawing2cad.models import model_gemini
from drawing2cad.partspec import PartSpec
from drawing2cad.prompts import EXTRACTION_PROMPT

load_dotenv()


def extract(image_part: dict, model=model_gemini) -> PartSpec:
    """Read a drawing image (LangChain image part) into a PartSpec via a vision LLM."""
    message = HumanMessage(content=[
        {"type": "text", "text": EXTRACTION_PROMPT},
        image_part,
    ])
    structured = model.with_structured_output(PartSpec)
    return structured.invoke([message])


def extract_drawing_info(path: str, model=model_gemini) -> PartSpec:
    """Convenience wrapper: load a drawing file from disk, then extract a PartSpec."""
    image_part = load_image_part(path)
    return extract(image_part, model=model)


if __name__ == "__main__":
    spec = extract_drawing_info("tests/images/test_1.png")
    print(spec.model_dump_json(indent=2))
