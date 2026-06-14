# drawing2cad

Convert a technical drawing image into an editable CadQuery model, STEP file, STL file,
and validation report.

The system uses a vision LLM to extract a typed `PartSpec`, then generates CadQuery code
deterministically where possible. Generated geometry is measured against the extracted
spec, and an optional LLM repair loop can revise models that fail validation.

## Pipeline

```text
PNG/JPG drawing
  -> vision extraction
  -> Pydantic PartSpec
  -> sanity checks
  -> deterministic CadQuery generation
  -> STEP/STL export
  -> dimensional validation
  -> optional visual review and LLM refinement
```

Each completed run writes:

- `partspec.json` - the exact specification used for generation
- `part.py` - editable CadQuery source with named parameters
- `part.step` - B-rep CAD model
- `part.stl` - triangulated preview model

## Supported Geometry

`PartSpec` currently supports:

- Extruded rectangle, circle, and polygon profiles
- Stepped revolved parts with coaxial bores
- Multi-body unions and cuts
- Boxes and rounded boxes
- Cylinders on global or arbitrary 3D axes
- Solid and hollow spheres
- Polygon prisms with line and circular-arc outlines
- Rectangular and circular sweeps along 3D line/arc paths
- Capsule-shaped slots and drains
- Through, blind, threaded, counterbored, and countersunk holes
- Counterbores on the start, end, or both ends of an arbitrary-axis bore
- Rectangular pockets and notches
- Direction-specific body fillets
- Rounded and scalloped profile corners
- Inch-to-millimetre normalization

These primitives cover plates, brackets, trays, stepped shafts, bent constant-section
arms, forked mounts, sphere packings, and many machined parts. Freeform surfaces,
variable-section lofts, and exact sheet-metal development remain approximation cases.

## Stack

- Python 3.11+
- CadQuery
- Pydantic
- LangChain with Google Gemini and OpenAI adapters
- FastAPI and Uvicorn
- Next.js 16, React 19, Three.js
- pytest

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Git Bash, macOS, or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd drawing2cad/frontend
npm.cmd install
cd ../..
```

On shells where the normal npm shim works, use `npm install` instead.

## Environment

Create `drawing2cad/.env` or set variables in your shell:

```dotenv
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

The default extraction model is Gemini. `OPENAI_API_KEY` is needed when selecting the
OpenAI model or using an OpenAI-backed workflow. Tavily is optional and only powers the
research features.

## Run The Web App

Start the FastAPI backend from the repository root:

```powershell
python -m drawing2cad.server
```

The backend listens on `http://localhost:5001`.

In another terminal, start the frontend:

```powershell
cd drawing2cad/frontend
npm.cmd run dev
```

Open `http://localhost:3000`.

The result page includes the source drawing, interactive STL viewer, extracted
parameters, dimensional checks, visual review, research tools, and editable CadQuery
source.

## Run From Python

Run the normal extraction, deterministic generation, and validation pipeline:

```python
from drawing2cad.orchestrator import reconstruct

result = reconstruct(
    "tests/images/test_5.png",
    out_dir="out/test_5",
    validate=True,
)

print(result["score"], result["stop_reason"])
```

Run the deterministic model first and allow the LLM to repair it if needed:

```powershell
python -m drawing2cad.llm_codegen tests/images/test_5.png
```

Generate CAD directly from an existing `PartSpec` JSON file:

```powershell
python -m drawing2cad.cad_generator drawing2cad/outputs/test_5_corrected.json
```

The direct generator writes to `out/<json-file-stem>/`.

## Batch Evaluation

Run every PNG under `tests/images/`:

```powershell
python -m drawing2cad.batch_run
```

Or provide another image directory:

```powershell
python -m drawing2cad.batch_run path/to/drawings
```

The command prints geometry type, validation score, attempt count, and stop reason for
each drawing.

## Validation

Layer 1 validation compares the generated solid to `PartSpec`:

- Connected solid count
- Bounding-box dimensions
- Hole/cut presence
- Named overall dimensions and tolerances
- Advisory volume comparison

Validate an existing STEP file manually:

```powershell
python -m drawing2cad.validator out/test_5/partspec.json out/test_5/part.step
```

Layer 2 visual validation renders the STL and asks a vision model to compare it with the
original drawing. It is advisory because dimensional validation can only prove that CAD
matches the extracted spec, not that extraction interpreted the drawing correctly.

## Tests

```powershell
pytest -q
```

Frontend production build:

```powershell
cd drawing2cad/frontend
npm.cmd run build
```

## Project Layout

```text
drawing2cad/
  partspec.py          Typed intermediate geometry representation
  extractor.py         Vision LLM structured extraction
  prompts.py           Drawing interpretation and generation instructions
  cad_generator.py     Deterministic PartSpec-to-CadQuery compiler
  validator.py         Dimensional and feature validation
  visual_validator.py  Render-to-drawing visual comparison
  orchestrator.py      Extraction, generation, execution, validation loop
  llm_codegen.py       Deterministic seed plus LLM repair workflow
  server.py            FastAPI application
  batch_run.py         Batch evaluation command
  frontend/            Next.js UI
  outputs/             Saved or reviewed PartSpec fixtures
  runs/                Web application run artifacts
tests/
  images/              Technical drawing inputs
  test_*.py            LLM-free regression tests
out/                    Local generated CAD artifacts
docs/                   Design specifications and implementation plans
```

## Current Limitations

- Extraction quality still depends on drawing clarity and view interpretation.
- Selected-edge fillets are represented by axis groups, not arbitrary individual edge IDs.
- Exact sheet-metal bend allowance and developed-flat calculations are not implemented.
- Variable-section sweeps, lofted surfaces, and general freeform cast geometry are not
  deterministic PartSpec features.
- The geometric validator does not independently understand the source drawing; use the
  visual review for extraction errors.
- Generated Python is executed with `exec()`. Do not execute LLM-generated code from an
  untrusted source without sandboxing it.

## License

See [LICENSE](LICENSE).
