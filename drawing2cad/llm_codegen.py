"""LLM code-repair loop for the drawing → CAD pipeline.

Workflow:
  1. Extractor     → PartSpec  (what the part looks like)
  2. spec_to_code  → Python    (deterministic first attempt)
  3. run + validate → if it fails, the LLM receives (spec + broken code + error/validator
                       feedback) and returns a fixed script → repeat until validated or
                       max_iters is hit.

The LLM never starts from scratch — it always patches the previous code, keeping what
worked and fixing only what the feedback calls out.  The drawing image is fed only on the
first LLM call as a visual reference for ambiguous geometry; subsequent calls rely on the
spec + feedback alone so the context stays tight.

Feedback channels:
  - Python traceback    if the script crashed
  - validator failures  if it ran but didn't match the spec
  - (future) rendered views vs drawing  <-- hook below
"""
import traceback as _tb
from pathlib import Path

from langchain_core.messages import HumanMessage

from drawing2cad.cad_generator import run_code, _strip_fences, spec_to_code
from drawing2cad.drawing_loader import load_image_part
from drawing2cad.prompts import GEN_FROM_DRAWING_SYSTEM
from drawing2cad.validator import validate


def _score(report) -> float:
    if not report or not report.checks:
        return 0.0
    return sum(1 for c in report.checks if c.passed) / len(report.checks)


def _repair_code(*, model, spec, code, feedback, image_part=None) -> str:
    """Ask the LLM to fix `code` given `feedback`. Attaches the drawing image only when
    provided (first iteration — useful visual reference for ambiguous geometry)."""
    content = [{"type": "text", "text": GEN_FROM_DRAWING_SYSTEM}]
    content.append({"type": "text", "text":
        "PartSpec (ground truth — your output must match these dimensions):\n"
        + spec.model_dump_json(indent=2)})
    content.append({"type": "text", "text":
        "Current CadQuery code (fix it, keep what worked):\n" + code})
    content.append({"type": "text", "text":
        "Problems to fix:\n" + feedback})
    if image_part is not None:
        content.append(image_part)
    response = model.invoke([HumanMessage(content=content)])
    return _strip_fences(response.content)


def repair_loop(spec, out_dir, *, model=None, image_path=None,
                max_iters: int = 4, tol: float = 0.5,
                threshold: float = 0.9) -> dict:
    """Run the deterministic generator, then let the LLM repair failures.

    Flow per iteration:
      - attempt 1: run spec_to_code output directly (no LLM call)
      - attempt 2+: LLM patches the broken code using spec + feedback
                    (drawing image attached on attempt 2 only)
    Exits on a VALIDATED build or after max_iters.
    """
    if model is None:
        from drawing2cad.models import model_gemini
        model = model_gemini

    image_part = load_image_part(image_path) if image_path else None

    # Seed with deterministic output — LLM only fixes, never starts from scratch.
    code = spec_to_code(spec)
    feedback = None
    report = None
    stop_reason = "max_iters"

    for attempt in range(1, max_iters + 1):
        if attempt > 1:
            # LLM repair: attach image only on first repair call as a visual hint.
            img = image_part if attempt == 2 else None
            code = _repair_code(model=model, spec=spec, code=code,
                                 feedback=feedback, image_part=img)

        try:
            result = run_code(code, out_dir, spec=spec)
        except Exception:
            feedback = "The code raised an exception:\n" + _tb.format_exc(limit=6)
            stop_reason = "crash"
            continue

        report = validate(spec, result, tol=tol)
        score = _score(report)
        if score >= threshold:
            stop_reason = "validated"
            break

        feedback = ("The build ran but failed these validator checks — fix the geometry:\n"
                    + report.feedback())
        # --- visual feedback hook ---------------------------------------------------
        # Append rendered-view notes here when the renderer exists, e.g.:
        #   feedback += "\n\nVisual diff vs drawing:\n" + visual_review(result, image_path)
        # ----------------------------------------------------------------------------
        stop_reason = "below_threshold"

    out = Path(out_dir)
    return {
        "engine": "llm_repair",
        "code": code,
        "report": report,
        "score": _score(report),
        "attempts": attempt,
        "stop_reason": stop_reason,
        "files": {"py": str(out / "part.py"), "step": str(out / "part.step"),
                  "stl": str(out / "part.stl")},
    }


def reconstruct_best(image_path, out_dir="out/run", *, model=None,
                     threshold: float = 0.9, tol: float = 0.5, max_iters: int = 4) -> dict:
    """Full pipeline: extract → deterministic → repair loop if needed.

    Returns the result with the highest score (deterministic if it already passes,
    otherwise the best the repair loop achieves within max_iters)."""
    from drawing2cad.orchestrator import reconstruct

    # Step 1+2: extract spec, run deterministic generator, validate.
    det = reconstruct(image_path, out_dir=out_dir, model=model,
                      threshold=threshold, tol=tol, validate=True)
    det["engine"] = "deterministic"
    if det.get("passed"):
        return det

    spec = det.get("spec")
    if spec is None:
        return det  # extraction itself failed; nothing to repair

    # Step 3: LLM repair loop seeded with the deterministic code.
    rep = repair_loop(spec, out_dir=str(Path(out_dir) / "repair"),
                      model=model, image_path=image_path,
                      max_iters=max_iters, tol=tol, threshold=threshold)
    return rep if rep["score"] >= det.get("score", 0.0) else det


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/images/test_5.png"
    res = reconstruct_best(path, out_dir="out/" + Path(path).stem)
    print(f"engine={res['engine']}  score={res['score']:.0%}  "
          f"stop={res.get('stop_reason')}  attempts={res.get('attempts')}")
