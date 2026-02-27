import React, { useRef, useEffect, useState, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useWasm } from '../hooks/useWasm'

const RESOLUTION = 60

export default function CalabiYauScene({ sliceZ, onStats }) {
  const { wasm, loading } = useWasm()
  const meshRef = useRef()
  const timeRef = useRef(0)
  const [geoData, setGeoData] = useState(null)

  // Generate mesh whenever sliceZ or psi changes
  const updateMesh = (wasm, t, sz) => {
    const psi = wasm.CalabiYauMesh.psi_from_time(t)
    const vertices = wasm.CalabiYauMesh.generate(RESOLUTION, sz, psi)
    const indices = wasm.CalabiYauMesh.generate_indices(RESOLUTION)
    setGeoData({ vertices, indices, psi })
    onStats?.({ energy: `ψ=${psi.toFixed(2)}`, loops: RESOLUTION * RESOLUTION * 2 })
  }

  useEffect(() => {
    if (!wasm || loading) return
    updateMesh(wasm, 0, sliceZ)
  }, [wasm, loading, sliceZ])

  useFrame((_, delta) => {
    if (!wasm || loading) return
    timeRef.current += delta * 0.4
    // Update mesh periodically (not every frame for performance)
    if (Math.round(timeRef.current * 10) % 5 === 0) {
      updateMesh(wasm, timeRef.current, sliceZ)
    }
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.1
      meshRef.current.rotation.x = Math.sin(timeRef.current * 0.2) * 0.2
    }
  })

  const geometry = useMemo(() => {
    if (!geoData) return null
    const { vertices, indices } = geoData
    const geo = new THREE.BufferGeometry()

    // vertices layout: x, y, z, nx, ny, nz, u, v (8 floats per vertex)
    const stride = 8
    const vertexCount = vertices.length / stride

    const positions = new Float32Array(vertexCount * 3)
    const normals = new Float32Array(vertexCount * 3)
    const uvs = new Float32Array(vertexCount * 2)

    for (let i = 0; i < vertexCount; i++) {
      positions[i * 3] = vertices[i * stride]
      positions[i * 3 + 1] = vertices[i * stride + 1]
      positions[i * 3 + 2] = vertices[i * stride + 2]
      normals[i * 3] = vertices[i * stride + 3]
      normals[i * 3 + 1] = vertices[i * stride + 4]
      normals[i * 3 + 2] = vertices[i * stride + 5]
      uvs[i * 2] = vertices[i * stride + 6]
      uvs[i * 2 + 1] = vertices[i * stride + 7]
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('normal', new THREE.BufferAttribute(normals, 3))
    geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2))
    geo.setIndex(new THREE.BufferAttribute(indices, 1))

    // Vertex colors based on curvature (normal z component)
    const colors = new Float32Array(vertexCount * 3)
    for (let i = 0; i < vertexCount; i++) {
      const nz = Math.abs(normals[i * 3 + 2])
      // Viridis-like gradient: dark blue → teal → yellow
      colors[i * 3] = nz * nz * 0.9
      colors[i * 3 + 1] = nz * 0.8
      colors[i * 3 + 2] = 0.5 + (1 - nz) * 0.5
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    return geo
  }, [geoData])

  if (loading || !geometry) return null

  return (
    <group>
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          vertexColors
          side={THREE.DoubleSide}
          roughness={0.2}
          metalness={0.7}
          wireframe={false}
          transparent
          opacity={0.85}
        />
      </mesh>
      {/* Wireframe overlay */}
      <mesh ref={undefined} geometry={geometry} rotation={meshRef.current?.rotation}>
        <meshBasicMaterial
          color="#334466"
          wireframe
          transparent
          opacity={0.15}
        />
      </mesh>
    </group>
  )
}
