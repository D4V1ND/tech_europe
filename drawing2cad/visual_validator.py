"""Layer 2 validator: an LLM-as-judge that compares the BUILT 3D model against the
ORIGINAL drawing. Where validator.py proves "the CAD matches the spec" (geometry vs
spec), this proves "the spec matches the drawing" -- it catches EXTRACTION errors a
purely geometric check is blind to (a missing hole, a wrong overall shape, an extra body).

It is intentionally NOT wired into the orchestrator loop: it costs a vision call and is
itself an LLM (so it can be confidently wrong). Run it on demand -- e.g. a UI button after
the model is generated -- and treat the verdict as ADVISORY, not a hard gate.

Pipeline:
    render the solid -> a multi-view PNG  (trimesh + matplotlib, headless)
    show Gemini both the drawing and the render
    return a structured VisualVerdict
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                       # headless: no display needed
import matplotlib.pyplot as plt             # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
import trimesh                              # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from pydantic import BaseModel, Field       # noqa: E402

from drawing2cad.drawing_loader import load_image_part  # noqa: E402
from drawing2cad.models import model_gemini  # noqa: E402


# --------------------------------------------------------------------------- schema

class VisualVerdict(BaseModel):
    """The judge's structured assessment of model-vs-drawing fidelity."""

    matches: bool = Field(description="True if the 3D model faithfully represents the drawing")
    confidence: float = Field(description="0.0-1.0 confidence in this verdict")
    discrepancies: list[str] = Field(
        default_factory=list,
        description="Specific features in the drawing that are missing/wrong in the model, "
        "e.g. 'top-left mounting hole missing', 'part is much taller than the drawing shows'",
    )
    assessment: str = Field(description="One-paragraph overall summary")


# --------------------------------------------------------------------------- rendering

_VIEWS = [
    ("isometric", 25, -60),
    ("front", 0, -90),
    ("top", 90, -90),
    ("side", 0, 0),
]


def render_solid(model_path: str | Path, out_path: str | Path) -> Path:
    """Render an STL/STEP solid to a 2x2 multi-view PNG and return its path."""
    out_path = Path(out_path)
    mesh = trimesh.load(str(model_path), force="mesh")
    verts = mesh.vertices
    tris = verts[mesh.faces]
    extents = [float(verts[:, i].max() - verts[:, i].min()) or 1.0 for i in range(3)]

    fig = plt.figure(figsize=(9, 8), facecolor="#0a0a18")
    for i, (name, elev, azim) in enumerate(_VIEWS, 1):
        ax = fig.add_subplot(2, 2, i, projection="3d")
        ax.add_collection3d(Poly3DCollection(
            tris, facecolor="#9db8e8", edgecolor="#33446a", linewidth=0.15, alpha=1.0,
        ))
        for axis, col in zip("xyz", range(3)):
            getattr(ax, f"set_{axis}lim")(verts[:, col].min(), verts[:, col].max())
        ax.set_box_aspect(extents)
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(name, color="white", fontsize=11)
        ax.set_axis_off()
        ax.set_facecolor("#0a0a18")
    fig.tight_layout()
    fig.savefig(out_path, dpi=90, facecolor="#0a0a18", bbox_inches="tight")
    plt.close(fig)
    return out_path


# --------------------------------------------------------------------------- judge

JUDGE_PROMPT = """You are a meticulous mechanical QA inspector. You are given TWO images:

  IMAGE 1 -- the ORIGINAL 2D technical drawing of a part.
  IMAGE 2 -- rendered views (isometric, front, top, side) of a 3D model that was
             automatically reconstructed from that drawing.

Your job: decide whether the 3D model faithfully represents the part in the drawing.

Compare them on FEATURE PRESENCE, COUNT, SHAPE, and PROPORTION:
  - Are all holes present, with the right count and roughly the right positions?
  - Are slots, notches, cutouts, pockets, and steps present?
  - Is the overall silhouette / outline the same (L-shape, bracket, plate, sloped wall)?
  - Are the proportions consistent (not twice as tall, not missing a leg/flange)?
  - Is the number of distinct bodies/plates consistent?

Do NOT nitpick exact millimetre dimensions -- you CANNOT measure those from a render, so
ignore small size differences. Focus on what is structurally present or missing/wrong.
If the render looks like a plain block but the drawing is clearly a detailed part, that is
a major discrepancy. List each problem specifically and concisely.

Set matches=true only if the model captures all the major features of the drawing."""


def visual_validate(
    drawing_path: str | Path,
    model_path: str | Path,
    render_path: str | Path | None = None,
    model=model_gemini,
) -> tuple[VisualVerdict, Path]:
    """Render the solid, then ask the vision LLM to compare it to the drawing.

    Returns (verdict, render_path). The render is kept so the UI can show what the
    judge actually saw.
    """
    if render_path is None:
        render_path = Path(model_path).with_name("render.png")
    render_path = render_solid(model_path, render_path)

    drawing_part = load_image_part(str(drawing_path))
    render_part = load_image_part(str(render_path))
    message = HumanMessage(content=[
        {"type": "text", "text": JUDGE_PROMPT},
        {"type": "text", "text": "IMAGE 1 -- original technical drawing:"},
        drawing_part,
        {"type": "text", "text": "IMAGE 2 -- rendered views of the reconstructed 3D model:"},
        render_part,
    ])
    verdict = model.with_structured_output(VisualVerdict).invoke([message])
    return verdict, render_path


if __name__ == "__main__":
    import sys

    drawing = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tests/images/test_5.png")
    solid = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("out/test_5/part.stl")

    verdict, render = visual_validate(drawing, solid)
    print(f"Rendered model to {render}\n")
    print(f"matches={verdict.matches}  confidence={verdict.confidence:.0%}")
    print(f"\nassessment: {verdict.assessment}")
    if verdict.discrepancies:
        print("\ndiscrepancies:")
        for d in verdict.discrepancies:
            print(f"  - {d}")
