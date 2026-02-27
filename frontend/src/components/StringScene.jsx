import React, { useRef, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useWasm } from '../hooks/useWasm'

// Colors for up to 8 string loops
const LOOP_COLORS = [
  new THREE.Color(0x00ffff),
  new THREE.Color(0xff6688),
  new THREE.Color(0x88ff44),
  new THREE.Color(0xffaa00),
  new THREE.Color(0xaa44ff),
  new THREE.Color(0xff4444),
  new THREE.Color(0x44ffaa),
  new THREE.Color(0xffff44),
]

const MAX_LOOPS = 8
const MAX_PTS = 512

function StringLoop({ geometry, color, tubeRadius = 0.04 }) {
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.6}
        roughness={0.2}
        metalness={0.5}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

export default function StringScene({ coupling, onStats }) {
  const { wasm, loading } = useWasm()
  const simRef = useRef(null)
  // Map from colorId → TubeGeometry, so we dispose only replaced ones
  const geoMapRef = useRef({})
  const [loops, setLoops] = useState([])
  const frameCount = useRef(0)

  // Initialize simulation
  useEffect(() => {
    if (!wasm || loading) return
    simRef.current = new wasm.StringSimulation(coupling)
    return () => {
      if (simRef.current) {
        simRef.current.free()
        simRef.current = null
      }
    }
  }, [wasm, loading])

  // Update coupling
  useEffect(() => {
    if (simRef.current) simRef.current.set_coupling(coupling)
  }, [coupling])

  useFrame((_, delta) => {
    if (!simRef.current) return
    const dt = Math.min(delta, 0.033)

    for (let i = 0; i < 3; i++) {
      simRef.current.step(dt / 3)
    }

    const data = simRef.current.get_positions()
    const velData = simRef.current.get_velocities_mag()

    const loopCount = Math.round(data[0])
    const newLoops = []
    let dataIdx = 1
    let velIdx = 1

    for (let li = 0; li < loopCount; li++) {
      const n = Math.round(data[dataIdx++])
      const colorId = Math.round(data[dataIdx++])
      velIdx++ // skip velocity n (same as n)

      const pts = []
      const speeds = []
      for (let i = 0; i < n; i++) {
        pts.push(new THREE.Vector3(data[dataIdx], data[dataIdx + 1], data[dataIdx + 2]))
        dataIdx += 3
        speeds.push(velData[velIdx++])
      }

      // Close the loop
      if (pts.length > 2) {
        pts.push(pts[0].clone())
        speeds.push(speeds[0])
      }

      newLoops.push({ pts, speeds, colorId: colorId % LOOP_COLORS.length, n })
    }

    // Build / update geometries, disposing ones no longer present
    const geoMap = geoMapRef.current
    const activeIds = new Set(newLoops.map(l => l.colorId))
    for (const id of Object.keys(geoMap)) {
      if (!activeIds.has(Number(id))) {
        geoMap[id]?.dispose()
        delete geoMap[id]
      }
    }

    for (const { pts, speeds, colorId } of newLoops) {
      if (pts.length < 3) continue
      const curve = new THREE.CatmullRomCurve3(pts, true)
      const tubePoints = 200
      const tubeGeo = new THREE.TubeGeometry(curve, tubePoints, 0.05, 8, true)

      // Color vertices by speed
      const count = tubeGeo.attributes.position.count
      const colors = new Float32Array(count * 3)
      const maxSpeed = Math.max(...speeds, 0.001)
      const vertsPerSegment = 9 // 8 sides + 1 repeated
      for (let i = 0; i < count; i++) {
        const seg = Math.floor(i / vertsPerSegment)
        const speedIdx = Math.min(Math.floor(seg / tubePoints * pts.length), speeds.length - 1)
        const t = Math.min(speeds[speedIdx] / maxSpeed, 1.0)
        const base = LOOP_COLORS[colorId]
        colors[i * 3]     = base.r + t * (1.0 - base.r)
        colors[i * 3 + 1] = base.g * (1.0 - t * 0.7)
        colors[i * 3 + 2] = base.b * (1.0 - t * 0.9)
      }
      tubeGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3))

      // Dispose previous geometry for this loop identity before replacing
      geoMap[colorId]?.dispose()
      geoMap[colorId] = tubeGeo
    }

    frameCount.current++
    if (frameCount.current % 3 === 0) {
      onStats?.({
        energy: simRef.current.get_total_energy().toFixed(2),
        loops: simRef.current.get_loop_count(),
      })
    }

    setLoops(newLoops)
  })

  if (loading) return null

  return (
    <group>
      {loops.map((loop) => {
        const geo = geoMapRef.current[loop.colorId]
        if (!geo) return null
        return (
          // key=colorId tracks loop identity across splits — stable across re-renders
          <mesh key={loop.colorId} geometry={geo}>
            <meshStandardMaterial
              vertexColors
              emissive={LOOP_COLORS[loop.colorId]}
              emissiveIntensity={0.4}
              roughness={0.15}
              metalness={0.6}
            />
          </mesh>
        )
      })}
    </group>
  )
}
