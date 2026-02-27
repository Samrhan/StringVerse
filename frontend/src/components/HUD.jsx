import React from 'react'

const MODULE_LABELS = {
  string: 'Nambu-Goto Relativistic String',
  matrix: 'BFSS Matrix Model (D0-Branes)',
  calabi: 'Calabi-Yau Quintic Manifold',
}

const MODULE_DESCRIPTIONS = {
  string: 'Closed strings evolve via the wave equation. Topology changes when strings self-intersect.',
  matrix: 'D0-branes emerge as eigenvalues of 3 non-commuting Hermitian matrices.',
  calabi: 'Interactive slice through the Fermat quintic: Σzᵢ⁵ = 0 in CP⁴.',
}

export default function HUD({ module, stats }) {
  return (
    <>
      {/* Top-right module info */}
      <div style={styles.moduleInfo}>
        <div style={styles.moduleTitle}>{MODULE_LABELS[module]}</div>
        <div style={styles.moduleDesc}>{MODULE_DESCRIPTIONS[module]}</div>
      </div>

      {/* Bottom-left stats */}
      <div style={styles.stats}>
        {module === 'string' && (
          <>
            <div>Loops: <span style={styles.statVal}>{stats.loops}</span></div>
            <div>Energy: <span style={styles.statVal}>{stats.energy}</span></div>
          </>
        )}
        {module === 'matrix' && (
          <>
            <div>D0-Branes: <span style={styles.statVal}>{stats.loops}</span></div>
            <div>Energy: <span style={styles.statVal}>{stats.energy}</span></div>
          </>
        )}
        {module === 'calabi' && (
          <>
            <div>Triangles: <span style={styles.statVal}>{stats.loops}</span></div>
            <div style={{ color: '#88aacc' }}>{stats.energy}</div>
          </>
        )}
      </div>
    </>
  )
}

const styles = {
  moduleInfo: {
    position: 'absolute',
    top: 20,
    right: 20,
    maxWidth: 280,
    textAlign: 'right',
    fontFamily: "'Courier New', monospace",
    zIndex: 10,
  },
  moduleTitle: {
    fontSize: 13,
    color: '#00ccff',
    letterSpacing: 1,
    textShadow: '0 0 8px #0088aa',
    marginBottom: 4,
  },
  moduleDesc: {
    fontSize: 10,
    color: '#446688',
    lineHeight: 1.5,
  },
  stats: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    fontFamily: "'Courier New', monospace",
    fontSize: 11,
    color: '#4477aa',
    lineHeight: 1.8,
    zIndex: 10,
  },
  statVal: {
    color: '#00aaff',
    fontWeight: 'bold',
  },
}
