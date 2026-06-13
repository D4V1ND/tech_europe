'use client'
import { useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { PipelineStatus } from './PipelineStatus'
import { Button } from './ui/Button'
import { reconstruct } from '@/lib/api'

interface Props {
  open: boolean
  onClose: () => void
}

interface QueueItem {
  file: File
  preview: string
}

export function NewAnalysisModal({ open, onClose }: Props) {
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<QueueItem[]>([])
  const [processing, setProcessing] = useState(false)
  const [pipelineStep, setPipelineStep] = useState(-1)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const addFiles = (newFiles: FileList | null) => {
    if (!newFiles) return
    setFiles(prev => [
      ...prev,
      ...Array.from(newFiles).map(f => ({ file: f, preview: URL.createObjectURL(f) })),
    ])
  }

  const handleStart = async () => {
    if (!files.length) return
    setProcessing(true)
    setError(null)
    setPipelineStep(0)
    try {
      const result = await reconstruct(files[0].file, (step) => setPipelineStep(step))
      setPipelineStep(-1)
      await new Promise(r => setTimeout(r, 1000))
      setProcessing(false)
      onClose()
      router.push(`/result/${result.run_id}`)
    } catch (e) {
      setProcessing(false)
      setError(e instanceof Error ? e.message : 'Reconstruction failed')
    }
  }

  const previewItems = files.slice(0, 5)
  const overflow = files.length - 5

  return (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      onClick={e => { if (e.target === e.currentTarget && !processing) onClose() }}
    >
      {/* Backdrop */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }} />

      {/* Card */}
      <div
        style={{
          position: 'relative', zIndex: 1,
          width: '100%', maxWidth: 560,
          margin: '0 24px',
          background: '#0d0a1b',
          border: '1px solid rgba(255,255,255,0.09)',
          borderRadius: 20,
          boxShadow: '0 24px 80px rgba(0,0,0,0.7), inset 0 1px rgba(255,255,255,0.07)',
          padding: 28,
          display: 'flex',
          flexDirection: 'column',
          gap: 20,
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: 'white', margin: 0 }}>New Analysis</h2>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              Drop technical drawings to reconstruct parametric CAD models
            </p>
          </div>
          {!processing && (
            <button
              onClick={onClose}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18, padding: '0 4px' }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Drop zone */}
        <div
          style={{
            borderRadius: 12,
            border: `2px dashed ${dragOver ? 'var(--ky-blue)' : 'rgba(255,255,255,0.12)'}`,
            background: dragOver ? 'rgba(77,154,255,0.06)' : 'rgba(255,255,255,0.03)',
            cursor: processing ? 'default' : 'pointer',
            transition: 'all 0.2s',
          }}
          onClick={() => !processing && inputRef.current?.click()}
          onDrop={e => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept="image/*,.pdf"
            style={{ display: 'none' }}
            onChange={e => addFiles(e.target.files)}
          />

          {files.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, padding: '32px 24px' }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(77,154,255,0.1)', fontSize: 20,
              }}>📐</div>
              <p style={{ color: 'white', fontWeight: 500, fontSize: 14, margin: 0 }}>
                Drop drawings here or click to browse
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: 0 }}>
                PNG · JPG · PDF — multiple files supported
              </p>
            </div>
          ) : (
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {previewItems.map((item, i) => (
                  <div key={i} style={{ width: 56, height: 56, borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={item.preview} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                ))}
                {overflow > 0 && (
                  <div style={{
                    width: 56, height: 56, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600,
                    border: '1px solid var(--border)',
                  }}>
                    +{overflow}
                  </div>
                )}
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
                {files.length} {files.length === 1 ? 'drawing' : 'drawings'} selected
                <button
                  style={{ marginLeft: 8, fontSize: 11, color: 'var(--ky-blue)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                  onClick={e => { e.stopPropagation(); setFiles([]) }}
                >
                  clear
                </button>
              </p>
            </div>
          )}
        </div>

        {/* Pipeline status (while processing) */}
        {processing && (
          <div style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: 12, border: '1px solid var(--border)' }}>
            <PipelineStatus activeStep={pipelineStep} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.3)', fontSize: 12, color: '#ff6b6b' }}>
            {error}
          </div>
        )}

        {/* Footer */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
          <Button
            onClick={handleStart}
            loading={processing}
            disabled={!files.length || processing}
          >
            ✦ Reconstruct
          </Button>
        </div>
      </div>
    </div>
  )
}
