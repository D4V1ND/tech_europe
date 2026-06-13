# Drawing → Validated Parametric CAD — Design Spec

**Date:** 2026-06-13
**Status:** Draft (awaiting review)
**Context:** 1-day hackathon project (Tech: Europe). Standalone, lives in `tech_europe/drawing2cad/`, separate from the `image2lego` repo.

## Goal

Take a **technical drawing** (raster image / scanned PDF) as input and run an **agentic pipeline** that reconstructs the part as a **parametric CAD model** (editable, not just a mesh). The result must be **validated**: the pipeline measures the generated solid and checks that its dimensions match the drawing, automatically correcting itself when they don't.

### Use cases
- Turn legacy drawings into 3D models for replacement parts on old machines.
- Reverse-engineer parts where the only information available is technical drawings and product catalogs.

## Settled decisions

| Decision | Choice | Reason |
|---|---|---|
| CAD engine | **CadQuery** (code-CAD) | Pure-Python `pip install`, fits LangChain stack, exposes a B-rep query API for validation, exports STEP (parametric) + STL. |
| Parametric deliverable | **Generated CadQuery `.py` script** with named parameters, plus exported **STEP** | The script *is* the editable parametric source; STEP is the interoperable editable form. |
| Input format | **Raster image / scanned PDF** read by a vision LLM | Matches the legacy-drawing use case; reuses existing vision-LLM plumbing. No DXF/vector path (YAGNI). |
| Part scope | **Prismatic**: profile extruded to a thickness + through/blind holes, corner fillets/chamfers | Cleanest CadQuery mapping and easiest to extract & validate in one day. |
| Validation | **Auto-measure + correction loop** (capped retries) | Satisfies "validated"; the self-correcting loop is the core agentic story. |
| Orchestration | **Approach A** — typed `PartSpec` intermediate between extraction and code generation | Gives validation real, independent targets; localizes failures; debuggable. |

## Architecture

Each module has one responsibility and a clear interface.

| Module | Responsibility | Depends on |
|---|---|---|
| `partspec.py` | Pydantic models — the typed contract between stages. **Pure data, no logic, no LLM.** | pydantic |
| `drawing_loader.py` | Load image / PDF page → normalized base64 image for the LLM | pillow, pdf2image |
| `extractor.py` | Vision LLM reads the drawing → emits a filled-in `PartSpec` (structured output) | langchain, partspec |
| `cad_generator.py` | `generate_code()`: `PartSpec` (+ correction feedback) → CadQuery script. `run_code()`: exec script → solid → export STEP + STL | langchain, cadquery, partspec |
| `validator.py` | Independently measure the solid, compare to `PartSpec` → pass/fail report | cadquery, partspec |
| `orchestrator.py` | The agent loop: extract → generate → run → validate → correct (max N retries) | all the above |
| `cli.py` | Entry point: `python -m drawing2cad drawing.png` | orchestrator |
| `app.py` *(stretch goal)* | Tiny Flask: upload image, show STL viewer + report table | orchestrator |

### Mental model: template vs instance
- `partspec.py` defines the **shape of the facts** (static, hand-written once). It is a passive data definition — no LLM, no geometry.
- `cad_generator.py` is an **action** that consumes those facts and produces geometry (uses the LLM, runs code, exports files).
- Per drawing, the pipeline produces a *filled-in* `PartSpec` (`partspec.json`) and a freshly generated `part.py`.

## The `PartSpec` contract

```python
from pydantic import BaseModel
from typing import Literal

class Hole(BaseModel):
    x: float                      # center X in mm, from profile origin (bottom-left)
    y: float                      # center Y in mm
    diameter: float
    through: bool = True
    depth: float | None = None    # for blind holes

class Dimension(BaseModel):
    name: str                     # "overall_width", "hole1_dia", ...
    nominal: float
    tol_plus: float = 0.5
    tol_minus: float = 0.5

class PartSpec(BaseModel):
    units: Literal["mm", "in"] = "mm"
    profile_kind: Literal["rectangle", "polygon"] = "rectangle"
    width: float | None = None                       # rectangle
    height: float | None = None                      # rectangle
    polygon: list[tuple[float, float]] | None = None # polygon outline
    thickness: float
    holes: list[Hole] = []
    fillets: list[float] = []     # corner radii
    chamfers: list[float] = []
    dimensions: list[Dimension] = []  # explicit callouts to validate against
    notes: str | None = None
```

## Data flow

```
drawing image ─▶ [vision LLM] ─▶ PartSpec ─▶ [CAD LLM] ─▶ CadQuery code ─▶ solid (STEP/STL)
                                    │                                         │
                                    └──────────── compared by validator ──────┘
```

1. `drawing_loader` → normalized image.
2. `extractor` → `model.with_structured_output(PartSpec)` → `PartSpec` (saved as `partspec.json`).
3. `cad_generator.generate_code(spec)` → CadQuery script with named params at top building a `result` workplane (saved as `part.py`).
4. `cad_generator.run_code(code)` → exec in restricted namespace → `cq.Workplane` → export `part.step` + `part.stl`.
5. `validator` → measure solid, compare to `PartSpec` → `report.json`.
6. `orchestrator` → on failure, feed diffs back to `generate_code(spec, feedback=...)` and retry (max 3).

### Generated `part.py` (example of runtime output)
```python
import cadquery as cq

# --- parameters (editable) ---
width = 50.0
height = 30.0
thickness = 5.0
hole_dia = 10.0
hole_x, hole_y = 25.0, 15.0

# --- build ---
result = (cq.Workplane("XY")
          .box(width, height, thickness)
          .faces(">Z").workplane()
          .pushPoints([(hole_x - width/2, hole_y - height/2)])
          .hole(hole_dia))
```

## Validation (the important nuance)

Because the code is generated *from* the `PartSpec`, dimensions could match "by construction." The validator earns its keep by **measuring the actual geometry independently** rather than reading parameter values back:

- **Overall W / H / thickness** ← `result.val().BoundingBox()`
- **Holes** ← iterate cylindrical faces → radius + center, match to expected holes
- Compare each `Dimension.nominal` to the measured value within `[−tol_minus, +tol_plus]` → **pass/fail table** (`name | target | actual | error | ✓/✗`).

This catches the real failure modes: wrong extrude axis, unit mix-ups, mis-placed holes, fillets consuming an edge, silent clamping. Default tolerance ±0.5 mm, configurable.

## Error handling & correction loop

- **Code exec error** (syntax / CadQuery exception) → captured traceback fed back to the generator as feedback; counts as a failed attempt.
- **Validation failures** → human-readable diff (`overall_width target 50.0, actual 48.2`) fed back to the generator.
- **Implausible spec** (e.g. hole ⌀ > part) → sanity check before generating; fed back to extractor/generator.
- **Structured-output parse failure** → retry extraction once.
- **Retry cap reached** → return best attempt with report marked `FAILED`. Never crash mid-demo — the report still renders.

## Artifacts produced per run

| File | What it is | Requirement it satisfies |
|---|---|---|
| `partspec.json` | extracted facts (filled-in `PartSpec`) | the validation yardstick |
| `part.py` | parametric CadQuery script (named params) | "parametric, editable" deliverable |
| `part.step` | B-rep solid, opens in any CAD | interoperable editable format |
| `part.stl` | mesh, for preview/render | quick visual check |
| `report.json` | pass/fail table (target vs actual vs error) | "validated" evidence |

## Testing

- **Deterministic golden test (no LLM):** known `PartSpec` → `generate`/measure → assert within tolerance. Tests generator + validator without LLM flakiness. *(Note: for fully deterministic runs, use a hand-written reference `part.py` rather than an LLM call.)*
- **Validator unit test:** hand-built solid (50×30×5 plate, ⌀10 hole at (25,15)) → assert measured values.
- **Smoke test:** 2–3 sample drawing images end-to-end (manual).
- LLM is **injectable/mockable** so the suite runs offline.

## Scope guardrails (YAGNI for 1 day)

- Units: mm + inch only.
- Profile: rectangle or simple polygon (no spline/arc profiles beyond corner fillets/chamfers).
- Holes: through + simple blind. No counterbores, countersinks, threads.
- Single part, single body. No assemblies.
- No GD&T interpretation — linear dimensions and hole dimensions only.
- **CLI is the shippable core; the Flask viewer is an explicit stretch goal** to be attempted only after the core pipeline works end-to-end.

## Dependencies

`cadquery`, `pydantic`, `langchain` + `langchain-openai` (reuse existing vision-LLM wiring), `pillow` / `pdf2image` (PDF→image, optional), `pytest`.

## Open questions / risks

- **Extraction accuracy** is the dominant risk: vision LLMs misread dimension callouts and confuse views. Mitigation: strict structured-output schema, a focused prompt, and the validation loop catching gross errors.
- **Hole face matching** in the validator needs care when multiple holes share a diameter (match by nearest expected position).
- Single-view vs multi-view drawings: assume the front view + thickness callout suffice for prismatic parts; multi-view fusion is out of scope.
