import React from 'react'

export default function Controls({
  module,
  onModuleChange,
  coupling,
  onCouplingChange,
  mass,
  onMassChange,
  sliceZ,
  onSliceZChange,
  onPoke,
}) {
  return (
    <div style={styles.panel}>
      <div style={styles.title}>StringVerse</div>
      <div style={styles.subtitle}>String Theory Sandbox</div>

      {/* Module selector */}
      <div style={styles.section}>
        <div style={styles.label}>MODULE</div>
        <div style={styles.buttonRow}>
          <button
            style={{ ...styles.btn, ...(module === 'string' ? styles.btnActive : {}) }}
            onClick={() => onModuleChange('string')}
          >1. String</button>
          <button
            style={{ ...styles.btn, ...(module === 'matrix' ? styles.btnActive : {}) }}
            onClick={() => onModuleChange('matrix')}
          >2. Matrix</button>
          <button
            style={{ ...styles.btn, ...(module === 'calabi' ? styles.btnActive : {}) }}
            onClick={() => onModuleChange('calabi')}
          >3. Calabi-Yau</button>
        </div>
      </div>

      {/* Coupling slider */}
      <div style={styles.section}>
        <div style={styles.label}>
          COUPLING / TENSION
          <span style={styles.value}>{coupling.toFixed(2)}</span>
        </div>
        <input
          type="range" min="0.1" max="5.0" step="0.05"
          value={coupling}
          onChange={e => onCouplingChange(parseFloat(e.target.value))}
          style={styles.slider}
        />
      </div>

      {/* Mass slider (matrix only) */}
      {module === 'matrix' && (
        <div style={styles.section}>
          <div style={styles.label}>
            MASS / CONFINEMENT
            <span style={styles.value}>{mass.toFixed(2)}</span>
          </div>
          <input
            type="range" min="0.0" max="3.0" step="0.05"
            value={mass}
            onChange={e => onMassChange(parseFloat(e.target.value))}
            style={styles.slider}
          />
        </div>
      )}

      {/* Slice Z (Calabi-Yau only) */}
      {module === 'calabi' && (
        <div style={styles.section}>
          <div style={styles.label}>
            EXTRA DIMENSION SLICE
            <span style={styles.value}>{sliceZ.toFixed(2)}</span>
          </div>
          <input
            type="range" min="-1.5" max="1.5" step="0.05"
            value={sliceZ}
            onChange={e => onSliceZChange(parseFloat(e.target.value))}
            style={styles.slider}
          />
        </div>
      )}

      {/* Poke button (matrix only) */}
      {module === 'matrix' && (
        <div style={styles.section}>
          <button style={styles.pokeBtn} onClick={onPoke}>
            ⚡ POKE (SPACE)
          </button>
        </div>
      )}

      {/* Key hints */}
      <div style={styles.hints}>
        <div>Drag to orbit · Scroll to zoom</div>
        {module === 'matrix' && <div>SPACE to poke branes</div>}
      </div>
    </div>
  )
}

// Keyboard shortcut handler — wire to App
export function useKeyboardShortcuts({ onModuleChange, onPoke }) {
  React.useEffect(() => {
    const handler = (e) => {
      if (e.key === '1') onModuleChange('string')
      if (e.key === '2') onModuleChange('matrix')
      if (e.key === '3') onModuleChange('calabi')
      if (e.key === ' ') { e.preventDefault(); onPoke?.() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onModuleChange, onPoke])
}

const styles = {
  panel: {
    position: 'absolute',
    top: 20,
    left: 20,
    background: 'rgba(0, 8, 20, 0.85)',
    border: '1px solid #1a3a5c',
    borderRadius: 8,
    padding: '16px 20px',
    minWidth: 240,
    backdropFilter: 'blur(10px)',
    zIndex: 10,
    color: '#c0d8f0',
    fontFamily: "'Courier New', monospace",
    fontSize: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00ccff',
    letterSpacing: 3,
    textShadow: '0 0 10px #00aaff',
  },
  subtitle: {
    fontSize: 10,
    color: '#4488aa',
    letterSpacing: 2,
    marginBottom: 14,
    textTransform: 'uppercase',
  },
  section: {
    marginBottom: 14,
  },
  label: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: 6,
    color: '#6699bb',
    letterSpacing: 1,
    fontSize: 10,
    textTransform: 'uppercase',
  },
  value: {
    color: '#00ccff',
    fontWeight: 'bold',
  },
  slider: {
    width: '100%',
    accentColor: '#00aaff',
    cursor: 'pointer',
  },
  buttonRow: {
    display: 'flex',
    gap: 6,
  },
  btn: {
    flex: 1,
    padding: '5px 4px',
    background: 'rgba(0,20,40,0.8)',
    border: '1px solid #1a3a5c',
    borderRadius: 4,
    color: '#4488aa',
    cursor: 'pointer',
    fontSize: 11,
    fontFamily: "'Courier New', monospace",
    transition: 'all 0.15s',
  },
  btnActive: {
    background: 'rgba(0,80,150,0.6)',
    border: '1px solid #0088cc',
    color: '#00eeff',
    boxShadow: '0 0 8px rgba(0,150,255,0.4)',
  },
  pokeBtn: {
    width: '100%',
    padding: '8px',
    background: 'rgba(60,20,0,0.8)',
    border: '1px solid #aa4400',
    borderRadius: 4,
    color: '#ff8822',
    cursor: 'pointer',
    fontSize: 12,
    fontFamily: "'Courier New', monospace",
    fontWeight: 'bold',
    letterSpacing: 1,
    transition: 'all 0.1s',
  },
  hints: {
    marginTop: 10,
    padding: '8px 0 0',
    borderTop: '1px solid #0d2a40',
    color: '#335566',
    fontSize: 10,
    lineHeight: 1.6,
  },
}
