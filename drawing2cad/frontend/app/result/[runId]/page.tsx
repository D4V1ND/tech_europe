'use client'
import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import { ValidationPanel } from '@/components/ValidationPanel'
import { ScriptEditor } from '@/components/ScriptEditor'
import { DrawingPanel } from '@/components/DrawingPanel'
import { VisualReviewPanel } from '@/components/VisualReviewPanel'
import { TavilyResearchPanel } from '@/components/TavilyResearchPanel'
import { TavilySuggestionCard } from '@/components/TavilySuggestionCard'
import { getResult, rerun, tavilySuggest, applySuggestion, ReconstructResult, TavilyQuestion, PartSpec } from '@/lib/api'
import type { ViewPreset } from '@/components/ModelViewer3D'

const ModelViewer3D = dynamic(
  () => import('@/components/ModelViewer3D').then(m => m.ModelViewer3D),
  { ssr: false, loading: () => <div className="flex-1 rounded-xl" style={{ background: '#0a0a18', minHeight: 300 }} /> }
)

const MOCK_TAVILY_QUESTION: TavilyQuestion = {
  field: 'thickness',
  question: 'Wall thickness could not be read clearly. Tavily found: XY-300 series typically uses 5.0mm wall thickness.',
  tavily_suggestion: 5.0,
  source_url: 'https://manufacturer-specs.example.com/xy-300',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const th = (label: string) => (
  <th style={{
    textAlign: 'left', padding: '9px 16px',
    fontSize: 11, fontWeight: 600, textTransform: 'uppercase' as const,
    letterSpacing: '0.08em', color: 'rgba(255,255,255,0.35)',
    borderBottom: '1px solid rgba(255,255,255,0.07)',
  }}>{label}</th>
)

const mono = (v: string | number, color?: string) => (
  <td style={{ padding: '10px 16px', fontSize: 13, fontFamily: 'monospace', color: color ?? 'rgba(255,255,255,0.75)' }}>
    {v}
  </td>
)

function SectionHeader({ label }: { label: string }) {
  return (
    <div style={{
      padding: '8px 16px 4px',
      fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '0.12em', color: 'rgba(255,255,255,0.3)',
    }}>{label}</div>
  )
}

// ── PartSpecTab ───────────────────────────────────────────────────────────────

function PartSpecTab({ spec }: { spec: PartSpec }) {
  const profileColor = spec.profile_kind === 'circle' ? '#a78bfa' : spec.profile_kind === 'polygon' ? '#34d399' : '#4d9aff'

  return (
    <div style={{ padding: '12px 0 4px' }}>

      {/* Profile badge + key dims */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0 16px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{
          fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 100,
          background: `${profileColor}18`, color: profileColor, border: `1px solid ${profileColor}40`,
          letterSpacing: '0.06em', textTransform: 'uppercase',
        }}>{spec.profile_kind}</span>
        <span style={{ fontSize: 13, fontFamily: 'monospace', color: 'rgba(255,255,255,0.6)' }}>
          {spec.profile_kind === 'circle'
            ? `Ø${spec.diameter} × ${spec.thickness} ${spec.units}`
            : `${spec.width} × ${spec.height} × ${spec.thickness} ${spec.units}`}
        </span>
        {spec.notes && (
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginLeft: 'auto', fontStyle: 'italic' }}>
            {spec.notes}
          </span>
        )}
      </div>

      {/* Named dimensions */}
      {spec.dimensions.length > 0 && (
        <>
          <SectionHeader label="Dimensions" />
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{th('Name')}{th('Nominal')}{th('+Tol')}{th('−Tol')}</tr></thead>
            <tbody>
              {spec.dimensions.map((d, i) => (
                <tr key={d.name} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' }}>
                  <td style={{ padding: '9px 16px', fontSize: 13, color: 'white', fontFamily: 'monospace' }}>{d.name}</td>
                  {mono(`${d.nominal} ${spec.units}`, '#4d9aff')}
                  {mono(`+${d.tol_plus}`)}
                  {mono(`−${d.tol_minus}`)}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* Holes */}
      {spec.holes.length > 0 && (
        <>
          <SectionHeader label={`Holes (${spec.holes.length})`} />
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{th('#')}{th('Ø')}{th('Center X')}{th('Center Y')}{th('Type')}{th('Depth')}</tr></thead>
            <tbody>
              {spec.holes.map((h, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' }}>
                  {mono(i + 1, 'rgba(255,255,255,0.4)')}
                  {mono(`${h.diameter} ${spec.units}`, '#a78bfa')}
                  {mono(`${h.x} ${spec.units}`)}
                  {mono(`${h.y} ${spec.units}`)}
                  <td style={{ padding: '9px 16px' }}>
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 100,
                      background: h.through ? 'rgba(52,211,153,0.1)' : 'rgba(251,191,36,0.1)',
                      color: h.through ? '#34d399' : '#fbbf24',
                    }}>
                      {h.through ? 'through' : 'blind'}
                    </span>
                  </td>
                  {mono(h.depth != null ? `${h.depth} ${spec.units}` : '—', 'rgba(255,255,255,0.4)')}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* Cuts */}
      {spec.cuts.length > 0 && (
        <>
          <SectionHeader label={`Rect Cuts (${spec.cuts.length})`} />
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr>{th('#')}{th('Origin (x,y,z)')}{th('Size (dx,dy,dz)')}</tr></thead>
            <tbody>
              {spec.cuts.map((c, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' }}>
                  {mono(i + 1, 'rgba(255,255,255,0.4)')}
                  {mono(`${c.x}, ${c.y}, ${c.z}`)}
                  {mono(`${c.dx} × ${c.dy} × ${c.dz}`)}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* Fillets / Chamfers */}
      {(spec.fillets.length > 0 || spec.chamfers.length > 0) && (
        <div style={{ display: 'flex', gap: 24, padding: '10px 16px 6px' }}>
          {spec.fillets.length > 0 && (
            <div>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Fillets </span>
              <span style={{ fontSize: 13, fontFamily: 'monospace', color: 'rgba(255,255,255,0.7)' }}>
                {spec.fillets.map(r => `r${r}`).join(', ')} {spec.units}
              </span>
            </div>
          )}
          {spec.chamfers.length > 0 && (
            <div>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Chamfers </span>
              <span style={{ fontSize: 13, fontFamily: 'monospace', color: 'rgba(255,255,255,0.7)' }}>
                {spec.chamfers.map(c => `${c}`).join(', ')} {spec.units}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

type BottomTab = 'parameters' | 'validation' | 'review' | 'research' | 'script'

const BOTTOM_TABS: { id: BottomTab; label: string }[] = [
  { id: 'parameters', label: 'Parameters' },
  { id: 'validation', label: 'Validation' },
  { id: 'review',     label: 'AI Review' },
  { id: 'research',   label: 'Research' },
  { id: 'script',     label: 'Parametric Script' },
]

export default function ResultPage() {
  const params = useParams()
  const runId = typeof params.runId === 'string' ? params.runId : 'demo'

  const [result, setResult] = useState<ReconstructResult | null>(null)
  const [view, setView] = useState<ViewPreset>('iso')
  const [rerunLoading, setRerunLoading] = useState(false)
  const [showTavily, setShowTavily] = useState(true)
  const [tavilyQ, setTavilyQ] = useState<TavilyQuestion | null>(null)
  const [bottomTab, setBottomTab] = useState<BottomTab>('parameters')

  useEffect(() => {
    getResult(runId).then(setResult).catch(console.error)
  }, [runId])

  // Real Tavily lookup for the floating card: fetch a standard wall-thickness suggestion
  // once the run is loaded (the demo fixture keeps its canned card instead).
  useEffect(() => {
    if (runId === 'demo' || !result || result.status !== 'done') return
    let cancelled = false
    tavilySuggest(runId, 'thickness')
      .then(q => { if (!cancelled && q.tavily_suggestion != null) setTavilyQ(q) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [runId, result?.status])

  const handleAcceptSuggestion = async (field: string, value: number) => {
    setShowTavily(false)
    try {
      setResult(await applySuggestion(runId, field, value))
    } catch (e) {
      console.error(e)
    }
  }

  const handleRerun = async (code: string) => {
    if (!result) return
    setRerunLoading(true)
    try {
      const updated = await rerun(result.run_id, code)
      setResult(updated)
    } finally {
      setRerunLoading(false)
    }
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-base)' }}>
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-10 w-10 text-[var(--ky-blue)]" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
          </svg>
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Loading result…</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 p-6 min-h-screen" style={{ background: 'var(--bg-base)' }}>

      {/* Top: Drawing LEFT, 3D Model RIGHT */}
      <div className="grid grid-cols-2 gap-6" style={{ height: 450 }}>
        <DrawingPanel src={result.drawing_url} filename="technical_drawing.png" stlUrl={result.stl_url} />
        {result.model_available === false ? (
          <div className="flex flex-col items-center justify-center rounded-xl text-center px-8"
            style={{ background: '#0a0a18', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
            <div style={{ fontSize: 15, fontWeight: 600, color: 'white', marginBottom: 8 }}>
              No 3D model was generated
            </div>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.6, maxWidth: 420 }}>
              The extraction for this drawing couldn’t be turned into a valid part, so nothing
              was built to display.
              {result.stop_reason && (
                <div style={{ marginTop: 12, fontFamily: 'monospace', fontSize: 11.5,
                  color: 'rgba(255,170,51,0.9)', wordBreak: 'break-word' }}>
                  {result.stop_reason}
                </div>
              )}
            </div>
          </div>
        ) : (
          <ModelViewer3D
            stlUrl={result.stl_url}
            view={view}
            onViewChange={setView}
            loading={rerunLoading}
            drawingUrl={result.drawing_url}
            report={result.report ?? undefined}
          />
        )}
      </div>

      {/* Tavily suggestion — real lookup for actual runs, canned card for the demo fixture */}
      {showTavily && result.status === 'done' && (runId === 'demo' || tavilyQ) && (
        <div className="flex justify-start">
          <TavilySuggestionCard
            question={runId === 'demo' ? MOCK_TAVILY_QUESTION : (tavilyQ as TavilyQuestion)}
            onAccept={runId === 'demo' ? () => setShowTavily(false) : handleAcceptSuggestion}
            onIgnore={() => setShowTavily(false)}
          />
        </div>
      )}

      {/* Tabbed bottom section */}
      <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12 }}>
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
          {BOTTOM_TABS.map(tab => (
            <button key={tab.id} onClick={() => setBottomTab(tab.id)} style={{
              padding: '12px 20px', fontSize: 13, fontWeight: 500,
              color: bottomTab === tab.id ? 'white' : 'rgba(255,255,255,0.4)',
              background: 'none', border: 'none',
              borderBottom: bottomTab === tab.id ? '2px solid #4d9aff' : '2px solid transparent',
              marginBottom: -1, cursor: 'pointer', transition: 'color 0.15s',
            }}>
              {tab.label}
            </button>
          ))}
        </div>

        {bottomTab === 'parameters' && (
          result.spec
            ? <PartSpecTab spec={result.spec} />
            : <div style={{ padding: '24px 16px', color: 'rgba(255,255,255,0.35)', fontSize: 13 }}>
                Part specification not available yet.
              </div>
        )}
        {bottomTab === 'validation' && <ValidationPanel report={result.report} />}
        {bottomTab === 'review'     && <VisualReviewPanel runId={result.run_id} onRefined={setResult} />}
        {bottomTab === 'research'   && <TavilyResearchPanel runId={result.run_id} spec={result.spec} onApplied={setResult} />}
        {bottomTab === 'script'     && <ScriptEditor code={result.code} stepUrl={result.step_url} onRerun={handleRerun} />}
      </div>
    </div>
  )
}
