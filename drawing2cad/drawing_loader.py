import base64
from pathlib import Path

_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".png": "image/png", ".webp": "image/webp"}


def load_image_part(path: str) -> dict:
    """Load an image (or first page of a PDF) into a LangChain image content part."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    if p.suffix.lower() == ".pdf":
        path = _pdf_first_page_to_png(p)
        p = Path(path)

    mime = _MIME.get(p.suffix.lower(), "image/png")
    data = base64.b64encode(p.read_bytes()).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def _pdf_first_page_to_png(pdf_path: Path) -> str:
    """Best-effort PDF->PNG of the first page. Requires poppler + pdf2image."""
    from pdf2image import convert_from_path
    out = pdf_path.with_suffix(".page1.png")
    images = convert_from_path(str(pdf_path), first_page=1, last_page=1)
    images[0].save(out)
    return str(out)


if __name__ == "__main__":
    import sys
    print(load_image_part(sys.argv[1]))