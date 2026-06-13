'use client'
import { Suspense, useEffect, useState, useMemo, useRef } from 'react'
import { Canvas, ThreeEvent, useThree } from '@react-three/fiber'
import { OrbitControls, Grid, Line, Html } from '@react-three/drei'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import { useLoader } from '@react-three/fiber'
import * as THREE from 'three'
import { Card } from './ui/Card'
import type { ValidationReport, Check } from '@/lib/api'

type ViewPreset = 'iso' | 'top' | 'bottom' | 'front' | 'inside'
type FaceName = 'top' | 'bottom' | 'right' | 'left' | 'front' | 'back'

const VIEW_PRESETS: { id: ViewPreset; label: string }[] = [
  { id: 'iso',    label: 'ISO' },
  { id: 'top',    label: 'Top ↑' },
  { id: 'bottom', label: 'Bottom ↓' },
  { id: 'front',  label: 'Front' },
  { id: 'inside', label: 'Inside' },
]

const CAMERA_POSITIONS: Record<ViewPreset, [number, number, number]> = {
  iso:    [60, 45, 60],
  top:    [0, 100, 0.01],
  bottom: [0, -100, 0.01],
  front:  [0, 0, 100],
  inside: [5, 2, 5],
}

// Which 3D axis a check name measures — used to place dimension arrows
const AXIS_FOR_CHECK: Record<string, 'x' | 'y' | 'z'> = {
  overall_width:  'x',
  overall_height: 'y',
  thickness:      'z',
  hole0_dia:      'y',
  hole0_x:        'x',
  hole0_y:        'y',
}

function normalToFace(nx: number, ny: number, nz: number): FaceName {
  const ax = Math.abs(nx), ay = Math.abs(ny), az = Math.abs(nz)
  if (ay >= ax && ay >= az) return ny > 0 ? 'top' : 'bottom'
  if (ax >= ay && ax >= az) return nx > 0 ? 'right' : 'left'
  return nz > 0 ? 'front' : 'back'
}

// ── STLModel ──────────────────────────────────────────────────────────────────

function STLModel({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url)
  const [activeFace, setActiveFace] = useState<FaceName | null>(null)

  const coloredGeo = useMemo(() => {
    const geo = geometry.clone()
    geo.center()
    const count = geo.attributes.position.count
    const colors = new Float32Array(count * 3).fill(0.941)
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    return geo
  }, [geometry])

  const edgesGeo = useMemo(() => {
    const geo = geometry.clone()
    geo.center()
    const eg = new THREE.EdgesGeometry(geo, 12)
    geo.dispose()
    return eg
  }, [geometry])

  useEffect(() => () => { coloredGeo.dispose(); edgesGeo.dispose() }, [coloredGeo, edgesGeo])

  useEffect(() => {
    const nor = coloredGeo.attributes.normal as THREE.BufferAttribute
    const col = coloredGeo.attributes.color as THREE.BufferAttribute
    const highlighted = new THREE.Color('#6ab0ff')
    for (let i = 0; i < coloredGeo.attributes.position.count; i++) {
      if (activeFace && normalToFace(nor.getX(i), nor.getY(i), nor.getZ(i)) === activeFace) {
        col.setXYZ(i, highlighted.r, highlighted.g, highlighted.b)
      } else {
        col.setXYZ(i, 0.941, 0.941, 0.941)
      }
    }
    col.needsUpdate = true
  }, [activeFace, coloredGeo])

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    if (!e.face) return
    const face = normalToFace(e.face.normal.x, e.face.normal.y, e.face.normal.z)
    setActiveFace(prev => prev === face ? null : face)
  }

  return (
    <>
      <mesh geometry={coloredGeo} castShadow receiveShadow onClick={handleClick}>
        <meshStandardMaterial vertexColors roughness={0.3} metalness={0.1} />
      </mesh>
      <lineSegments geometry={edgesGeo}>
        <lineBasicMaterial color="#c0c8e0" opacity={0.7} transparent />
      </lineSegments>
    </>
  )
}

// ── DimensionArrows ───────────────────────────────────────────────────────────

function ArrowCone({
  tip, direction, size, color,
}: {
  tip: THREE.Vector3; direction: THREE.Vector3; size: number; color: string
}) {
  const quaternion = useMemo(() => {
    const q = new THREE.Quaternion()
    q.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction)
    return q
  }, [direction])
  // shift cone so its TIP is at `tip`, not its center
  const pos = useMemo(() => tip.clone().sub(direction.clone().multiplyScalar(size * 0.75)), [tip, direction, size])
  return (
    <mesh position={pos} quaternion={quaternion}>
      <coneGeometry args={[size * 0.35, size * 1.5, 8]} />
      <meshBasicMaterial color={color} />
    </mesh>
  )
}

function DimensionArrows({ stlUrl, check }: { stlUrl: string; check: Check | null }) {
  const geometry = useLoader(STLLoader, stlUrl)

  const bounds = useMemo(() => {
    const geo = geometry.clone()
    geo.center()
    geo.computeBoundingBox()
    const bb = geo.boundingBox!
    const result = { min: bb.min.clone(), max: bb.max.clone() }
    geo.dispose()
    return result
  }, [geometry])

  if (!check) return null
  const axis = AXIS_FOR_CHECK[check.name]
  if (!axis) return null

  const color = check.passed ? '#44ff88' : '#ff4444'
  const { min, max } = bounds
  const span = Math.max(max.x - min.x, max.y - min.y, max.z - min.z)
  const gap = span * 0.22
  const coneSize = span * 0.045

  let from: THREE.Vector3, to: THREE.Vector3
  let leaders: Array<[THREE.Vector3, THREE.Vector3]> = []

  const midX = (min.x + max.x) / 2
  const midY = (min.y + max.y) / 2
  const midZ = (min.z + max.z) / 2

  if (axis === 'x') {
    const arrowY = max.y + gap
    from = new THREE.Vector3(min.x, arrowY, midZ)
    to   = new THREE.Vector3(max.x, arrowY, midZ)
    leaders = [
      [new THREE.Vector3(min.x, max.y, midZ), new THREE.Vector3(min.x, arrowY, midZ)],
      [new THREE.Vector3(max.x, max.y, midZ), new THREE.Vector3(max.x, arrowY, midZ)],
    ]
  } else if (axis === 'y') {
    const arrowX = max.x + gap
    from = new THREE.Vector3(arrowX, min.y, midZ)
    to   = new THREE.Vector3(arrowX, max.y, midZ)
    leaders = [
      [new THREE.Vector3(max.x, min.y, midZ), new THREE.Vector3(arrowX, min.y, midZ)],
      [new THREE.Vector3(max.x, max.y, midZ), new THREE.Vector3(arrowX, max.y, midZ)],
    ]
  } else {
    const arrowX = max.x + gap * 0.6
    const arrowY = max.y + gap * 0.6
    from = new THREE.Vector3(arrowX, arrowY, min.z)
    to   = new THREE.Vector3(arrowX, arrowY, max.z)
    leaders = [
      [new THREE.Vector3(max.x, max.y, min.z), new THREE.Vector3(arrowX, arrowY, min.z)],
      [new THREE.Vector3(max.x, max.y, max.z), new THREE.Vector3(arrowX, arrowY, max.z)],
    ]
  }

  const dir = new THREE.Vector3().subVectors(to, from).normalize()
  const mid = new THREE.Vector3().addVectors(from, to).multiplyScalar(0.5)

  const toArr = (v: THREE.Vector3): [number, number, number] => [v.x, v.y, v.z]

  return (
    <>
      {/* Main dimension line */}
      <Line points={[toArr(from), toArr(to)]} color={color} lineWidth={2.5} />

      {/* Arrowheads */}
      <ArrowCone tip={from} direction={dir.clone().negate()} size={coneSize} color={color} />
      <ArrowCone tip={to}   direction={dir}                   size={coneSize} color={color} />

      {/* Leader lines */}
      {leaders.map(([a, b], i) => (
        <Line key={i} points={[toArr(a), toArr(b)]} color={color} lineWidth={1} opacity={0.45} transparent />
      ))}

      {/* Floating label */}
      <Html position={toArr(mid)} center style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'rgba(10,8,30,0.88)',
          border: `1px solid ${color}`,
          color,
          padding: '3px 9px',
          borderRadius: 6,
          fontSize: 12,
          fontFamily: 'monospace',
          fontWeight: 700,
          whiteSpace: 'nowrap',
          backdropFilter: 'blur(6px)',
          boxShadow: `0 0 12px ${color}44`,
        }}>
          {check.actual ?? '?'} mm&nbsp;&nbsp;
          <span style={{ opacity: 0.65, fontSize: 10 }}>
            target {check.target} ±{check.tolerance}
          </span>
          &nbsp;&nbsp;{check.passed ? '✓' : '✕'}
        </div>
      </Html>
    </>
  )
}

// ── Scene ─────────────────────────────────────────────────────────────────────

function CameraController({ view }: { view: ViewPreset }) {
  const { camera } = useThree()
  useEffect(() => {
    const [x, y, z] = CAMERA_POSITIONS[view]
    camera.position.set(x, y, z)
    camera.lookAt(0, 0, 0)
  }, [view, camera])
  return <OrbitControls enableDamping dampingFactor={0.05} makeDefault />
}

function Scene({
  stlUrl, view, activeCheck,
}: {
  stlUrl: string; view: ViewPreset; activeCheck: Check | null
}) {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[50, 80, 60]} intensity={1.2} castShadow />
      <directionalLight position={[-50, -60, -60]} intensity={0.45} />
      <directionalLight position={[-20, -30, 30]} intensity={0.2} />
      <Suspense fallback={null}>
        <STLModel url={stlUrl} />
        <DimensionArrows stlUrl={stlUrl} check={activeCheck} />
      </Suspense>
      <Grid
        args={[200, 200]}
        cellSize={5} cellThickness={0.5} cellColor="#3e3281"
        sectionSize={25} sectionThickness={1} sectionColor="#5a4db0"
        fadeDistance={120} fadeStrength={1} infiniteGrid
      />
      <CameraController view={view} />
    </>
  )
}

// ── MiniDrawing ───────────────────────────────────────────────────────────────

function MiniDrawing({ src }: { src: string }) {
  const [scale, setScale] = useState(1)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const dragging = useRef(false)
  const dragStart = useRef({ x: 0, y: 0 })
  const viewportRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = viewportRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setScale(s => Math.max(0.5, Math.min(5, s - e.deltaY * 0.001)))
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  })

  return (
    <div style={{
      position: 'absolute', top: 16, left: 16, zIndex: 20,
      width: 360, borderRadius: 12, overflow: 'hidden',
      background: 'rgba(10,10,24,0.85)',
      border: '1px solid rgba(255,255,255,0.10)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      backdropFilter: 'blur(12px)',
    }}>
      <div className="flex items-center gap-2 px-3 py-2" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--ky-blue)' }} />
        <span className="text-[10px] font-semibold text-white uppercase tracking-widest">Input</span>
        <span className="ml-auto text-[9px]" style={{ color: 'var(--text-muted)' }}>scroll · drag</span>
      </div>
      <div
        ref={viewportRef}
        style={{ height: 280, overflow: 'hidden', position: 'relative', cursor: 'grab' }}
        onMouseDown={e => { dragging.current = true; dragStart.current = { x: e.clientX - pos.x, y: e.clientY - pos.y } }}
        onMouseMove={e => { if (dragging.current) setPos({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y }) }}
        onMouseUp={() => { dragging.current = false }}
        onMouseLeave={() => { dragging.current = false }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt="drawing" draggable={false} style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'contain',
          transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
          transformOrigin: 'center',
        }} />
      </div>
    </div>
  )
}

// ── MiniParams ────────────────────────────────────────────────────────────────

function MiniParams({
  report, selected, onSelect,
}: {
  report: ValidationReport
  selected: string | null
  onSelect: (name: string | null) => void
}) {
  return (
    <div style={{
      position: 'absolute', bottom: 16, left: 16, zIndex: 20,
      width: 300, borderRadius: 12, overflow: 'hidden',
      background: 'rgba(10,10,24,0.85)',
      border: '1px solid rgba(255,255,255,0.10)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      backdropFilter: 'blur(12px)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '7px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--ky-purple)' }} />
        <span style={{ fontSize: 10, fontWeight: 600, color: 'white', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Parameters</span>
        <span style={{ marginLeft: 'auto', fontSize: 9, color: 'rgba(255,255,255,0.35)' }}>
          {report.checks.filter(c => c.passed).length}/{report.checks.length} passed
        </span>
      </div>
      <div style={{ padding: '4px 0' }}>
        {report.checks.map(c => {
          const isSelected = selected === c.name
          const passColor = c.passed ? '#44ff88' : '#ff4444'
          return (
            <div
              key={c.name}
              onClick={() => onSelect(isSelected ? null : c.name)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '6px 12px',
                cursor: 'pointer',
                background: isSelected ? `${passColor}14` : 'transparent',
                borderLeft: isSelected ? `2px solid ${passColor}` : '2px solid transparent',
                transition: 'background 0.15s, border-color 0.15s',
              }}
            >
              <span style={{
                fontSize: 11, fontFamily: 'monospace',
                color: isSelected ? 'white' : 'rgba(255,255,255,0.7)',
                fontWeight: isSelected ? 600 : 400,
              }}>{c.name}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 600, color: c.passed ? '#4d9aff' : '#ff6060' }}>
                  {c.actual ?? '—'} mm
                </span>
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 100,
                  background: c.passed ? 'rgba(68,255,136,0.12)' : 'rgba(255,68,68,0.12)',
                  color: passColor,
                }}>
                  {c.passed ? '✓' : '✕'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      <div style={{
        padding: '5px 12px', fontSize: 9, color: 'rgba(255,255,255,0.25)',
        borderTop: '1px solid rgba(255,255,255,0.06)', textAlign: 'center',
      }}>
        {selected ? 'click again to hide arrow' : 'click a parameter to show dimension arrow'}
      </div>
    </div>
  )
}

// ── ViewBar ───────────────────────────────────────────────────────────────────

function ViewBar({ view, onViewChange, onClose }: { view: ViewPreset; onViewChange: (v: ViewPreset) => void; onClose: () => void }) {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, zIndex: 20,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '10px 16px',
      background: 'rgba(10,10,24,0.75)',
      borderBottom: '1px solid rgba(255,255,255,0.07)',
      backdropFilter: 'blur(12px)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--ky-purple)' }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'white', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Output · Parametric 3D
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        {VIEW_PRESETS.map(p => (
          <button key={p.id} onClick={() => onViewChange(p.id)} style={{
            padding: '4px 10px', fontSize: 11, borderRadius: 6, border: 'none',
            background: view === p.id ? 'var(--ky-purple)' : 'transparent',
            color: view === p.id ? 'white' : 'rgba(255,255,255,0.45)',
            cursor: 'pointer',
          }}>
            {p.label}
          </button>
        ))}
        <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.12)', margin: '0 6px' }} />
        <button onClick={onClose} style={{
          padding: '4px 12px', fontSize: 11, borderRadius: 6, border: '1px solid rgba(255,255,255,0.15)',
          background: 'rgba(255,255,255,0.06)', color: 'white', cursor: 'pointer',
        }}>
          ✕ Close
        </button>
      </div>
    </div>
  )
}

// ── ModelViewer3D ─────────────────────────────────────────────────────────────

interface ModelViewer3DProps {
  stlUrl: string
  view: ViewPreset
  onViewChange: (v: ViewPreset) => void
  loading?: boolean
  drawingUrl?: string
  report?: ValidationReport
}

export function ModelViewer3D({ stlUrl, view, onViewChange, loading, drawingUrl, report }: ModelViewer3DProps) {
  const [fullscreen, setFullscreen] = useState(false)
  const [activeCheck, setActiveCheck] = useState<string | null>(null)

  const activeCheckObj = report?.checks.find(c => c.name === activeCheck) ?? null

  const canvas = (
    <Canvas camera={{ position: CAMERA_POSITIONS.iso, fov: 45 }} shadows gl={{ antialias: true }}>
      <Scene stlUrl={stlUrl} view={view} activeCheck={activeCheckObj} />
    </Canvas>
  )

  return (
    <>
      <Card className="flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ background: 'var(--ky-purple)' }} />
            <span className="text-xs font-semibold text-white uppercase tracking-widest">Output · Parametric 3D</span>
          </div>
          <div className="flex items-center gap-1">
            {VIEW_PRESETS.map(p => (
              <button
                key={p.id}
                onClick={() => onViewChange(p.id)}
                className={`px-2.5 py-1 text-xs rounded-md transition-all ${
                  view === p.id ? 'bg-[var(--ky-purple)] text-white' : 'text-[var(--text-muted)] hover:text-white'
                }`}
              >
                {p.label}
              </button>
            ))}
            <div style={{ width: 1, height: 14, background: 'rgba(255,255,255,0.12)', margin: '0 4px' }} />
            <button
              onClick={() => setFullscreen(true)}
              className="px-2.5 py-1 text-xs rounded-md text-[var(--text-muted)] hover:text-white transition-all"
              title="Fullscreen"
            >
              ⛶
            </button>
          </div>
        </div>
        <div className="flex-1 relative" style={{ minHeight: 300, background: '#0a0a18' }}>
          {loading && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 rounded-b-xl">
              <div className="flex flex-col items-center gap-3">
                <svg className="animate-spin h-8 w-8 text-[var(--ky-blue)]" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                <span className="text-sm text-[var(--text-secondary)]">Regenerating…</span>
              </div>
            </div>
          )}
          {canvas}
        </div>
      </Card>

      {fullscreen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 100, background: '#060610' }}>
          <ViewBar view={view} onViewChange={onViewChange} onClose={() => { setFullscreen(false); setActiveCheck(null) }} />
          {drawingUrl && <MiniDrawing src={drawingUrl} />}
          {report && (
            <MiniParams report={report} selected={activeCheck} onSelect={setActiveCheck} />
          )}
          <div style={{ position: 'absolute', inset: 0, paddingTop: 49 }}>
            {canvas}
          </div>
        </div>
      )}
    </>
  )
}

export type { ViewPreset }
