# drawing2cad

Turn a technical drawing image into a validated, editable parametric CAD part.

**Pipeline:** Vision LLM reads the drawing → extracts geometry into a typed `PartSpec` → a second LLM writes a parametric CadQuery script → the script is executed to a B-rep solid → a validator measures the solid and checks dimensions against the spec → the orchestrator self-corrects and retries on mismatch.

**Output:** editable `part.py` (named parameters), `part.step` (opens in any CAD), `part.stl` (preview), and a pass/fail validation report.

## Use cases
- Turn legacy drawings into 3D models for replacement parts on old machines.
- Reverse-engineer parts where the only available information is technical drawings and product catalogs.

## Stack
Python 3.11+, CadQuery, Pydantic, LangChain + langchain-openai, Flask, pytest.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Run (CLI)

```bash
export OPENAI_API_KEY=sk-...
python -m drawing2cad path/to/drawing.png --out out/
```

## Run (web UI)

```bash
python app.py
# open http://localhost:5001
```

## Test

```bash
pytest -q
```

## Project layout

```
drawing2cad/      # Python package (extraction, CAD gen, validation, orchestrator)
web/              # Frontend (STL viewer, report table, script view)
app.py            # Flask entry point
fixtures/         # Sample artifacts for UI development
tests/            # pytest suite (LLM-free, uses fakes)
docs/
  specs/          # Design spec
  plans/          # Implementation plan
```
