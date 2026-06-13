import { Card } from './ui/Card'
import { ValidationReport } from '@/lib/api'

const PARAM_MAP: Record<string, string> = {
  overall_width:  'box(width, …)',
  overall_height: 'box(…, height, …)',
  thickness:      'box(…, …, thickness)',
  hole0_dia:      '.hole(hole_dia)',
  hole0_x:        'pushPoints([(hole_x - width/2, …)])',
  hole0_y:        'pushPoints([(…, hole_y - height/2)])',
}

interface ValidationPanelProps {
  report: ValidationReport | null
}

export function ValidationPanel({ report }: ValidationPanelProps) {
  if (!report) {
    return (
      <div style={{ padding: '24px 16px', color: 'rgba(255,255,255,0.35)', fontSize: 13 }}>
        Validation not available — validator module not yet implemented.
      </div>
    )
  }
  const failCount = report.checks.filter(c => !c.passed).length

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-white uppercase tracking-widest">Validation</span>
          <span className="text-xs text-[var(--text-muted)]">Attempts: {report.attempts}</span>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
          report.passed
            ? 'bg-[rgba(77,154,255,0.15)] text-[var(--green-pass)]'
            : 'bg-[rgba(255,60,60,0.15)] text-[var(--red-text)]'
        }`}>
          <span>{report.passed ? '●' : '✗'}</span>
          <span>{report.passed ? 'PASSED' : `FAILED (${failCount} ${failCount === 1 ? 'error' : 'errors'})`}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Dimension', 'Target', 'Actual', 'Tolerance', 'Status', 'In model'].map(h => (
                <th key={h} className="px-4 py-2 text-left text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {report.checks.map((check, i) => (
              <tr
                key={i}
                style={{
                  background: check.passed ? 'transparent' : 'var(--red-fail)',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                <td className="px-4 py-2.5 font-mono text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {check.name}
                </td>
                <td className="px-4 py-2.5 text-xs text-white">
                  {check.target != null ? `${check.target} mm` : '—'}
                </td>
                <td className={`px-4 py-2.5 text-xs font-medium ${check.passed ? 'text-white' : 'text-[var(--red-text)]'}`}>
                  {check.actual != null ? `${check.actual} mm` : 'missing'}
                </td>
                <td className="px-4 py-2.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                  ±{check.tolerance} mm
                </td>
                <td className="px-4 py-2.5 text-xs">
                  {check.passed
                    ? <span style={{ color: 'var(--green-pass)' }}>✓</span>
                    : <span style={{ color: 'var(--red-text)' }}>✗</span>
                  }
                </td>
                <td className="px-4 py-2.5 font-mono text-xs" style={{ color: 'var(--text-muted)' }}>
                  {PARAM_MAP[check.name] ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
