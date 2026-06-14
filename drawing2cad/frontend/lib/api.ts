export interface Check {
  name: string
  target: number | null
  actual: number | null
  tolerance: number
  passed: boolean
}

export interface ValidationReport {
  passed: boolean
  attempts: number
  checks: Check[]
}

export interface TavilyQuestion {
  field: string
  question: string
  tavily_suggestion: number
  source_url: string
}

// PartSpec types — mirror drawing2cad/partspec.py exactly
export interface Dimension {
  name: string
  nominal: number
  tol_plus: number
  tol_minus: number
}

export interface Hole {
  x: number
  y: number
  diameter: number
  through: boolean
  depth: number | null
}

export interface RectCut {
  x: number; y: number; z: number
  dx: number; dy: number; dz: number
}

export interface PartSpec {
  units: 'mm' | 'in'
  profile_kind: 'rectangle' | 'circle' | 'polygon'
  width: number | null
  height: number | null
  diameter: number | null
  profile_points: { x: number; y: number }[]
  thickness: number
  holes: Hole[]
  cuts: RectCut[]
  fillets: number[]
  chamfers: number[]
  dimensions: Dimension[]
  notes: string | null
}

export interface ReconstructResult {
  run_id: string
  passed: boolean
  attempts: number
  score?: number
  spec?: PartSpec
  report: ValidationReport | null
  code: string
  stl_url: string
  step_url: string
  drawing_url: string
  status: 'done' | 'needs_input'
  pending_questions?: TavilyQuestion[]
}

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

const FIXTURE_RESULT: ReconstructResult = {
  run_id: 'demo',
  passed: true,
  attempts: 1,
  score: 1.0,
  spec: {
    units: 'mm',
    profile_kind: 'rectangle',
    width: 50.0,
    height: 30.0,
    diameter: null,
    profile_points: [],
    thickness: 5.0,
    holes: [],
    cuts: [],
    fillets: [],
    chamfers: [],
    dimensions: [
      { name: 'overall_width',  nominal: 50.0, tol_plus: 0.5, tol_minus: 0.5 },
      { name: 'overall_height', nominal: 30.0, tol_plus: 0.5, tol_minus: 0.5 },
      { name: 'thickness',      nominal: 5.0,  tol_plus: 0.5, tol_minus: 0.5 },
    ],
    notes: 'Mounting bracket XY-300, AL-6061',
  },
  report: {
    passed: true,
    attempts: 1,
    checks: [
      { name: 'overall_width',  target: 50.0, actual: 50.0, tolerance: 0.5, passed: true },
      { name: 'overall_height', target: 30.0, actual: 30.0, tolerance: 0.5, passed: true },
      { name: 'thickness',      target: 5.0,  actual: 5.0,  tolerance: 0.5, passed: true },
    ],
  },
  code: `import cadquery as cq\n\n# --- parameters (editable) ---\nwidth      = 50.0   # mm\nheight     = 30.0   # mm\nthickness  =  5.0   # mm\nhole_dia   = 10.0   # mm\nhole_x     = 25.0   # mm  from bottom-left origin\nhole_y     = 15.0   # mm  from bottom-left origin\n\n# --- build ---\nresult = (\n    cq.Workplane("XY")\n    .box(width, height, thickness)\n    .faces(">Z").workplane()\n    .pushPoints([(hole_x - width / 2, hole_y - height / 2)])\n    .hole(hole_dia)\n)\n`,
  stl_url: '/fixtures/part.stl',
  step_url: '/fixtures/part.step',
  drawing_url: '/fixtures/drawing.png',
  status: 'done',
}

export async function getResult(runId: string): Promise<ReconstructResult> {
  if (runId === 'demo') return FIXTURE_RESULT
  const res = await fetch(`/runs/${runId}`)
  if (!res.ok) throw new Error(`Failed to load run ${runId}`)
  return res.json()
}

export async function reconstruct(
  file: File,
  onProgress: (step: number) => void,
): Promise<ReconstructResult> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch('/api/reconstruct', { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  const { run_id } = await res.json()

  while (true) {
    const poll = await fetch(`/runs/${run_id}`)
    if (!poll.ok) throw new Error(`Poll failed: ${poll.status}`)
    const data = await poll.json()
    if (data.status === 'running') {
      if (data.step !== undefined) onProgress(data.step)
      await sleep(500)
      continue
    }
    if (data.status === 'done' || data.status === 'needs_input') return data
    throw new Error(`Unexpected status: ${data.status}`)
  }
}

export async function rerun(runId: string, code: string): Promise<ReconstructResult> {
  const res = await fetch('/api/rerun', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, code }),
  })
  if (!res.ok) throw new Error(`Rerun failed: ${res.status}`)
  return res.json()
}

export interface VisualVerdict {
  matches: boolean
  confidence: number
  discrepancies: string[]
  assessment: string
  render_url: string
}

export async function visualValidate(runId: string): Promise<VisualVerdict> {
  const res = await fetch('/api/visual-validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId }),
  })
  if (!res.ok) throw new Error(`Visual validation failed: ${res.status}`)
  return res.json()
}

export async function continueWithAnswers(
  _runId: string,
  _answers: { field: string; value: number | null }[]
): Promise<ReconstructResult> {
  await sleep(2000)
  return FIXTURE_RESULT
}
