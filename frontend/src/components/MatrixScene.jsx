import React, { useRef, useEffect, useMemo, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useWasm } from '../hooks/useWasm'

const BRANE_COLOR = new THREE.Color(0x00e5ff)
const CONNECTION_COLOR_LOW = new THREE.Color(0x002244)
const CONNECTION_COLOR_HIGH = new THREE.Color(0xff6600)
const MATRIX_N = 16 // NxN matrices — keep manageable in WASM

export default function MatrixScene({ coupling, mass, poke, onStats }) {
  const { wasm, loading } = useWasm()
  const simRef = useRef(null)
  const pokeRef = useRef(poke)
  const frameCount = useRef(0)

  const [branePositions, setBranePositions] = useState([])
  const [connections, setConnections] = useState([])

  useEffect(() => {
    if (!wasm || loading) return
    simRef.current = new wasm.MatrixSimulation(MATRIX_N, coupling, mass)
    return () => {
      if (simRef.current) { simRef.current.free(); simRef.current = null }
    }
  }, [wasm, loading])

  useEffect(() => {
    if (simRef.current) simRef.current.set_coupling(coupling)
  }, [coupling])

  useEffect(() => {
    if (simRef.current) simRef.current.set_mass(mass)
  }, [mass])

  // Handle poke
  useEffect(() => {
    if (poke > pokeRef.current && simRef.current) {
      simRef.current.poke(3.0)
    }
    pokeRef.current = poke
  }, [poke])

  useFrame((_, delta) => {
    if (!simRef.current) return
    const dt = Math.min(delta, 0.033)

    for (let i = 0; i < 4; i++) {
      simRef.current.step(dt / 4)
    }

    const eigs = simRef.current.get_eigenvalues()
    const conns = simRef.current.get_connections()

    const newBranes = []
    for (let i = 0; i < MATRIX_N; i++) {
      newBranes.push([eigs[i * 3] * 2, eigs[i * 3 + 1] * 2, eigs[i * 3 + 2] * 2])
    }

    // Parse connections: [a, b, strength, ...]
    const newConns = []
    const threshold = 0.1
    for (let i = 0; i < conns.length; i += 3) {
      const a = Math.round(conns[i])
      const b = Math.round(conns[i + 1])
      const s = conns[i + 2]
      if (s > threshold && a < newBranes.length && b < newBranes.length) {
        newConns.push({ a, b, strength: s })
      }
    }

    frameCount.current++
    if (frameCount.current % 3 === 0) {
      onStats?.({
        energy: simRef.current.get_energy().toFixed(2),
        loops: MATRIX_N,
      })
    }

    setBranePositions(newBranes)
    setConnections(newConns)
  })

  const maxStrength = useMemo(
    () => connections.reduce((m, c) => Math.max(m, c.strength), 0.001),
    [connections]
  )

  if (loading) return null

  return (
    <group>
      {/* D0-Branes as glowing spheres */}
      {branePositions.map((pos, i) => {
        const distFromCenter = Math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2)
        const scale = 0.08 + distFromCenter * 0.02
        return (
          <mesh key={i} position={pos}>
            <sphereGeometry args={[scale, 8, 8]} />
            <meshStandardMaterial
              color={BRANE_COLOR}
              emissive={BRANE_COLOR}
              emissiveIntensity={1.2}
              roughness={0}
              metalness={1}
            />
          </mesh>
        )
      })}

      {/* Connection lines between branes */}
      {connections.map(({ a, b, strength }, i) => {
        if (a >= branePositions.length || b >= branePositions.length) return null
        const posA = branePositions[a]
        const posB = branePositions[b]
        const t = Math.min(strength / maxStrength, 1.0)

        const color = CONNECTION_COLOR_LOW.clone().lerp(CONNECTION_COLOR_HIGH, t)
        const opacity = 0.2 + t * 0.8

        return (
          <ConnectionLine key={i} start={posA} end={posB} color={color} opacity={opacity} />
        )
      })}

      {/* Center of mass indicator */}
      <mesh>
        <sphereGeometry args={[0.05, 8, 8]} />
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={2} />
      </mesh>
    </group>
  )
}

function ConnectionLine({ start, end, color, opacity }) {
  const points = useMemo(() => [
    new THREE.Vector3(...start),
    new THREE.Vector3(...end),
  ], [start, end])

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints(points)
    return geo
  }, [points])

  return (
    <line geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={opacity} />
    </line>
  )
}
