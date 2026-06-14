"""Second-pass refinement: feed the visual validator's findings back to the extractor.

Where the orchestrator does a first-pass extract -> generate -> validate, this closes the
Layer-2 loop: it takes the discrepancies the AI visual review found (model vs drawing) and
RE-EXTRACTS the drawing with that feedback, producing a corrected, more detailed PartSpec,
then regenerates and re-validates.

Kept in its own file (not the orchestrator) and triggered on demand from the UI -- it costs
a fresh vision extraction call, so it runs only when the user clicks "Refine".

The `discrepancies` are plain strings; this module does not know an LLM produced them, so
nothing here is coupled to the judge.
"""
from pathlib import Path

from drawing2cad.cad_generator import generate_code, run_code
from drawing2cad.partspec import PartSpec
from drawing2cad.prompts import build_refinement_feedback

DEFAULT_THRESHOLD = 0.9


def _score(report) -> float:
    if not report or not report.checks:
        return 0.0
    return sum(1 for c in report.checks if c.passed) / len(report.checks)


def refine(
    image_path: str | Path,
    previous_spec: PartSpec,
    discrepancies: list[str],
    out_dir: str | Path,
    *,
    model=None,
    threshold: float = DEFAULT_THRESHOLD,
    tol: float = 0.5,
) -> dict:
    """Re-extract `image_path` using `discrepancies` as feedback, then regenerate and
    re-validate. Returns the same result dict shape as orchestrator.reconstruct().
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    from drawing2cad.extractor import extract_drawing_info
    if model is None:
        from drawing2cad.models import model_gemini
        model = model_gemini

    feedback = build_refinement_feedback(previous_spec, discrepancies)
    spec = extract_drawing_info(image_path, model=model, feedback=feedback,
                                output_path=out_dir / "partspec.json")

    errors = spec.sanity_check()
    if errors:
        return {
            "spec": spec, "code": None, "passed": False, "attempts": 0,
            "score": 0.0, "files": {}, "report": None,
            "stop_reason": f"sanity_check_failed: {errors}",
        }

    code = generate_code(spec)
    try:
        result = run_code(code, out_dir, spec=spec)
    except Exception as e:
        return {
            "spec": spec, "code": code, "passed": False, "attempts": 1,
            "score": 0.0, "files": {}, "report": None,
            "stop_reason": f"codegen_error: {e}",
        }

    from drawing2cad.validator import validate as run_validate
    report = run_validate(spec, result, tol=tol)
    score = _score(report)

    files = {
        "py":   str(out_dir / "part.py"),
        "step": str(out_dir / "part.step"),
        "stl":  str(out_dir / "part.stl"),
        "spec": str(out_dir / "partspec.json"),
    }
    return {
        "spec": spec, "code": code, "passed": score >= threshold,
        "attempts": 1, "score": score, "files": files, "report": report,
        "stop_reason": "refined",
    }
