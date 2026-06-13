import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'drawing2cad — Technical Drawings to Parametric CAD',
  description: 'Turn legacy technical drawings into validated, editable parametric 3D models.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className="h-full">
      <body className="min-h-full flex flex-col" style={{ background: 'var(--bg-base)' }}>
        <Navbar />
        <main className="flex-1" style={{ paddingTop: 99 }}>{children}</main>
      </body>
    </html>
  )
}
