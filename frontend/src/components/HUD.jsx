import React from 'react'
import { useIsMobile } from '../hooks/useIsMobile'

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
  const isMobile = useIsMobile()

  return (
    <>
      {/* Module title — top-right on desktop, top-center on mobile */}
      <div style={isMobile ? styles.moduleMobile : styles.moduleDesktop}>
        <div style={styles.moduleTitle}>{MODULE_LABELS[module]}</div>
        {!isMobile && (
          <div style={styles.moduleDesc}>{MODULE_DESCRIPTIONS[module]}</div>
        )}
      </div>

      {/* Stats — bottom-left on desktop, hidden on mobile (panel takes bottom) */}
      {!isMobile && (
        <div style={styles.stats}>
          <StatRow module={module} stats={stats} />
        </div>
      )}

      {/* On mobile show stats top-left, small */}
      {isMobile && (
        <div style={styles.statsMobile}>
          <StatRow module={module} stats={stats} />
        </div>
      )}
    </>
  )
}

function StatRow({ module, stats }) {
  if (module === 'string') return (
    <>
      <div>Loops <span style={styles.statVal}>{stats.loops}</span></div>
      <div>E <span style={styles.statVal}>{stats.energy}</span></div>
    </>
  )
  if (module === 'matrix') return (
    <>
      <div>Branes <span style={styles.statVal}>{stats.loops}</span></div>
      <div>E <span style={styles.statVal}>{stats.energy}</span></div>
    </>
  )
  return (
    <>
      <div>Tris <span style={styles.statVal}>{stats.loops}</span></div>
      <div style={{ color: '#88aacc' }}>{stats.energy}</div>
    </>
  )
}

const styles = {
  moduleDesktop: {
    position: 'absolute', top: 20, right: 20,
    maxWidth: 280, textAlign: 'right',
    fontFamily: "'Courier New', monospace", zIndex: 10,
  },
  moduleMobile: {
    position: 'absolute', top: 12, left: '50%',
    transform: 'translateX(-50%)',
    textAlign: 'center', whiteSpace: 'nowrap',
    fontFamily: "'Courier New', monospace", zIndex: 10,
  },
  moduleTitle: {
    fontSize: 12, color: '#00ccff', letterSpacing: 1,
    textShadow: '0 0 8px #0088aa', marginBottom: 4,
  },
  moduleDesc: {
    fontSize: 10, color: '#446688', lineHeight: 1.5,
  },
  stats: {
    position: 'absolute', bottom: 20, left: 20,
    fontFamily: "'Courier New', monospace", fontSize: 11,
    color: '#4477aa', lineHeight: 1.8, zIndex: 10,
  },
  statsMobile: {
    position: 'absolute', top: 36, left: 12,
    fontFamily: "'Courier New', monospace", fontSize: 10,
    color: '#4477aa', lineHeight: 1.6, zIndex: 10,
  },
  statVal: { color: '#00aaff', fontWeight: 'bold' },
}
