'use client'
import { useState } from 'react'
import { TavilyQuestion } from '@/lib/api'
import { Button } from './ui/Button'

interface TavilySuggestionCardProps {
  question: TavilyQuestion
  onAccept: (field: string, value: number) => void
  onIgnore: (field: string) => void
}

export function TavilySuggestionCard({ question, onAccept, onIgnore }: TavilySuggestionCardProps) {
  const [customValue, setCustomValue] = useState(String(question.tavily_suggestion))

  return (
    <div
      className="rounded-xl border shadow-xl p-4 flex flex-col gap-3 w-72 animate-in slide-in-from-bottom-2"
      style={{
        backdropFilter: 'blur(32px) saturate(180%)',
        WebkitBackdropFilter: 'blur(32px) saturate(180%)',
        background: 'var(--card-bg)',
        borderColor: 'var(--ky-purple)',
        boxShadow: '0 0 20px rgba(62,50,129,0.4), inset 0 1px #ffffff12',
      }}
    >
      <div className="flex items-start gap-2">
        <span className="text-[var(--ky-blue)] text-base mt-0.5">🔍</span>
        <div>
          <p className="text-xs font-semibold text-white mb-1">Tavily Suggestion</p>
          <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{question.question}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="number"
          value={customValue}
          onChange={e => setCustomValue(e.target.value)}
          className="flex-1 rounded-md px-3 py-1.5 text-sm font-mono text-white outline-none focus:ring-1"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
        />
        <span className="text-xs text-[var(--text-muted)]">mm</span>
      </div>

      {question.source_url && (
        <a
          href={question.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs truncate hover:underline"
          style={{ color: 'var(--ky-blue)' }}
        >
          ↗ {question.source_url.replace(/^https?:\/\//, '')}
        </a>
      )}

      <div className="flex gap-2 justify-end">
        <Button variant="secondary" onClick={() => onIgnore(question.field)} className="text-xs py-1.5">
          Dismiss
        </Button>
        <Button onClick={() => onAccept(question.field, Number(customValue))} className="text-xs py-1.5">
          ✓ Apply
        </Button>
      </div>
    </div>
  )
}
