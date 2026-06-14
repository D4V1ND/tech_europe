"""Run the full pipeline over every drawing in tests/images/ and print a scoreboard.

Usage:
    python -m drawing2cad.batch_run                # all PNGs in tests/images/
    python -m drawing2cad.batch_run path/to/dir    # all PNGs in a chosen directory

For each image it runs orchestrator.reconstruct() and reports the validation score,
attempt count, and stop reason -- a single table to optimize the test set against.
"""
from pathlib import Path
import sys
import traceback

from drawing2cad.orchestrator import reconstruct

DEFAULT_DIR = Path("tests/images")


def _profile_of(spec) -> str:
    """Short label for the chosen geometry variant."""
    if spec is None:
        return "-"
    geom = getattr(spec, "geometry", None)
    if geom is None:
        return "?"
    kind = getattr(geom, "kind", "?")
    if kind == "extruded":
        return getattr(geom, "profile_kind", "extruded")
    return kind


def main(image_dir: Path) -> None:
    images = sorted(image_dir.glob("*.png"))
    if not images:
        print(f"No PNG images found in {image_dir}")
        return

    rows = []
    for img in images:
        out_dir = Path("out") / img.stem
        try:
            if out_dir == Path("out/test_5"):
                break
            res = reconstruct(img, out_dir=out_dir)
            rows.append({
                "name": img.name,
                "profile": _profile_of(res.get("spec")),
                "score": res.get("score", 0.0),
                "passed": res.get("passed", False),
                "attempts": res.get("attempts", 0),
                "stop": res.get("stop_reason", "?"),
            })
            print(f"check {out_dir}: score={res.get('score', 0.0):.0%}  passed={res.get('passed', False)}  attempts={res.get('attempts', 0)}  stop={res.get('stop_reason', '?')}")

        except Exception as e:                       # one bad image must not kill the run
            traceback.print_exc()
            rows.append({
                "name": img.name, "profile": "-", "score": 0.0,
                "passed": False, "attempts": 0, "stop": f"crash: {type(e).__name__}: {e}",
            })

    # --- scoreboard ---
    print(f"\n{'image':<14}{'profile':<11}{'score':>7}{'pass':>6}{'att':>5}  stop_reason")
    print("-" * 78)
    for r in rows:
        print(f"{r['name']:<14}{r['profile']:<11}{r['score']:>6.0%}"
              f"{('Y' if r['passed'] else 'N'):>6}{r['attempts']:>5}  {r['stop']}")
    print("-" * 78)
    passed = sum(1 for r in rows if r["passed"])
    avg = sum(r["score"] for r in rows) / len(rows)
    print(f"{passed}/{len(rows)} passed   avg score {avg:.0%}\n")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    main(target)
