'use client'
import { clsx } from 'clsx'
import { ReactNode, useState } from 'react'

interface ButtonProps {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
  loading?: boolean
  className?: string
  type?: 'button' | 'submit'
}

export function Button({
  children, onClick, variant = 'primary', disabled, loading, className, type = 'button'
}: ButtonProps) {
  const [hovered, setHovered] = useState(false)

  const primaryStyle = {
    background: hovered ? 'var(--cta-hover)' : 'var(--cta)',
    borderRadius: '100px' as const,
    backdropFilter: 'blur(16px) saturate(180%)',
    boxShadow: 'inset -1px -1px #fff6, inset 1px 1px #fff3',
    transition: 'all 0.4s cubic-bezier(.4, 0, .2, 1)',
    color: 'white',
  }

  const secondaryStyle = {
    background: hovered
      ? 'linear-gradient(150deg, #2a2a2a1a, #c0c0c01a 80%, #90909033)'
      : 'linear-gradient(150deg, #1a1a1a1a, #a4a3a31a 80%, #79727233)',
    borderRadius: '100px' as const,
    backdropFilter: 'blur(16px) saturate(180%)',
    border: '1px solid rgba(255,255,255,0.12)',
    transition: 'all 0.4s cubic-bezier(.4, 0, .2, 1)',
    color: hovered ? 'white' : 'rgba(255,255,255,0.7)',
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={clsx(
        'inline-flex items-center gap-2 px-5 py-2.5 font-medium text-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      style={variant === 'primary' ? primaryStyle : variant === 'secondary' ? secondaryStyle : undefined}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      )}
      {children}
    </button>
  )
}
