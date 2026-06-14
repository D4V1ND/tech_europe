import sys
import time
import uuid
import mimetypes
import threading
import traceback
from pathlib import Path

# Ensure the parent directory is on sys.path so `drawing2cad` is importable
# regardless of where the script is invoked from.
_here = Path(__file__).parent
sys.path.insert(0, str(_here.parent))

# Load .env from the drawing2cad directory before any model imports
from dotenv import load_dotenv
load_dotenv(_here / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS_DIR = Path(__file__).parent / "runs"

# In-memory job store: run_id → job dict
_jobs: dict[str, dict] = {}


class RerunBody(BaseModel):
    run_id: str
    code: str


class VisualValidateBody(BaseModel):
    run_id: str


class RefineBody(BaseModel):
    run_id: str
    discrepancies: list[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/api/reconstruct")
async def start_reconstruct(file: UploadFile = File(...)):
    run_id = str(uuid.uuid4())
    out_dir = RUNS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "drawing.png").suffix or ".png"
    drawing_path = out_dir / f"drawing{suffix}"
    drawing_path.write_bytes(await file.read())

    _jobs[run_id] = {
        "status": "running",
        "step": 0,
        "drawing_path": str(drawing_path),
        "out_dir": str(out_dir),
        "result": None,
        "error": None,
    }

    threading.Thread(
        target=_run_job,
        args=(run_id, drawing_path, out_dir),
        daemon=True,
    ).start()
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    job = _jobs.get(run_id)
    if not job:
        raise HTTPException(404, "Run not found")
    if job["status"] == "running":
        return {"run_id": run_id, "status": "running", "step": job["step"]}
    if job["status"] == "refining":
        return {"run_id": run_id, "status": "refining"}
    if job["status"] == "error":
        raise HTTPException(500, detail=job.get("error", "Reconstruction failed"))
    resp = _build_response(run_id, job)
    if job.get("refine_error"):
        resp["refine_error"] = job["refine_error"]
    return resp


@app.get("/runs/{run_id}/stl")
def get_stl(run_id: str):
    job = _require_done(run_id)
    path = Path(job["out_dir"]) / "part.stl"
    if not path.exists():
        raise HTTPException(404, "STL not generated")
    return FileResponse(path, media_type="model/stl", filename="part.stl")


@app.get("/runs/{run_id}/step")
def get_step_file(run_id: str):
    job = _require_done(run_id)
    path = Path(job["out_dir"]) / "part.step"
    if not path.exists():
        raise HTTPException(404, "STEP not generated")
    return FileResponse(path, media_type="application/octet-stream", filename="part.step")


@app.get("/runs/{run_id}/drawing")
def get_drawing(run_id: str):
    job = _jobs.get(run_id)
    if not job:
        raise HTTPException(404, "Run not found")
    path = Path(job["drawing_path"])
    if not path.exists():
        raise HTTPException(404, "Drawing not found")
    mime, _ = mimetypes.guess_type(str(path))
    return FileResponse(path, media_type=mime or "image/png")


@app.post("/api/visual-validate")
def visual_validate_run(body: VisualValidateBody):
    """Layer 2 check: render the built solid and ask the vision LLM to compare it to
    the original drawing. On-demand only (a vision call); advisory, never a gate."""
    job = _require_done(body.run_id)
    out_dir = Path(job["out_dir"])
    stl_path = out_dir / "part.stl"
    if not stl_path.exists():
        raise HTTPException(404, "STL not generated")
    try:
        from drawing2cad.visual_validator import visual_validate
        verdict, _ = visual_validate(
            job["drawing_path"], stl_path, render_path=out_dir / "render.png"
        )
    except Exception as e:
        raise HTTPException(500, detail=f"visual validation failed: {e}")
    return {
        "matches": verdict.matches,
        "confidence": verdict.confidence,
        "discrepancies": verdict.discrepancies,
        "assessment": verdict.assessment,
        "render_url": f"/runs/{body.run_id}/render?t={int(time.time())}",
    }


@app.post("/api/refine")
def refine_run(body: RefineBody):
    """Second pass: feed the visual review's discrepancies back to the extractor, then
    regenerate and re-validate. Runs ASYNC -- re-extraction can take minutes, which would
    blow past the dev proxy's request timeout if done synchronously. Returns immediately;
    the client polls GET /runs/{run_id} until status flips back to 'done'."""
    job = _require_done(body.run_id)
    if job["result"].get("spec") is None:
        raise HTTPException(400, "No previous spec to refine")
    job["status"] = "refining"
    job["refine_error"] = None
    threading.Thread(
        target=_run_refine_job,
        args=(body.run_id, body.discrepancies),
        daemon=True,
    ).start()
    return {"run_id": body.run_id, "status": "refining"}


def _run_refine_job(run_id: str, discrepancies: list[str]):
    job = _jobs[run_id]
    try:
        from drawing2cad.refiner import refine
        result = refine(
            job["drawing_path"], job["result"]["spec"], discrepancies, Path(job["out_dir"])
        )
        if result.get("spec") is None or result["stop_reason"].startswith("sanity_check_failed"):
            job["refine_error"] = f"refined extraction was invalid: {result['stop_reason']}"
        else:
            job["result"] = result
            job["stl_version"] = int(time.time())   # new geometry -> bust the viewer cache
            job["refine_error"] = None
    except Exception as e:
        traceback.print_exc()                 # full traceback to the server console
        job["refine_error"] = f"refine failed: {type(e).__name__}: {e}"
    finally:
        job["status"] = "done"


@app.get("/runs/{run_id}/render")
def get_render(run_id: str):
    job = _require_done(run_id)
    path = Path(job["out_dir"]) / "render.png"
    if not path.exists():
        raise HTTPException(404, "Render not generated")
    return FileResponse(path, media_type="image/png", filename="render.png")


@app.post("/api/rerun")
async def rerun(body: RerunBody):
    job = _require_done(body.run_id)
    out_dir = Path(job["out_dir"])
    try:
        from drawing2cad.cad_generator import run_code
        run_code(body.code, out_dir)
    except Exception as e:
        raise HTTPException(400, detail=str(e))

    job["result"]["code"] = body.code
    job["stl_version"] = int(time.time())
    # Bust the browser cache so the 3D viewer reloads the new STL
    return _build_response(body.run_id, job, cache_bust=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _run_job(run_id: str, drawing_path: Path, out_dir: Path):
    def on_step(step: int):
        _jobs[run_id]["step"] = step

    try:
        from drawing2cad.orchestrator import reconstruct
        result = reconstruct(drawing_path, out_dir=out_dir, on_step=on_step)
        _jobs[run_id]["result"] = result
        _jobs[run_id]["stl_version"] = int(time.time())
        _jobs[run_id]["status"] = "done"
    except Exception as e:
        _jobs[run_id]["status"] = "error"
        _jobs[run_id]["error"] = str(e)


def _require_done(run_id: str) -> dict:
    job = _jobs.get(run_id)
    if not job:
        raise HTTPException(404, "Run not found")
    if job["status"] != "done":
        raise HTTPException(409, "Run not complete")
    return job


def _flatten_spec(spec) -> dict | None:
    """Flatten the new discriminated-union PartSpec into the legacy flat shape the
    frontend PartSpecTab expects: profile_kind/width/height/thickness at the top level,
    holes with a boolean `through` field."""
    if spec is None:
        return None
    from drawing2cad.partspec import ExtrudedGeometry, RevolvedGeometry

    geo = spec.geometry
    if isinstance(geo, ExtrudedGeometry):
        flat = {
            "profile_kind": geo.profile_kind,
            "width": geo.width,
            "height": geo.height,
            "diameter": geo.diameter,
            "thickness": geo.thickness,
            "profile_points": [{"x": p.x, "y": p.y} for p in geo.profile_points],
        }
    elif isinstance(geo, RevolvedGeometry):
        bw, _, bt = geo.bbox()
        flat = {"profile_kind": "circle", "width": None, "height": None,
                "diameter": bw, "thickness": bt, "profile_points": []}
    else:
        bw, bh, bt = geo.bbox()
        flat = {"profile_kind": "rectangle", "width": bw, "height": bh,
                "diameter": None, "thickness": bt, "profile_points": []}

    return {
        "units": spec.units,
        **flat,
        "holes": [{"x": h.x, "y": h.y, "diameter": h.diameter,
                   "through": h.hole_type == "through", "depth": h.depth}
                  for h in spec.holes],
        "cuts": [{"x": c.x, "y": c.y, "z": c.z,
                  "dx": c.dx, "dy": c.dy, "dz": c.dz} for c in spec.cuts],
        "fillets": spec.fillets,
        "chamfers": spec.chamfers,
        "dimensions": [{"name": d.name, "nominal": d.nominal,
                        "tol_plus": d.tol_plus, "tol_minus": d.tol_minus}
                       for d in spec.dimensions],
        "notes": spec.notes,
    }


def _build_response(run_id: str, job: dict, cache_bust: bool = False) -> dict:
    result = job["result"]
    spec = result.get("spec")
    report = result.get("report")
    # Stamp the model URLs with a version that bumps whenever the geometry is rebuilt
    # (initial run, refine, rerun). This makes the URL change so the 3D viewer reloads
    # the NEW mesh instead of serving the cached old one -- regardless of which endpoint
    # delivers the response (direct return or the poll on GET /runs/{id}).
    version = job.get("stl_version")
    if cache_bust and not version:
        version = int(time.time())
    suffix = f"?t={version}" if version else ""
    return {
        "run_id": run_id,
        "status": "done",
        "passed": result["passed"],
        "attempts": result["attempts"],
        "score": result["score"],
        "spec": _flatten_spec(spec),
        "report": {
            "passed": report.ok(),
            "attempts": result["attempts"],
            "checks": [{"name": c.name, "target": c.expected, "actual": c.measured,
                        "tolerance": c.tol, "passed": c.passed}
                       for c in report.checks],
        } if report else None,
        "code": result.get("code") or "",
        "stl_url": f"/runs/{run_id}/stl{suffix}",
        "step_url": f"/runs/{run_id}/step{suffix}",
        "drawing_url": f"/runs/{run_id}/drawing",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
