# Drawing → Validated Parametric CAD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn a technical drawing image into a validated, editable parametric CAD part (CadQuery script + STEP) via an agentic extract → generate → measure → self-correct loop.

**Architecture:** Vision LLM extracts a typed `PartSpec` from the drawing. A second LLM turns the `PartSpec` into a parametric CadQuery script, which is executed to a B-rep solid and exported to STEP/STL. A validator independently measures the solid and compares it to the `PartSpec`; on mismatch the orchestrator feeds diffs back to the generator and retries (capped). A Flask UI shows the STL, the editable script, and the validation report.

**Tech Stack:** Python 3.11+, CadQuery (OCP backend), Pydantic, LangChain + langchain-openai (vision), Pillow/pdf2image, Flask, pytest.

**Project root:** `tech_europe/drawing2cad/` (its own git repo, separate from image2lego). All paths below are relative to this root. Run all commands from this root. Package name: `drawing2cad`.

---

## Team & Parallelization

| Track | Owner | Modules | Starts after |
|---|---|---|---|
| **Phase 0 — Contracts & scaffold** | All three (pair ~30 min) | scaffold, `partspec.py`, `results.py`, fixtures | — |
| **Track V — Vision/Extraction** | **You** (vision LLM) | `drawing_loader.py`, `extractor.py` | Phase 0 |
| **Track G — CAD generation** | **Chia** (some LLM) | `cad_generator.py` | Phase 0 |
| **Track X — Validator (3D)** | **You** (3D) | `validator.py` | Phase 0 |
| **Track O — Orchestrator** | Chia + You (integration) | `orchestrator.py`, `cli.py`, `llm.py` | Tracks V, G, X |
| **Track U — UI/Demo** | **Demo person** | `app.py`, `web/index.html` | Phase 0 (uses fixtures, swaps to real orchestrator in Track O) |

**Why this works:** `PartSpec` + `results.py` are the only shared contracts. Once Phase 0 is committed, V/G/X/U proceed without touching each other's files. The demo person builds against committed fixture files (`fixtures/`) so they never wait for the pipeline.

**Planning refinements baked in (vs the spec):**
1. Validation compares the concrete `PartSpec` geometry fields (`width`, `height`, `thickness`, `holes[].diameter/x/y`) to the measured solid, using measured bounding-box edges as the coordinate origin — unambiguous and LLM-independent. The free-form `dimensions[]` list is retained for reporting/provenance only.
2. The orchestrator takes injected `extract_fn` / `generate_fn` callables so the full correction loop is testable offline with fakes (no API key in tests).

---

## File Structure

```
tech_europe/drawing2cad/
├── drawing2cad/
│   ├── __init__.py
│   ├── partspec.py          # Pydantic data models (PartSpec, Hole, Dimension)
│   ├── results.py           # Dataclasses: Check, ValidationReport, ReconstructResult
│   ├── drawing_loader.py    # image/PDF -> base64 LLM image part
│   ├── extractor.py         # vision LLM -> PartSpec
│   ├── cad_generator.py     # PartSpec -> CadQuery code (LLM) ; run code -> solid+exports
│   ├── validator.py         # measure solid, compare to PartSpec -> ValidationReport
│   ├── orchestrator.py      # extract->generate->run->validate->correct loop
│   ├── llm.py               # OpenAI vision model factory (lazy)
│   └── cli.py               # python -m drawing2cad <image>
├── web/
│   └── index.html           # STL viewer + report table + script view
├── app.py                   # Flask: upload -> run pipeline -> serve results
├── fixtures/                # sample artifacts for UI dev (committed in Phase 0)
│   ├── partspec.json
│   ├── part.py
│   ├── part.stl
│   └── report.json
├── tests/
│   ├── conftest.py
│   ├── test_partspec.py
│   ├── test_results.py
│   ├── test_drawing_loader.py
│   ├── test_extractor.py
│   ├── test_cad_generator.py
│   ├── test_validator.py
│   └── test_orchestrator.py
├── requirements.txt
└── README.md
```

---

# Phase 0 — Contracts & Scaffold (all three, together)

### Task 1: Project scaffold and dependencies

**Files:**
- Create: `requirements.txt`, `README.md`, `drawing2cad/__init__.py`, `tests/conftest.py`

- [ ] **Step 1: Create the directory layout and package marker**

```bash
cd tech_europe/drawing2cad
mkdir -p drawing2cad web fixtures tests
printf '' > drawing2cad/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
cadquery>=2.4
pydantic>=2.6
langchain>=0.2
langchain-openai>=0.1
pillow>=10.0
pdf2image>=1.17
flask>=3.0
pytest>=8.0
```

- [ ] **Step 3: Create and activate a virtualenv, install deps**

Run:
```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```
Expected: installs without error (CadQuery pulls in `cadquery-ocp`).

- [ ] **Step 4: Verify CadQuery imports and builds a solid**

Run:
```bash
python -c "import cadquery as cq; print(cq.Workplane('XY').box(1,1,1).val().BoundingBox().xlen)"
```
Expected: prints `1.0`.

- [ ] **Step 5: Minimal `README.md`**

```markdown
# drawing2cad
Technical drawing -> validated parametric CAD (CadQuery). Hackathon project.

## Run
    python -m drawing2cad path/to/drawing.png --out out/

## Test
    pytest -q
```

- [ ] **Step 6: Empty `tests/conftest.py`** (placeholder for shared fixtures)

```python
# shared pytest fixtures go here
```

- [ ] **Step 7: Commit**

```bash
git add tech_europe/drawing2cad
git commit -m "scaffold drawing2cad project"
```

---

### Task 2: `PartSpec` data models

**Files:**
- Create: `drawing2cad/partspec.py`
- Test: `tests/test_partspec.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_partspec.py
from drawing2cad.partspec import PartSpec, Hole

def test_partspec_roundtrip():
    spec = PartSpec(
        width=50, height=30, thickness=5,
        holes=[Hole(x=25, y=15, diameter=10)],
    )
    data = spec.model_dump_json()
    again = PartSpec.model_validate_json(data)
    assert again.width == 50
    assert again.holes[0].diameter == 10
    assert again.units == "mm"          # default
    assert again.profile_kind == "rectangle"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_partspec.py -v`
Expected: FAIL with `ModuleNotFoundError: drawing2cad.partspec`.

- [ ] **Step 3: Write `drawing2cad/partspec.py`**

```python
from pydantic import BaseModel
from typing import Literal


class Hole(BaseModel):
    x: float                      # center X, mm, from profile origin (bottom-left)
    y: float                      # center Y, mm
    diameter: float
    through: bool = True
    depth: float | None = None    # for blind holes


class Dimension(BaseModel):
    name: str
    nominal: float
    tol_plus: float = 0.5
    tol_minus: float = 0.5


class PartSpec(BaseModel):
    units: Literal["mm", "in"] = "mm"
    profile_kind: Literal["rectangle", "polygon"] = "rectangle"
    width: float | None = None
    height: float | None = None
    polygon: list[tuple[float, float]] | None = None
    thickness: float
    holes: list[Hole] = []
    fillets: list[float] = []
    chamfers: list[float] = []
    dimensions: list[Dimension] = []
    notes: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_partspec.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/partspec.py tests/test_partspec.py
git commit -m "add PartSpec data models"
```

---

### Task 3: `results.py` contracts + fixtures for the UI

**Files:**
- Create: `drawing2cad/results.py`
- Test: `tests/test_results.py`
- Create: `fixtures/partspec.json`, `fixtures/part.py`, `fixtures/part.stl`, `fixtures/report.json`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_results.py
from drawing2cad.results import Check, ValidationReport

def test_report_passed_and_feedback():
    ok = Check(name="overall_width", target=50.0, actual=50.2, tolerance=0.5, passed=True)
    bad = Check(name="thickness", target=5.0, actual=8.0, tolerance=0.5, passed=False)
    report = ValidationReport(checks=[ok, bad], passed=False)
    assert report.passed is False
    fb = report.feedback()
    assert "thickness" in fb and "8.0" in fb
    assert "overall_width" not in fb          # only failed checks in feedback
    d = report.to_dict()
    assert d["passed"] is False
    assert len(d["checks"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_results.py -v`
Expected: FAIL with `ModuleNotFoundError: drawing2cad.results`.

- [ ] **Step 3: Write `drawing2cad/results.py`**

```python
from dataclasses import dataclass, field, asdict


@dataclass
class Check:
    name: str
    target: float | None
    actual: float | None
    tolerance: float
    passed: bool


@dataclass
class ValidationReport:
    checks: list[Check]
    passed: bool

    def feedback(self) -> str:
        """Human-readable diffs for FAILED checks only (fed back to the generator)."""
        lines = []
        for c in self.checks:
            if not c.passed:
                actual = "missing" if c.actual is None else f"{c.actual:.3f}"
                lines.append(f"- {c.name}: target {c.target}, actual {actual} "
                             f"(tolerance +/-{c.tolerance})")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"passed": self.passed, "checks": [asdict(c) for c in self.checks]}


@dataclass
class ReconstructResult:
    spec: object              # PartSpec
    code: str                 # generated part.py source
    report: ValidationReport
    attempts: int
    passed: bool
    out_dir: str
    files: dict = field(default_factory=dict)   # {"step":..., "stl":..., "py":..., "spec":...}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_results.py -v`
Expected: PASS.

- [ ] **Step 5: Generate fixture artifacts for the UI track**

Run (writes a real STL + matching files so the demo person has live data):
```bash
python - <<'PY'
import json, cadquery as cq
from pathlib import Path
fx = Path("fixtures"); fx.mkdir(exist_ok=True)

code = '''import cadquery as cq

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
'''
(fx / "part.py").write_text(code)

ns = {}; exec(code, ns)
cq.exporters.export(ns["result"], str(fx / "part.stl"))

(fx / "partspec.json").write_text(json.dumps({
    "units": "mm", "profile_kind": "rectangle",
    "width": 50, "height": 30, "thickness": 5,
    "holes": [{"x": 25, "y": 15, "diameter": 10, "through": True}],
    "dimensions": [], "fillets": [], "chamfers": []
}, indent=2))

(fx / "report.json").write_text(json.dumps({
    "passed": True,
    "checks": [
        {"name": "overall_width", "target": 50, "actual": 50.0, "tolerance": 0.5, "passed": True},
        {"name": "overall_height", "target": 30, "actual": 30.0, "tolerance": 0.5, "passed": True},
        {"name": "thickness", "target": 5, "actual": 5.0, "tolerance": 0.5, "passed": True},
        {"name": "hole0_dia", "target": 10, "actual": 10.0, "tolerance": 0.5, "passed": True}
    ]
}, indent=2))
print("fixtures written")
PY
```
Expected: prints `fixtures written` and creates 4 files in `fixtures/`.

- [ ] **Step 6: Commit**

```bash
git add drawing2cad/results.py tests/test_results.py fixtures/
git commit -m "add result/report contracts and UI fixtures"
```

**>>> Phase 0 complete. Tracks V, G, X, and U can now run in parallel. <<<**

---

# Track V — Vision / Extraction (Owner: You)

### Task 4: `drawing_loader.py`

**Files:**
- Create: `drawing2cad/drawing_loader.py`
- Test: `tests/test_drawing_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_drawing_loader.py
from PIL import Image
from drawing2cad.drawing_loader import load_image_part

def test_load_png_as_data_url(tmp_path):
    p = tmp_path / "drawing.png"
    Image.new("RGB", (8, 8), "white").save(p)
    part = load_image_part(str(p))
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/png;base64,")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_drawing_loader.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `drawing2cad/drawing_loader.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_drawing_loader.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/drawing_loader.py tests/test_drawing_loader.py
git commit -m "add drawing_loader (image/pdf -> data url)"
```

---

### Task 5: `extractor.py` (vision LLM → PartSpec)

**Files:**
- Create: `drawing2cad/extractor.py`
- Test: `tests/test_extractor.py`

- [ ] **Step 1: Write the failing test (uses a fake structured-output model — no API key)**

```python
# tests/test_extractor.py
from drawing2cad.partspec import PartSpec, Hole
from drawing2cad.extractor import extract

class FakeStructuredModel:
    def __init__(self, spec): self._spec = spec
    def with_structured_output(self, schema): return self
    def invoke(self, messages): return self._spec

def test_extract_returns_partspec():
    expected = PartSpec(width=50, height=30, thickness=5,
                        holes=[Hole(x=25, y=15, diameter=10)])
    model = FakeStructuredModel(expected)
    spec = extract(image_part={"type": "image_url", "image_url": {"url": "data:..."}},
                   model=model)
    assert isinstance(spec, PartSpec)
    assert spec.width == 50
    assert spec.holes[0].diameter == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_extractor.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `drawing2cad/extractor.py`**

```python
from langchain_core.messages import HumanMessage
from .partspec import PartSpec

EXTRACTION_PROMPT = """You are a mechanical engineer reading a technical drawing of a
single PRISMATIC part (a flat profile extruded to a thickness, possibly with holes,
fillets, and chamfers).

Extract the geometry into the required structured schema:
- units: "mm" or "in" as shown on the drawing (default mm).
- profile_kind: "rectangle" if the outline is a rectangle, else "polygon".
- For a rectangle: width (X) and height (Y). For a polygon: the outline points in mm,
  counter-clockwise, starting at the bottom-left, origin at the bottom-left corner.
- thickness: the extrude depth (the dimension NOT visible in the main face view).
- holes: each hole center (x, y) in mm measured from the bottom-left origin, its
  diameter, and whether it is a through hole.
- fillets / chamfers: corner radii / chamfer sizes in mm if called out.
- dimensions: list every explicit linear/diameter callout as {name, nominal}.

Report numbers exactly as dimensioned. Do not invent dimensions that are not shown.
"""


def extract(image_part: dict, model) -> PartSpec:
    """Read a drawing image (LangChain image part) into a PartSpec via a vision LLM."""
    message = HumanMessage(content=[{"type": "text", "text": EXTRACTION_PROMPT}, image_part])
    structured = model.with_structured_output(PartSpec)
    return structured.invoke([message])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_extractor.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/extractor.py tests/test_extractor.py
git commit -m "add extractor (drawing -> PartSpec via vision LLM)"
```

---

# Track G — CAD Generation (Owner: Chia)

### Task 6: `cad_generator.run_code` (execute code → solid + exports)

**Files:**
- Create: `drawing2cad/cad_generator.py`
- Test: `tests/test_cad_generator.py`

- [ ] **Step 1: Write the failing test (hand-written code string — no LLM)**

```python
# tests/test_cad_generator.py
from drawing2cad.cad_generator import run_code

def test_run_code_builds_and_exports(tmp_path):
    code = (
        "import cadquery as cq\n"
        "result = cq.Workplane('XY').box(10, 20, 3)\n"
    )
    result = run_code(code, tmp_path)
    bb = result.val().BoundingBox()
    assert abs(bb.xlen - 10) < 1e-6
    assert (tmp_path / "part.step").exists()
    assert (tmp_path / "part.stl").exists()
    assert (tmp_path / "part.py").exists()

def test_run_code_missing_result_raises(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        run_code("import cadquery as cq\nx = 1\n", tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cad_generator.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `run_code` in `drawing2cad/cad_generator.py`**

```python
from pathlib import Path
import cadquery as cq


def run_code(code: str, out_dir) -> cq.Workplane:
    """Execute generated CadQuery code, returning the `result` Workplane and exporting
    part.py / part.step / part.stl into out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    namespace: dict = {}
    exec(code, namespace)                       # generated code, sandboxed namespace
    if "result" not in namespace:
        raise ValueError("Generated code did not define a `result` variable.")
    result = namespace["result"]

    (out_dir / "part.py").write_text(code)
    cq.exporters.export(result, str(out_dir / "part.step"))
    cq.exporters.export(result, str(out_dir / "part.stl"))
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cad_generator.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/cad_generator.py tests/test_cad_generator.py
git commit -m "add cad_generator.run_code"
```

---

### Task 7: `cad_generator.generate_code` (PartSpec → CadQuery via LLM)

**Files:**
- Modify: `drawing2cad/cad_generator.py`
- Modify: `tests/test_cad_generator.py`

- [ ] **Step 1: Add the failing test (fake LLM returning fenced code)**

```python
# append to tests/test_cad_generator.py
from types import SimpleNamespace
from drawing2cad.partspec import PartSpec
from drawing2cad.cad_generator import generate_code

class FakeLLM:
    def __init__(self, content): self._content = content
    def invoke(self, messages): return SimpleNamespace(content=self._content)

def test_generate_code_strips_fences_and_includes_feedback():
    spec = PartSpec(width=50, height=30, thickness=5)
    fenced = "```python\nimport cadquery as cq\nresult = cq.Workplane('XY').box(50,30,5)\n```"
    out = generate_code(spec, feedback="thickness wrong", model=FakeLLM(fenced))
    assert out.startswith("import cadquery")
    assert "```" not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cad_generator.py::test_generate_code_strips_fences_and_includes_feedback -v`
Expected: FAIL with `ImportError: cannot import name 'generate_code'`.

- [ ] **Step 3: Add `generate_code` (and `_strip_fences`) to `drawing2cad/cad_generator.py`**

```python
# add near the top of cad_generator.py
from .partspec import PartSpec

GEN_SYSTEM = """You are a CAD engineer. Given a PartSpec as JSON, write a CadQuery
(Python) script that reconstructs the part. Requirements:
- Put EVERY dimension as a named variable at the top of the script.
- Build the solid into a variable named exactly `result`.
- Origin convention: the PartSpec hole coordinates (x, y) are measured from the
  bottom-left of the profile. CadQuery's box is centered on the origin, so place a
  hole at (hole_x - width/2, hole_y - height/2) on the top face.
- Use through holes via .hole(d); for blind holes use .cboreHole/.hole with depth.
- Apply corner fillets/chamfers if present.
- Output ONLY Python code, no prose, no markdown fences.
"""


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t        # drop opening ```lang line
        if t.endswith("```"):
            t = t[: t.rfind("```")]
    return t.strip()


def generate_code(spec: PartSpec, feedback: str | None = None, *, model) -> str:
    """Turn a PartSpec into CadQuery source. `feedback` carries validation diffs on retry."""
    user = f"PartSpec JSON:\n{spec.model_dump_json(indent=2)}"
    if feedback:
        user += ("\n\nThe previous attempt FAILED these checks. Fix the code so the "
                 f"measured geometry matches:\n{feedback}")
    messages = [("system", GEN_SYSTEM), ("user", user)]
    resp = model.invoke(messages)
    return _strip_fences(resp.content)
```

- [ ] **Step 4: Run the full generator test file**

Run: `pytest tests/test_cad_generator.py -v`
Expected: PASS (all three tests).

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/cad_generator.py tests/test_cad_generator.py
git commit -m "add cad_generator.generate_code (PartSpec -> CadQuery via LLM)"
```

---

# Track X — Validator (Owner: You, 3D)

### Task 8: Bounding-box measurement + overall-dimension validation

**Files:**
- Create: `drawing2cad/validator.py`
- Test: `tests/test_validator.py`

- [ ] **Step 1: Write the failing test (deterministic, no LLM)**

```python
# tests/test_validator.py
import cadquery as cq
from drawing2cad.partspec import PartSpec
from drawing2cad.validator import validate

def test_overall_dims_pass():
    result = cq.Workplane("XY").box(50, 30, 5)
    spec = PartSpec(width=50, height=30, thickness=5)
    report = validate(spec, result)
    assert report.passed
    names = {c.name for c in report.checks}
    assert {"overall_width", "overall_height", "thickness"} <= names

def test_overall_dims_fail_when_thickness_off():
    result = cq.Workplane("XY").box(50, 30, 8)   # built thicker than spec
    spec = PartSpec(width=50, height=30, thickness=5)
    report = validate(spec, result)
    assert not report.passed
    bad = next(c for c in report.checks if c.name == "thickness")
    assert bad.passed is False
    assert abs(bad.actual - 8.0) < 1e-6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `drawing2cad/validator.py` (overall dims only for now)**

```python
import cadquery as cq
from .partspec import PartSpec
from .results import Check, ValidationReport


def _check(name: str, target, actual, tol: float) -> Check:
    if target is None or actual is None:
        return Check(name, target, actual, tol, passed=False)
    return Check(name, float(target), float(actual), tol, passed=abs(actual - target) <= tol)


def measure_bbox(result: cq.Workplane):
    return result.val().BoundingBox()


def validate(spec: PartSpec, result: cq.Workplane, tol: float = 0.5) -> ValidationReport:
    bb = measure_bbox(result)
    checks = [
        _check("overall_width", spec.width, bb.xlen, tol),
        _check("overall_height", spec.height, bb.ylen, tol),
        _check("thickness", spec.thickness, bb.zlen, tol),
    ]
    passed = all(c.passed for c in checks)
    return ValidationReport(checks=checks, passed=passed)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validator.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/validator.py tests/test_validator.py
git commit -m "add validator: bbox measurement + overall dims"
```

---

### Task 9: Cylinder measurement + hole validation

**Files:**
- Modify: `drawing2cad/validator.py`
- Modify: `tests/test_validator.py`

- [ ] **Step 1: Add the failing test (plate with a known hole)**

```python
# append to tests/test_validator.py
from drawing2cad.partspec import Hole

def _plate_with_hole():
    # 50x30x5 plate, 10mm-dia hole centered at profile (25,15) == model (0,0)
    return (cq.Workplane("XY").box(50, 30, 5)
            .faces(">Z").workplane()
            .pushPoints([(0, 0)]).hole(10))

def test_hole_validation_passes():
    result = _plate_with_hole()
    spec = PartSpec(width=50, height=30, thickness=5,
                    holes=[Hole(x=25, y=15, diameter=10)])
    report = validate(spec, result)
    assert report.passed, report.feedback()
    assert any(c.name == "hole0_dia" for c in report.checks)

def test_hole_validation_fails_on_wrong_diameter():
    result = _plate_with_hole()                     # actual 10mm
    spec = PartSpec(width=50, height=30, thickness=5,
                    holes=[Hole(x=25, y=15, diameter=6)])  # spec says 6mm
    report = validate(spec, result)
    assert not report.passed
    dia = next(c for c in report.checks if c.name == "hole0_dia")
    assert dia.passed is False
    assert abs(dia.actual - 10.0) < 0.1             # measured the real 10mm
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator.py -k hole -v`
Expected: FAIL (holes not yet measured; `hole0_dia` check missing).

- [ ] **Step 3: Add cylinder measurement + hole checks to `drawing2cad/validator.py`**

```python
# add these imports at the top of validator.py
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder


def measure_cylinders(result: cq.Workplane) -> list[dict]:
    """Return every cylindrical face as {radius, x, y, z} (axis location point)."""
    out = []
    for face in result.faces().vals():
        adaptor = BRepAdaptor_Surface(face.wrapped)
        if adaptor.GetType() == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            loc = cyl.Location()
            out.append({"radius": cyl.Radius(), "x": loc.X(), "y": loc.Y(), "z": loc.Z()})
    return out


def _nearest_cylinder(cyls, target_x, target_y, expected_r, tol):
    """Match the cylinder closest in (x,y) whose radius is within a generous band of the
    expected radius (filters out fillet faces that sit far from the hole center)."""
    best, best_d = None, None
    for c in cyls:
        if abs(c["radius"] - expected_r) > max(expected_r, tol * 4):
            continue
        d = ((c["x"] - target_x) ** 2 + (c["y"] - target_y) ** 2) ** 0.5
        if best_d is None or d < best_d:
            best, best_d = c, d
    return best
```

Then extend `validate` — replace its body with:

```python
def validate(spec: PartSpec, result: cq.Workplane, tol: float = 0.5) -> ValidationReport:
    bb = measure_bbox(result)
    checks = [
        _check("overall_width", spec.width, bb.xlen, tol),
        _check("overall_height", spec.height, bb.ylen, tol),
        _check("thickness", spec.thickness, bb.zlen, tol),
    ]

    cyls = measure_cylinders(result)
    for i, hole in enumerate(spec.holes):
        # spec coords are profile (origin bottom-left); convert to model coords via bbox min
        target_x = hole.x + bb.xmin
        target_y = hole.y + bb.ymin
        match = _nearest_cylinder(cyls, target_x, target_y, hole.diameter / 2, tol)
        if match is None:
            checks.append(Check(f"hole{i}_dia", hole.diameter, None, tol, False))
            continue
        checks.append(_check(f"hole{i}_dia", hole.diameter, match["radius"] * 2, tol))
        checks.append(_check(f"hole{i}_x", hole.x, match["x"] - bb.xmin, tol))
        checks.append(_check(f"hole{i}_y", hole.y, match["y"] - bb.ymin, tol))

    passed = all(c.passed for c in checks)
    return ValidationReport(checks=checks, passed=passed)
```

(Delete the old `validate` body so only this version remains.)

- [ ] **Step 4: Run the full validator test file**

Run: `pytest tests/test_validator.py -v`
Expected: PASS (all four tests).

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/validator.py tests/test_validator.py
git commit -m "add validator: cylinder measurement + hole checks"
```

---

# Track O — Orchestrator & CLI (Owner: Chia + You, after V/G/X)

### Task 10: `orchestrator.reconstruct` (the agentic correction loop)

**Files:**
- Create: `drawing2cad/orchestrator.py`
- Test: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing test (fakes: first attempt wrong, second correct)**

```python
# tests/test_orchestrator.py
from drawing2cad.partspec import PartSpec
from drawing2cad.orchestrator import reconstruct

def test_correction_loop_recovers(tmp_path):
    spec = PartSpec(width=50, height=30, thickness=5)
    calls = {"n": 0}

    def fake_extract(image_part):
        return spec

    def fake_generate(spec, feedback):
        calls["n"] += 1
        w = 40 if calls["n"] == 1 else 50          # first attempt is wrong width
        return f"import cadquery as cq\nresult = cq.Workplane('XY').box({w}, 30, 5)\n"

    res = reconstruct(image_part=None, out_dir=tmp_path,
                      extract_fn=fake_extract, generate_fn=fake_generate, max_retries=3)
    assert res.passed
    assert calls["n"] == 2                          # retried exactly once
    assert res.attempts == 2

def test_gives_up_after_max_retries(tmp_path):
    spec = PartSpec(width=50, height=30, thickness=5)

    def bad_generate(spec, feedback):
        return "import cadquery as cq\nresult = cq.Workplane('XY').box(99, 30, 5)\n"

    res = reconstruct(image_part=None, out_dir=tmp_path,
                      extract_fn=lambda i: spec, generate_fn=bad_generate, max_retries=2)
    assert not res.passed
    assert res.attempts == 3                         # initial + 2 retries
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `drawing2cad/orchestrator.py`**

```python
from pathlib import Path
from .cad_generator import run_code
from .validator import validate
from .results import ReconstructResult, ValidationReport, Check


def reconstruct(image_part, out_dir, *, extract_fn, generate_fn,
                run_fn=run_code, validate_fn=validate,
                max_retries: int = 3, tol: float = 0.5) -> ReconstructResult:
    """Agentic loop: extract -> generate -> run -> validate -> (correct & retry)."""
    out_dir = Path(out_dir)
    spec = extract_fn(image_part)
    (out_dir).mkdir(parents=True, exist_ok=True)
    (out_dir / "partspec.json").write_text(spec.model_dump_json(indent=2))

    feedback = None
    last_code, last_report = "", ValidationReport(checks=[], passed=False)
    attempts = 0

    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        code = generate_fn(spec, feedback)
        last_code = code
        try:
            result = run_fn(code, out_dir)
        except Exception as e:                       # code failed to execute -> feed back
            last_report = ValidationReport(
                checks=[Check("code_execution", None, None, tol, False)], passed=False)
            feedback = f"The generated code raised an error and must be fixed:\n{e}"
            continue

        report = validate_fn(spec, result, tol)
        last_report = report
        if report.passed:
            break
        feedback = report.feedback()

    files = {
        "py": str(out_dir / "part.py"),
        "step": str(out_dir / "part.step"),
        "stl": str(out_dir / "part.stl"),
        "spec": str(out_dir / "partspec.json"),
    }
    (out_dir / "report.json").write_text(_report_json(last_report))
    files["report"] = str(out_dir / "report.json")

    return ReconstructResult(spec=spec, code=last_code, report=last_report,
                             attempts=attempts, passed=last_report.passed,
                             out_dir=str(out_dir), files=files)


def _report_json(report: ValidationReport) -> str:
    import json
    return json.dumps(report.to_dict(), indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_orchestrator.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add drawing2cad/orchestrator.py tests/test_orchestrator.py
git commit -m "add orchestrator correction loop"
```

---

### Task 11: `llm.py` + `cli.py` (real wiring + entry point)

**Files:**
- Create: `drawing2cad/llm.py`, `drawing2cad/cli.py`, `drawing2cad/__main__.py`

- [ ] **Step 1: Write `drawing2cad/llm.py`**

```python
import os


def get_vision_model(temperature: float = 0.0):
    """OpenAI vision-capable chat model. Reads OPENAI_API_KEY from env.
    Override the model id with DRAWING2CAD_MODEL."""
    from langchain_openai import ChatOpenAI
    model = os.getenv("DRAWING2CAD_MODEL", "gpt-4o")
    return ChatOpenAI(model=model, temperature=temperature)
```

- [ ] **Step 2: Write `drawing2cad/cli.py`**

```python
import argparse
from pathlib import Path
from .drawing_loader import load_image_part
from .extractor import extract
from .cad_generator import generate_code
from .orchestrator import reconstruct
from .llm import get_vision_model


def main(argv=None):
    ap = argparse.ArgumentParser(prog="drawing2cad")
    ap.add_argument("image", help="path to the drawing image or PDF")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--tol", type=float, default=0.5, help="tolerance in mm")
    ap.add_argument("--max-retries", type=int, default=3)
    args = ap.parse_args(argv)

    model = get_vision_model()
    image_part = load_image_part(args.image)

    res = reconstruct(
        image_part=image_part,
        out_dir=Path(args.out),
        extract_fn=lambda part: extract(part, model=model),
        generate_fn=lambda spec, fb: generate_code(spec, fb, model=model),
        max_retries=args.max_retries,
        tol=args.tol,
    )

    print(f"\nAttempts: {res.attempts}   Passed: {res.passed}")
    print(f"{'CHECK':<16}{'TARGET':>10}{'ACTUAL':>10}  OK")
    for c in res.report.checks:
        actual = "missing" if c.actual is None else f"{c.actual:.3f}"
        print(f"{c.name:<16}{str(c.target):>10}{actual:>10}  {'Y' if c.passed else 'N'}")
    print(f"\nArtifacts in: {res.out_dir}")
    return 0 if res.passed else 1
```

- [ ] **Step 3: Write `drawing2cad/__main__.py`**

```python
import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Smoke test the CLI wiring without calling the API**

Run:
```bash
python -c "from drawing2cad.cli import main; print('cli import ok')"
```
Expected: prints `cli import ok` (no network/API key needed for import).

- [ ] **Step 5: (Manual, needs OPENAI_API_KEY) End-to-end on a sample drawing**

Run:
```bash
export OPENAI_API_KEY=sk-...
python -m drawing2cad path/to/sample_drawing.png --out out/
```
Expected: prints a check table and writes `out/part.py`, `out/part.step`, `out/part.stl`, `out/partspec.json`, `out/report.json`.

- [ ] **Step 6: Commit**

```bash
git add drawing2cad/llm.py drawing2cad/cli.py drawing2cad/__main__.py
git commit -m "add llm wiring and CLI entry point"
```

---

# Track U — UI / Demo (Owner: Demo person, starts after Phase 0)

The demo person builds against `fixtures/` immediately, then points the upload endpoint at the real `reconstruct` once Track O lands. No code dependency on V/G/X internals — only the file artifacts.

### Task 12: Flask app — upload, run, serve results

**Files:**
- Create: `app.py`

- [ ] **Step 1: Write `app.py`**

```python
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="web", static_url_path="")
OUT_ROOT = Path("runs")
OUT_ROOT.mkdir(exist_ok=True)


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/api/reconstruct", methods=["POST"])
def api_reconstruct():
    if "image" not in request.files:
        return jsonify({"error": "no image uploaded"}), 400
    run_id = uuid.uuid4().hex[:8]
    out_dir = OUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    img_path = out_dir / request.files["image"].filename
    request.files["image"].save(img_path)

    # Real pipeline (available once Track O lands):
    from drawing2cad.drawing_loader import load_image_part
    from drawing2cad.extractor import extract
    from drawing2cad.cad_generator import generate_code
    from drawing2cad.orchestrator import reconstruct
    from drawing2cad.llm import get_vision_model

    model = get_vision_model()
    res = reconstruct(
        image_part=load_image_part(str(img_path)),
        out_dir=out_dir,
        extract_fn=lambda part: extract(part, model=model),
        generate_fn=lambda spec, fb: generate_code(spec, fb, model=model),
    )
    return jsonify({
        "run_id": run_id,
        "passed": res.passed,
        "attempts": res.attempts,
        "report": res.report.to_dict(),
        "code": res.code,
        "stl_url": f"/runs/{run_id}/part.stl",
        "step_url": f"/runs/{run_id}/part.step",
    })


@app.route("/runs/<run_id>/<path:filename>")
def serve_run(run_id, filename):
    return send_from_directory(OUT_ROOT / run_id, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

- [ ] **Step 2: Smoke test the server boots**

Run:
```bash
python -c "import app; print('flask app import ok')"
```
Expected: prints `flask app import ok`.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "add Flask app: upload -> reconstruct -> serve results"
```

---

### Task 13: Frontend — STL viewer + report table + script view

**Files:**
- Create: `web/index.html`

- [ ] **Step 1: Write `web/index.html`**

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>drawing2cad</title>
  <script type="module"
    src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; }
    .row { display: flex; gap: 2rem; flex-wrap: wrap; }
    model-viewer { width: 420px; height: 360px; background: #f4f4f4; }
    table { border-collapse: collapse; } td, th { border: 1px solid #ccc; padding: 4px 10px; }
    .pass { color: green; } .fail { color: red; }
    pre { background: #1e1e1e; color: #eee; padding: 1rem; max-width: 520px; overflow:auto; }
  </style>
</head>
<body>
  <h1>Drawing → Parametric CAD</h1>
  <input type="file" id="file" accept="image/*,.pdf" />
  <button onclick="run()">Reconstruct</button>
  <p id="status"></p>

  <div class="row">
    <div>
      <h3>3D preview</h3>
      <!-- model-viewer wants glTF/GLB; for STL use a stl-loader build or convert.
           For the demo, model-viewer with .stl works via the community loader; if not,
           swap this element for a three.js STLLoader canvas. -->
      <model-viewer id="viewer" camera-controls auto-rotate></model-viewer>
    </div>
    <div>
      <h3>Validation report</h3>
      <p id="summary"></p>
      <table id="report"><thead>
        <tr><th>Check</th><th>Target</th><th>Actual</th><th>OK</th></tr>
      </thead><tbody></tbody></table>
    </div>
    <div>
      <h3>Parametric script (part.py)</h3>
      <pre id="code"></pre>
    </div>
  </div>

<script>
async function run() {
  const f = document.getElementById('file').files[0];
  if (!f) { alert('pick a drawing first'); return; }
  document.getElementById('status').textContent = 'Reconstructing… (extract → generate → validate)';
  const fd = new FormData(); fd.append('image', f);
  const r = await fetch('/api/reconstruct', { method: 'POST', body: fd });
  const data = await r.json();
  if (data.error) { document.getElementById('status').textContent = 'Error: ' + data.error; return; }

  document.getElementById('status').textContent = '';
  document.getElementById('summary').innerHTML =
    `Attempts: ${data.attempts} — <b class="${data.passed ? 'pass' : 'fail'}">`
    + `${data.passed ? 'PASSED' : 'FAILED'}</b>`;
  document.getElementById('viewer').src = data.stl_url;
  document.getElementById('code').textContent = data.code;

  const tb = document.querySelector('#report tbody'); tb.innerHTML = '';
  for (const c of data.report.checks) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${c.name}</td><td>${c.target ?? '—'}</td>`
      + `<td>${c.actual == null ? 'missing' : c.actual.toFixed(3)}</td>`
      + `<td class="${c.passed ? 'pass' : 'fail'}">${c.passed ? '✓' : '✗'}</td>`;
    tb.appendChild(tr);
  }
}
</script>
</body>
</html>
```

- [ ] **Step 2: Manual check against fixtures**

While Track O is unfinished, temporarily point `#viewer.src` and the table at `fixtures/part.stl` and `fixtures/report.json` to verify rendering. Run `python app.py`, open `http://localhost:5001`, confirm the page loads and the fixture STL renders.

> Note: `model-viewer` natively renders glTF/GLB. If STL doesn't display, either (a) add a three.js `STLLoader` `<canvas>` instead, or (b) have `run_code` also export `part.glb` (`cq.exporters.export(result, "part.glb")`) and point the viewer at that. Pick whichever renders first — decide during the demo build.

- [ ] **Step 3: Commit**

```bash
git add web/index.html
git commit -m "add frontend: STL viewer + report table + script view"
```

---

## Final integration check (all three)

- [ ] Run the full test suite from the project root:

Run: `pytest -q`
Expected: all tests pass.

- [ ] End-to-end demo dry run with `OPENAI_API_KEY` set: upload a sample drawing in the web UI, confirm the report table populates, the STL renders, and `part.py` shows named parameters. Edit a parameter in `part.py`, re-run it, and show the part changes — this is the "parametric, editable" proof.

---

## Notes & risks

- **Extraction accuracy is the dominant risk.** The validation loop catches gross errors but cannot fix a fundamentally misread drawing. Budget time to iterate on the `EXTRACTION_PROMPT` with your real sample drawings (You).
- **Cylinder/fillet ambiguity:** fillets also produce cylindrical faces; `_nearest_cylinder` filters by position + radius band. If a part has fillets with radii near a hole radius and close to a hole, revisit the matching heuristic.
- **STL in the browser:** see the note in Task 13 — exporting GLB is the safest fallback for `model-viewer`.
- **Tolerance** default is ±0.5 mm (`--tol`); tighten per drawing if needed.
