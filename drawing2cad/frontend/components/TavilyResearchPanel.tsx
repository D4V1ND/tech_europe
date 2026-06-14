'use client'
import { useState } from 'react'
import { tavilySuggest, tavilySearch, applySuggestion, PartSpec, ReconstructResult, TavilySource } from '@/lib/api'

interface TavilyResearchPanelProps {
  runId: string
  spec: PartSpec | undefined
  onApplied?: (result: ReconstructResult) => void
}

interface ResultState {
  field: string | null   // set for quick-lookups (appliable); null for free-text
  title: string
  answer: string
  suggestion: number | null
  sources: TavilySource[]
}

export function TavilyResearchPanel({ runId, spec, onApplied }: TavilyResearchPanelProps) {
  const [loading, setLoading] = useState<string | null>(null)   // which lookup is running
  const [result, setResult] = useState<ResultState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)

  // Quick-lookup chips: standard gaps + every named dimension in the spec
  const chips: { field: string; label: string }[] = [
    { field: 'thickness', label: 'Wall thickness' },
    ...(spec?.holes?.length ? [{ field: 'hole_diameter', label: 'Hole diameter' }] : []),
    { field: 'thread_pitch', label: 'Thread pitch' },
    ...(spec?.dimensions ?? []).map(d => ({ field: d.name, label: d.name.replace(/_/g, ' ') })),
  ]

  const lookupField = async (field: string, label: string) => {
    setLoading(field); setError(null); setApplied(false)
    try {
      const r = await tavilySuggest(runId, field)
      setResult({ field, title: `Standard ${label}`, answer: r.question, suggestion: r.tavily_suggestion, sources: r.sources ?? [] })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Tavily lookup failed')
    } finally {
      setLoading(null)
    }
  }

  const runSearch = async () => {
    if (!query.trim()) return
    setLoading('__query'); setError(null); setApplied(false)
    try {
      const r = await tavilySearch(query.trim())
      setResult({ field: null, title: query.trim(), answer: r.answer, suggestion: null, sources: r.sources })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Tavily search failed')
    } finally {
      setLoading(null)
    }
  }

  const applyToModel = async () => {
    if (!result?.field || result.suggestion == null) return
    setApplying(true); setError(null)
    try {
      const updated = await applySuggestion(runId, result.field, result.suggestion)
      onApplied?.(updated)
      setApplied(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Apply failed')
    } finally {
      setApplying(false)
    }
  }

  return (
    <div style={{ padding: '16px' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'white', marginBottom: 4 }}>
        🔍 Tavily Research
      </div>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 1.5, marginBottom: 14, maxWidth: 620 }}>
        Drawings are often under-dimensioned. Tavily searches the live web for the standard
        engineering value of a missing or uncertain field — with citable sources.
        {spec?.notes && <span style={{ color: 'rgba(255,255,255,0.6)' }}> Context: <i>{spec.notes}</i></span>}
      </div>

      {/* Free-text research */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') runSearch() }}
          placeholder="Ask Tavily about this part… e.g. standard M6 thread pitch"
          style={{
            flex: 1, padding: '9px 14px', fontSize: 13, borderRadius: 8, color: 'white',
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', outline: 'none',
          }}
        />
        <button
          onClick={runSearch}
          disabled={loading === '__query'}
          style={{
            padding: '9px 18px', fontSize: 13, fontWeight: 600, color: 'white',
            background: loading === '__query' ? 'rgba(255,255,255,0.06)' : '#4d9aff',
            border: 'none', borderRadius: 8, cursor: 'pointer',
          }}
        >
          {loading === '__query' ? 'Searching…' : 'Search'}
        </button>
      </div>

      {/* Quick lookups */}
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
        color: 'rgba(255,255,255,0.35)', marginBottom: 8 }}>
        Quick lookups
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {chips.map(c => (
          <button
            key={c.field}
            onClick={() => lookupField(c.field, c.label)}
            disabled={loading === c.field}
            style={{
              padding: '6px 12px', fontSize: 12, borderRadius: 100, cursor: 'pointer',
              color: loading === c.field ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.8)',
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.12)',
              textTransform: 'capitalize',
            }}
          >
            {loading === c.field ? 'Looking up…' : c.label}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, fontSize: 12,
          background: 'rgba(255,60,60,0.1)', color: '#ff8888', border: '1px solid rgba(255,60,60,0.2)' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ padding: '14px 16px', borderRadius: 10,
          background: 'rgba(77,154,255,0.06)', border: '1px solid rgba(77,154,255,0.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#4d9aff', textTransform: 'capitalize' }}>
              {result.title}
            </span>
            {result.suggestion != null && (
              <span style={{ fontSize: 12, fontWeight: 700, padding: '2px 10px', borderRadius: 100,
                background: 'rgba(52,211,153,0.12)', color: '#34d399', border: '1px solid rgba(52,211,153,0.4)' }}>
                ≈ {result.suggestion} mm
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.78)', lineHeight: 1.55, marginBottom: 12 }}>
            {result.answer}
          </div>
          {result.sources.length > 0 && (
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
                color: 'rgba(255,255,255,0.3)', marginBottom: 6 }}>
                Sources
              </div>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {result.sources.map((s, i) => (
                  <li key={i}>
                    <a href={s.url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 12, color: '#4d9aff', textDecoration: 'none' }}>
                      ↗ {s.title || s.url.replace(/^https?:\/\//, '')}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Apply the looked-up value into the spec and rebuild the model */}
          {result.field && result.suggestion != null && (
            <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
              <button
                onClick={applyToModel}
                disabled={applying || applied}
                style={{
                  padding: '8px 16px', fontSize: 12.5, fontWeight: 600,
                  color: applied ? '#34d399' : 'white',
                  background: applied ? 'rgba(52,211,153,0.12)'
                    : applying ? 'rgba(255,255,255,0.06)' : '#34d399',
                  border: applied ? '1px solid rgba(52,211,153,0.4)' : 'none',
                  borderRadius: 8, cursor: applying || applied ? 'default' : 'pointer',
                }}
              >
                {applied ? '✓ Applied & rebuilt' : applying ? 'Applying…'
                  : `Apply ${result.suggestion} mm to model`}
              </button>
              <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)' }}>
                Patches the spec and rebuilds — the 3D model & validation refresh.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
