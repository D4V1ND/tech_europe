from pathlib import Path

from drawing2cad.cad_generator import generate_code, run_code
from drawing2cad.partspec import PartSpec

HARD_LIMIT = 10       # absolute max attempts regardless of progress
DEFAULT_THRESHOLD = 0.9   # 90% of checks must pass to call it done


def _score(report) -> float:
    """Fraction of checks that passed."""
    if not report or not report.checks:
        return 0.0
    return sum(1 for c in report.checks if c.passed) / len(report.checks)


def reconstruct(
    image_path: str | Path,
    out_dir: str | Path = "out/",
    *,
    model=None,
    use_llm: bool = False,
    threshold: float = DEFAULT_THRESHOLD,
    tol: float = 0.5,
    validate: bool = True,
) -> dict:
    """Full pipeline: drawing image → validated parametric CAD.

    Loop stops when:
      - score >= threshold (success)
      - score didn't improve vs last attempt (plateau — LLM is stuck)
      - attempts > HARD_LIMIT (safety net)

    Returns a result dict with keys:
        spec, code, passed, attempts, score, files, report, stop_reason
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Extract PartSpec from drawing ---
    from drawing2cad.extractor import extract_drawing_info   # lazy: needs API key at runtime
    if model is None:
        from drawing2cad.models import model_gemini
        model = model_gemini
    spec = extract_drawing_info(image_path, model=model,
                                output_path=out_dir / "partspec.json")

    # --- Step 2: Sanity check before building ---
    errors = spec.sanity_check()
    if errors:
        return {
            "spec": spec, "code": None, "passed": False,
            "attempts": 0, "score": 0.0, "files": {},
            "report": None, "stop_reason": f"sanity_check_failed: {errors}",
        }

    # --- Step 3: Generate → Run → Validate loop ---
    feedback = None
    last_code = ""
    last_score = -1.0
    report = None
    stop_reason = "hard_limit"

    for attempt in range(1, HARD_LIMIT + 1):
        # Generate CadQuery code (deterministic or LLM)
        code = generate_code(spec, feedback=feedback, model=model, use_llm=use_llm)
        last_code = code

        # Execute code → build solid + export files
        try:
            result = run_code(code, out_dir)
        except Exception as e:
            feedback = f"Generated code raised an error: {e}"
            continue

        # Skip validation if not requested or validator not yet available
        if not validate:
            stop_reason = "validation_skipped"
            break
        try:
            from drawing2cad.validator import validate as run_validate
        except ImportError:
            stop_reason = "validator_not_implemented"
            break

        report = run_validate(spec, result, tol=tol)
        score = _score(report)

        # Success: enough checks pass
        if score >= threshold:
            stop_reason = "threshold_reached"
            break

        # Plateau: no improvement since last attempt → LLM is stuck, give up
        if score <= last_score:
            stop_reason = f"plateau_at_score_{score:.0%}"
            break

        last_score = score
        feedback = (
            f"Score {score:.0%} (need {threshold:.0%}). Fix these:\n"
            + report.feedback()
        )

    files = {
        "py":   str(out_dir / "part.py"),
        "step": str(out_dir / "part.step"),
        "stl":  str(out_dir / "part.stl"),
        "spec": str(out_dir / "partspec.json"),
    }

    final_score = _score(report)
    passed = final_score >= threshold if report else True

    return {
        "spec": spec,
        "code": last_code,
        "passed": passed,
        "attempts": attempt,
        "score": final_score,
        "files": files,
        "report": report,
        "stop_reason": stop_reason,
    }
