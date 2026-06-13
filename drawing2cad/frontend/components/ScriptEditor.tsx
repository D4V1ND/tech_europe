'use client'
import dynamic from 'next/dynamic'
import { useState } from 'react'
import { Button } from './ui/Button'
import { Card } from './ui/Card'

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

interface ScriptEditorProps {
  code: string
  stepUrl: string
  onRerun: (code: string) => Promise<void>
}

export function ScriptEditor({ code: initialCode, stepUrl, onRerun }: ScriptEditorProps) {
  const [code, setCode] = useState(initialCode)
  const [loading, setLoading] = useState(false)

  const handleRerun = async () => {
    setLoading(true)
    try {
      await onRerun(code)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-white uppercase tracking-widest">Parametric Script</span>
          <span className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>part.py</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => window.open(stepUrl)} className="text-xs">
            ↓ Download STEP
          </Button>
          <Button onClick={handleRerun} loading={loading} disabled={loading} className="text-xs">
            ↻ Re-run
          </Button>
        </div>
      </div>
      <div style={{ height: 280 }}>
        <MonacoEditor
          height="100%"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={v => setCode(v ?? '')}
          options={{
            fontSize: 13,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            padding: { top: 12, bottom: 12 },
            lineNumbers: 'on',
            renderLineHighlight: 'line',
          }}
        />
      </div>
    </Card>
  )
}
