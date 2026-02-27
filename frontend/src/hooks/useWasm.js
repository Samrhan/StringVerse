import { useState, useEffect } from 'react'

let wasmModule = null
let wasmPromise = null

async function loadWasm() {
  if (wasmModule) return wasmModule
  if (wasmPromise) return wasmPromise

  wasmPromise = (async () => {
    try {
      // Import the wasm-pack generated module
      const wasm = await import('../wasm-pkg/stringverse_wasm.js')
      await wasm.default()
      wasmModule = wasm
      return wasm
    } catch (e) {
      console.error('Failed to load WASM module:', e)
      // Return a mock for development when wasm isn't built yet
      return createMockWasm()
    }
  })()

  return wasmPromise
}

export function useWasm() {
  const [wasm, setWasm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadWasm()
      .then(mod => {
        setWasm(mod)
        setLoading(false)
      })
      .catch(err => {
        setError(err)
        setLoading(false)
      })
  }, [])

  return { wasm, loading, error }
}

// Mock WASM for development/testing without building Rust
function createMockWasm() {
  class StringSimulation {
    constructor(coupling) {
      this.coupling = coupling
      this.t = 0
      this.n = 64
    }
    step(dt) { this.t += dt }
    set_coupling(c) { this.coupling = c }
    get_positions() {
      const n = this.n
      const out = [1, n, 0]
      for (let i = 0; i < n; i++) {
        const t = 2 * Math.PI * i / n + this.t * 0.5
        out.push(Math.cos(t) * 3 + Math.sin(t * 2) * 0.5)
        out.push(Math.sin(t) * 3 + Math.cos(t * 3) * 0.5)
        out.push(Math.sin(t * 0.5) * 1.5)
      }
      return out
    }
    get_velocities_mag() {
      const n = this.n
      const out = [1, n]
      for (let i = 0; i < n; i++) out.push(Math.random() * 0.3)
      return out
    }
    get_total_energy() { return 42.0 + Math.sin(this.t) }
    get_loop_count() { return 1 }
    free() {}
  }

  class MatrixSimulation {
    constructor(n, coupling, mass) {
      this.n = n; this.coupling = coupling; this.mass = mass; this.t = 0
    }
    step(dt) { this.t += dt }
    set_coupling(c) { this.coupling = c }
    set_mass(m) { this.mass = m }
    poke(s) {}
    get_eigenvalues() {
      const out = []
      for (let i = 0; i < this.n; i++) {
        const a = (i / this.n) * 2 * Math.PI
        out.push(Math.cos(a + this.t * 0.3) * 2)
        out.push(Math.sin(a + this.t * 0.3) * 2)
        out.push(Math.sin(a * 2 + this.t * 0.2) * 1)
      }
      return out
    }
    get_connections() {
      const out = []
      for (let i = 0; i < this.n; i++) {
        for (let j = i + 1; j < this.n; j++) {
          out.push(i, j, Math.random() * 0.5)
        }
      }
      return out
    }
    get_energy() { return 10.0 + Math.sin(this.t) * 2 }
    free() {}
  }

  class CalabiYauMesh {
    static generate(resolution, sliceZ, psi) {
      const res = resolution
      const stride = 8
      const count = (res + 1) * (res + 1)
      const arr = new Float32Array(count * stride)
      for (let iu = 0; iu <= res; iu++) {
        for (let iv = 0; iv <= res; iv++) {
          const u = iu / res * Math.PI * 2
          const v = iv / res * Math.PI * 2
          const idx = (iu * (res + 1) + iv) * stride
          arr[idx] = Math.cos(u) * Math.cos(v) * 2.5 + sliceZ * 0.3 * Math.sin(u)
          arr[idx + 1] = Math.sin(u) * Math.cos(v) * 2.5 + sliceZ * 0.3
          arr[idx + 2] = (Math.sin(v) + sliceZ * 0.5) * 2.5 * psi * 0.3
          arr[idx + 3] = Math.cos(u); arr[idx + 4] = Math.sin(u); arr[idx + 5] = 0.5
          arr[idx + 6] = iu / res; arr[idx + 7] = iv / res
        }
      }
      return arr
    }
    static generate_indices(resolution) {
      const res = resolution
      const idxArr = new Uint32Array(res * res * 6)
      let k = 0
      for (let iu = 0; iu < res; iu++) {
        for (let iv = 0; iv < res; iv++) {
          const a = iu * (res + 1) + iv
          idxArr[k++] = a; idxArr[k++] = a + 1; idxArr[k++] = a + (res + 1)
          idxArr[k++] = a + 1; idxArr[k++] = a + (res + 2); idxArr[k++] = a + (res + 1)
        }
      }
      return idxArr
    }
    static psi_from_time(t) { return Math.sin(t * 0.3) * 0.8 + 1.0 }
  }

  return { StringSimulation, MatrixSimulation, CalabiYauMesh }
}
