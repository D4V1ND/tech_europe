'use client'
import { Suspense, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useLoader } from '@react-three/fiber'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import * as THREE from 'three'

function STLMesh({ url }: { url: string }) {
  const geometry = useLoader(STLLoader, url)
  const geo = useMemo(() => {
    const g = geometry.clone()
    g.center()
    return g
  }, [geometry])
  return (
    <mesh geometry={geo}>
      <meshStandardMaterial color="#c0c8e0" roughness={0.3} metalness={0.1} />
    </mesh>
  )
}

export default function MiniCanvas3D({ stlUrl }: { stlUrl: string }) {
  return (
    <Canvas camera={{ position: [60, 45, 60], fov: 45 }} gl={{ antialias: true }}>
      <ambientLight intensity={0.4} />
      <directionalLight position={[50, 80, 60]} intensity={1.2} />
      <directionalLight position={[-40, -50, -40]} intensity={0.35} />
      <Suspense fallback={null}>
        <STLMesh url={stlUrl} />
      </Suspense>
      <OrbitControls enableDamping dampingFactor={0.05} />
    </Canvas>
  )
}
