import React, { useState, useCallback, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import StringScene from './components/StringScene'
import MatrixScene from './components/MatrixScene'
import CalabiYauScene from './components/CalabiYauScene'
import Controls from './components/Controls'
import HUD from './components/HUD'
import './styles.css'

export default function App() {
  const [module, setModule] = useState('string') // 'string' | 'matrix' | 'calabi'
  const [coupling, setCoupling] = useState(1.0)
  const [mass, setMass] = useState(0.5)
  const [sliceZ, setSliceZ] = useState(0.0)
  const [poke, setPoke] = useState(0)
  const [stats, setStats] = useState({ energy: 0, loops: 0 })

  const handlePoke = useCallback(() => {
    setPoke(n => n + 1)
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      if (e.key === '1') setModule('string')
      if (e.key === '2') setModule('matrix')
      if (e.key === '3') setModule('calabi')
      if (e.key === ' ') { e.preventDefault(); handlePoke() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handlePoke])

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        camera={{ position: [0, 0, 12], fov: 60, near: 0.01, far: 1000 }}
        gl={{ antialias: true, alpha: false }}
        style={{ position: 'absolute', inset: 0 }}
      >
        <color attach="background" args={['#020408']} />
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#8ae" />
        <pointLight position={[-10, -5, -10]} intensity={0.8} color="#e8a" />
        <Stars radius={80} depth={50} count={3000} factor={4} fade />

        {module === 'string' && (
          <StringScene coupling={coupling} onStats={setStats} />
        )}
        {module === 'matrix' && (
          <MatrixScene coupling={coupling} mass={mass} poke={poke} onStats={setStats} />
        )}
        {module === 'calabi' && (
          <CalabiYauScene sliceZ={sliceZ} onStats={setStats} />
        )}

        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={2}
          maxDistance={50}
        />
      </Canvas>

      <HUD module={module} stats={stats} />

      <Controls
        module={module}
        onModuleChange={setModule}
        coupling={coupling}
        onCouplingChange={setCoupling}
        mass={mass}
        onMassChange={setMass}
        sliceZ={sliceZ}
        onSliceZChange={setSliceZ}
        onPoke={handlePoke}
      />
    </div>
  )
}
