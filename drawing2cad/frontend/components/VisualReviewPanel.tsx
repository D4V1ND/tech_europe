'use client'
import { useState } from 'react'
import { visualValidate, refine, VisualVerdict, ReconstructResult } from '@/lib/api'

interface VisualReviewPanelProps {
  runId: string
  onRefined?: (result: ReconstructResult) => void
}

export function VisualReviewPanel({ runId, onRefined }: VisualReviewPanelProps) {
  const [loading, setLoading] = useState(false)
  const [verdict, setVerdict] = useState<VisualVerdict | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refining, setRefining] = useState(false)
  const [refined, setRefined] = useState(false)

  const run = async () => {
    setLoading(true)
    setError(null)
    setRefined(false)
    try {
      setVerdict(await visualValidate(runId))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Visual review failed')
    } finally {
      setLoading(false)
    }
  }

  const runRefine = async () => {
    if (!verdict) return
    setRefining(true)
    setError(null)
    try {
      const updated = await refine(runId, verdict.discrepancies)
      onRefined?.(updated)
      setRefined(true)
      setVerdict(null)   // verdict is stale now — the model changed
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Refine failed')
    } finally {
      setRefining(false)
    }
  }

  return (
    <div style={{ padding: '16px' }}>
      {/* Intro + trigger */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ maxWidth: 520 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'white', marginBottom: 4 }}>
            AI Visual Review
          </div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', lineHeight: 1.5 }}>
            Renders the generated 3D model and asks the vision model to compare it against the
            original drawing — catching missing holes, wrong shapes, or extra bodies that the
            geometric validator cannot see. Advisory only.
          </div>
        </div>
        <button
          onClick={run}
          disabled={loading}
          style={{
            flexShrink: 0,
            padding: '9px 18px', fontSize: 13, fontWeight: 600,
            color: loading ? 'rgba(255,255,255,0.4)' : 'white',
            background: loading ? 'rgba(255,255,255,0.06)' : '#4d9aff',
            border: 'none', borderRadius: 8,
            cursor: loading ? 'default' : 'pointer',
            transition: 'background 0.15s',
          }}
        >
          {loading ? 'Reviewing…' : verdict ? 'Re-run Review' : 'Run AI Review'}
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 14, padding: '10px 14px', borderRadius: 8, fontSize: 12,
          background: 'rgba(255,60,60,0.1)', color: '#ff8888', border: '1px solid rgba(255,60,60,0.2)' }}>
          {error}
        </div>
      )}

      {verdict && (
        <div style={{ marginTop: 16, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          {/* Render the judge saw */}
          <img
            src={verdict.render_url}
            alt="Rendered model views"
            style={{ width: 300, borderRadius: 10, border: '1px solid rgba(255,255,255,0.1)', background: '#0a0a18' }}
          />

          {/* Verdict */}
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{
                fontSize: 12, fontWeight: 700, padding: '4px 12px', borderRadius: 100,
                background: verdict.matches ? 'rgba(52,211,153,0.12)' : 'rgba(255,170,50,0.12)',
                color: verdict.matches ? '#34d399' : '#ffaa33',
                border: `1px solid ${verdict.matches ? 'rgba(52,211,153,0.4)' : 'rgba(255,170,50,0.4)'}`,
              }}>
                {verdict.matches ? '● MATCHES DRAWING' : '▲ DISCREPANCIES FOUND'}
              </span>
              <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)' }}>
                {Math.round(verdict.confidence * 100)}% confidence
              </span>
            </div>

            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', lineHeight: 1.55, marginBottom: 14 }}>
              {verdict.assessment}
            </div>

            {verdict.discrepancies.length > 0 && (
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
                  color: 'rgba(255,255,255,0.35)', marginBottom: 8 }}>
                  Discrepancies ({verdict.discrepancies.length})
                </div>
                <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {verdict.discrepancies.map((d, i) => (
                    <li key={i} style={{ display: 'flex', gap: 8, fontSize: 12.5, color: 'rgba(255,255,255,0.7)', lineHeight: 1.45 }}>
                      <span style={{ color: '#ffaa33', flexShrink: 0 }}>•</span>
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>

                {/* Feed the findings back into the extractor for a corrected spec */}
                <button
                  onClick={runRefine}
                  disabled={refining}
                  style={{
                    marginTop: 16,
                    padding: '9px 18px', fontSize: 13, fontWeight: 600,
                    color: refining ? 'rgba(255,255,255,0.4)' : 'white',
                    background: refining ? 'rgba(255,255,255,0.06)' : 'rgba(255,170,51,0.85)',
                    border: 'none', borderRadius: 8,
                    cursor: refining ? 'default' : 'pointer',
                    transition: 'background 0.15s',
                  }}
                >
                  {refining ? 'Re-extracting with feedback…' : '↻ Refine extraction with this feedback'}
                </button>
                <div style={{ marginTop: 8, fontSize: 11, color: 'rgba(255,255,255,0.35)', lineHeight: 1.5 }}>
                  Sends these findings back to the extractor to produce a corrected, more
                  detailed spec, then rebuilds and re-validates the model.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {refined && (
        <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, fontSize: 13,
          background: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.3)' }}>
          ✓ Model refined. The 3D view, parameters, and validation have been updated with the
          new extraction. Run the review again to check the improved result.
        </div>
      )}
    </div>
  )
}
