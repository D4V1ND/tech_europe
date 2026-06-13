'use client'
import { useState } from 'react'

function KyrallLogo() {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/kyrall-logo-real.png"
      alt="Kyrall"
      style={{ height: 83, width: 'auto', mixBlendMode: 'screen' }}
    />
  )
}

export function Navbar() {
  const [ctaHovered, setCtaHovered] = useState(false)

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-2"
      style={{
        background: '#453889',
        borderBottom: 'none',
      }}
    >
      <a href="/">
        <KyrallLogo />
      </a>
      <div className="flex items-center gap-3">
        <a
          href="/"
          className="px-5 py-2 text-sm font-semibold text-white"
          style={{
            background: ctaHovered ? 'var(--cta-hover)' : 'var(--cta)',
            borderRadius: '100px',
            backdropFilter: 'blur(16px) saturate(180%)',
            boxShadow: 'inset -1px -1px #fff6, inset 1px 1px #fff3',
            transition: 'all 0.4s cubic-bezier(.4, 0, .2, 1)',
          }}
          onMouseEnter={() => setCtaHovered(true)}
          onMouseLeave={() => setCtaHovered(false)}
        >
          ✦ New Drawing
        </a>
        <a
          href="/dashboard"
          className="flex items-center gap-2 select-none"
          style={{ textDecoration: 'none' }}
        >
          <div
            className="flex items-center justify-center text-xs font-bold text-white"
            style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'linear-gradient(135deg, #5a4db0, #3e3281)',
              border: '2px solid rgba(255,255,255,0.25)',
              flexShrink: 0,
            }}
          >
            EM
          </div>
          <span className="text-sm font-medium text-white hidden sm:block" style={{ opacity: 0.9 }}>
            Elon Musk
          </span>
        </a>
      </div>
    </nav>
  )
}
