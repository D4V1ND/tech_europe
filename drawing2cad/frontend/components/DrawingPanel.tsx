'use client'
import { useState } from 'react'
import dynamic from 'next/dynamic'
import { Card } from './ui/Card'

const MiniCanvas3D = dynamic(() => import('./MiniCanvas3D'), { ssr: false })

interface DrawingPanelProps {
  src: string
  filename?: string
  stlUrl?: string
}

export function DrawingPanel({ src, filename = 'drawing.png', stlUrl }: DrawingPanelProps) {
  const [fullscreen, setFullscreen] = useState(false)

  return (
    <>
      {/* ── Card (normal view) ── */}
      <Card className="flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[var(--ky-blue)]" />
            <span className="text-xs font-semibold text-white uppercase tracking-widest">Input</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[var(--text-muted)]">{filename}</span>
            <div style={{ width: 1, height: 14, background: 'rgba(255,255,255,0.12)' }} />
            <button
              onClick={() => setFullscreen(true)}
              className="px-2.5 py-1 text-xs rounded-md text-[var(--text-muted)] hover:text-white transition-all"
              title="Fullscreen"
            >
              ⛶
            </button>
          </div>
        </div>
        <div className="flex-1 relative" style={{ minHeight: 300, background: 'white' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt="Technical drawing"
            draggable={false}
            className="absolute inset-0 w-full h-full object-contain"
          />
        </div>
      </Card>

      {/* ── Fullscreen overlay ── */}
      {fullscreen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 100, background: '#f8f8f4' }}>

          {/* Top bar */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, zIndex: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 16px',
            background: 'rgba(255,255,255,0.85)',
            borderBottom: '1px solid rgba(0,0,0,0.08)',
            backdropFilter: 'blur(12px)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--ky-blue)' }} />
              <span style={{ fontSize: 11, fontWeight: 600, color: '#1a1a2e', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                Input · {filename}
              </span>
            </div>
            <button
              onClick={() => setFullscreen(false)}
              style={{
                padding: '4px 12px', fontSize: 11, borderRadius: 6,
                border: '1px solid rgba(0,0,0,0.15)',
                background: 'rgba(0,0,0,0.04)', color: '#1a1a2e', cursor: 'pointer',
              }}
            >
              ✕ Close
            </button>
          </div>

          {/* Mini 3D model — top-left */}
          {stlUrl && (
            <div style={{
              position: 'absolute', top: 57, left: 16, zIndex: 20,
              width: 280, height: 210, borderRadius: 12, overflow: 'hidden',
              background: '#0a0a18',
              border: '1px solid rgba(255,255,255,0.10)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 10px', borderBottom: '1px solid rgba(255,255,255,0.08)',
              }}>
                <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--ky-purple)' }} />
                <span style={{ fontSize: 9, fontWeight: 600, color: 'white', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  Output · 3D
                </span>
              </div>
              <div style={{ height: 'calc(100% - 29px)' }}>
                <MiniCanvas3D stlUrl={stlUrl} />
              </div>
            </div>
          )}

          {/* Full drawing */}
          <div style={{ position: 'absolute', inset: 0, paddingTop: 49, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={src}
              alt="Technical drawing"
              draggable={false}
              style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
            />
          </div>
        </div>
      )}
    </>
  )
}
