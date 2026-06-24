import base64
from pathlib import Path

_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".png": "image/png", ".webp": "image/webp"}


def load_image_part(path: str) -> dict:
    """Load an image into a LangChain image content part."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    mime = _MIME.get(p.suffix.lower(), "image/png")
    data = base64.b64encode(p.read_bytes()).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}
