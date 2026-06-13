'use client'
import { useRouter } from 'next/navigation'
import { PerspectiveGrid } from '@/components/ui/PerspectiveGrid'
import { Button } from '@/components/ui/Button'

export default function Home() {
  const router = useRouter()

  return (
    <div
      className="relative min-h-screen flex flex-col items-center justify-center px-6 py-20 overflow-hidden"
      style={{ background: '#3e3281' }}
    >
      <PerspectiveGrid />

      <div className="relative z-10 flex flex-col items-center gap-10 max-w-2xl w-full text-center">
        <div>
          <h1
            className="uppercase leading-none mb-6 text-white"
            style={{
              fontFamily: "'Poppins', system-ui, sans-serif",
              fontWeight: 600,
              fontSize: 'clamp(3rem, 9vw, 7rem)',
              letterSpacing: '-0.01em',
            }}
          >
            DRAWINGS<br />TO CAD
          </h1>
          <p className="text-lg max-w-md mx-auto text-white" style={{ fontWeight: 400, opacity: 0.85 }}>
            Upload a technical drawing — get a validated, parametric 3D model. Nothing faked.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Button onClick={() => router.push('/dashboard')}>
            ✦ Open Dashboard
          </Button>
          <a
            href="/result/demo"
            style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14, textDecoration: 'none' }}
          >
            View example →
          </a>
        </div>

        <p className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>
          From idea to manufacturable model in seconds · Kyrall AI-powered CAD
        </p>
      </div>
    </div>
  )
}
