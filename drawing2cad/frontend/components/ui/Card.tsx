import { clsx } from 'clsx'
import { ReactNode } from 'react'

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={clsx('rounded-xl border', className)}
      style={{
        backdropFilter: 'blur(32px) saturate(180%)',
        WebkitBackdropFilter: 'blur(32px) saturate(180%)',
        background: 'var(--card-bg)',
        borderColor: 'rgba(255,255,255,0.07)',
        boxShadow: '0 4px 20px #0006, inset 0 1px #ffffff12',
      }}
    >
      {children}
    </div>
  )
}
