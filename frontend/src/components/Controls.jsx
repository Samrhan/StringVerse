import React, { useState } from 'react'
import { useIsMobile } from '../hooks/useIsMobile'

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
  const isMobile = useIsMobile()
  const [open, setOpen] = useState(true)

  if (isMobile) {
    return <MobileControls
      open={open} onToggle={() => setOpen(o => !o)}
      module={module} onModuleChange={onModuleChange}
      coupling={coupling} onCouplingChange={onCouplingChange}
      mass={mass} onMassChange={onMassChange}
      sliceZ={sliceZ} onSliceZChange={onSliceZChange}
      onPoke={onPoke}
    />
  }

  return (
    <div style={desktop.panel}>
      <div style={desktop.title}>StringVerse</div>
      <div style={desktop.subtitle}>String Theory Sandbox</div>

      <Section label="MODULE">
        <div style={desktop.buttonRow}>
          <ModuleBtn label="1. String"    id="string"  active={module} onClick={onModuleChange} styles={desktop} />
          <ModuleBtn label="2. Matrix"    id="matrix"  active={module} onClick={onModuleChange} styles={desktop} />
          <ModuleBtn label="3. Calabi-Yau" id="calabi" active={module} onClick={onModuleChange} styles={desktop} />
        </div>
      </Section>

      <SliderRow label="COUPLING / TENSION" value={coupling} min={0.1} max={5.0} step={0.05}
        onChange={onCouplingChange} styles={desktop} />

      {module === 'matrix' && (
        <SliderRow label="MASS / CONFINEMENT" value={mass} min={0.0} max={3.0} step={0.05}
          onChange={onMassChange} styles={desktop} />
      )}
      {module === 'calabi' && (
        <SliderRow label="EXTRA DIMENSION SLICE" value={sliceZ} min={-1.5} max={1.5} step={0.05}
          onChange={onSliceZChange} styles={desktop} />
      )}
      {module === 'matrix' && (
        <Section>
          <button style={desktop.pokeBtn} onClick={onPoke}>⚡ POKE (SPACE)</button>
        </Section>
      )}

      <div style={desktop.hints}>
        <div>Drag to orbit · Scroll to zoom</div>
        {module === 'matrix' && <div>SPACE to poke branes</div>}
      </div>
    </div>
  )
}

function MobileControls({ open, onToggle, module, onModuleChange, coupling, onCouplingChange,
  mass, onMassChange, sliceZ, onSliceZChange, onPoke }) {

  return (
    <div style={mobile.root}>
      {/* Collapsed bar always visible */}
      <div style={mobile.bar}>
        {/* Module tabs in the bar */}
        <div style={mobile.tabs}>
          {[['S', 'string'], ['M', 'matrix'], ['C', 'calabi']].map(([label, id]) => (
            <button key={id}
              style={{ ...mobile.tab, ...(module === id ? mobile.tabActive : {}) }}
              onClick={() => onModuleChange(id)}
            >{label}</button>
          ))}
        </div>

        {/* Poke button inline for matrix */}
        {module === 'matrix' && (
          <button style={mobile.pokeInline} onTouchStart={onPoke} onClick={onPoke}>⚡</button>
        )}

        {/* Expand/collapse */}
        <button style={mobile.toggle} onClick={onToggle}>{open ? '▼' : '▲'}</button>
      </div>

      {/* Expanded panel */}
      {open && (
        <div style={mobile.panel}>
          <SliderRow label="COUPLING / TENSION" value={coupling} min={0.1} max={5.0} step={0.05}
            onChange={onCouplingChange} styles={mobile} />
          {module === 'matrix' && (
            <SliderRow label="MASS / CONFINEMENT" value={mass} min={0.0} max={3.0} step={0.05}
              onChange={onMassChange} styles={mobile} />
          )}
          {module === 'calabi' && (
            <SliderRow label="EXTRA DIMENSION SLICE" value={sliceZ} min={-1.5} max={1.5} step={0.05}
              onChange={onSliceZChange} styles={mobile} />
          )}
          {module === 'matrix' && (
            <button style={mobile.pokeBtn} onTouchStart={onPoke} onClick={onPoke}>
              ⚡ POKE BRANES
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ── Shared sub-components ─────────────────────────────────────────────────────

function Section({ label, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <div style={{ color: '#6699bb', fontSize: 10, letterSpacing: 1,
        textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>}
      {children}
    </div>
  )
}

function ModuleBtn({ label, id, active, onClick, styles }) {
  return (
    <button
      style={{ ...styles.btn, ...(active === id ? styles.btnActive : {}) }}
      onClick={() => onClick(id)}
    >{label}</button>
  )
}

function SliderRow({ label, value, min, max, step, onChange, styles }) {
  return (
    <Section>
      <div style={{ display: 'flex', justifyContent: 'space-between',
        color: '#6699bb', fontSize: 10, letterSpacing: 1,
        textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
        <span style={{ color: '#00ccff', fontWeight: 'bold' }}>{value.toFixed(2)}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={styles.slider} />
    </Section>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const base = {
  slider: { width: '100%', accentColor: '#00aaff', cursor: 'pointer' },
  btn: {
    flex: 1, padding: '5px 4px',
    background: 'rgba(0,20,40,0.8)', border: '1px solid #1a3a5c',
    borderRadius: 4, color: '#4488aa', cursor: 'pointer',
    fontSize: 11, fontFamily: "'Courier New', monospace", transition: 'all 0.15s',
  },
  btnActive: {
    background: 'rgba(0,80,150,0.6)', border: '1px solid #0088cc',
    color: '#00eeff', boxShadow: '0 0 8px rgba(0,150,255,0.4)',
  },
  pokeBtn: {
    width: '100%', padding: '10px',
    background: 'rgba(60,20,0,0.8)', border: '1px solid #aa4400',
    borderRadius: 4, color: '#ff8822', cursor: 'pointer',
    fontSize: 13, fontFamily: "'Courier New', monospace",
    fontWeight: 'bold', letterSpacing: 1,
  },
}

const desktop = {
  ...base,
  panel: {
    position: 'absolute', top: 20, left: 20,
    background: 'rgba(0,8,20,0.85)', border: '1px solid #1a3a5c',
    borderRadius: 8, padding: '16px 20px', minWidth: 240,
    backdropFilter: 'blur(10px)', zIndex: 10,
    color: '#c0d8f0', fontFamily: "'Courier New', monospace", fontSize: 12,
  },
  title: { fontSize: 18, fontWeight: 'bold', color: '#00ccff', letterSpacing: 3,
    textShadow: '0 0 10px #00aaff' },
  subtitle: { fontSize: 10, color: '#4488aa', letterSpacing: 2, marginBottom: 14,
    textTransform: 'uppercase' },
  buttonRow: { display: 'flex', gap: 6 },
  hints: { marginTop: 10, padding: '8px 0 0', borderTop: '1px solid #0d2a40',
    color: '#335566', fontSize: 10, lineHeight: 1.6 },
}

const mobile = {
  ...base,
  root: {
    position: 'fixed', bottom: 0, left: 0, right: 0,
    zIndex: 20, fontFamily: "'Courier New', monospace",
  },
  bar: {
    display: 'flex', alignItems: 'center', gap: 8,
    background: 'rgba(0,8,20,0.95)', borderTop: '1px solid #1a3a5c',
    padding: '10px 16px',
  },
  tabs: { display: 'flex', gap: 8, flex: 1 },
  tab: {
    flex: 1, padding: '8px 4px',
    background: 'rgba(0,20,40,0.9)', border: '1px solid #1a3a5c',
    borderRadius: 6, color: '#4488aa', cursor: 'pointer',
    fontSize: 14, fontFamily: "'Courier New', monospace",
    fontWeight: 'bold', minHeight: 40,
  },
  tabActive: {
    background: 'rgba(0,80,150,0.7)', border: '1px solid #0088cc',
    color: '#00eeff', boxShadow: '0 0 10px rgba(0,150,255,0.4)',
  },
  pokeInline: {
    padding: '8px 14px', background: 'rgba(60,20,0,0.9)',
    border: '1px solid #aa4400', borderRadius: 6, color: '#ff8822',
    fontSize: 18, cursor: 'pointer', minHeight: 40,
  },
  toggle: {
    padding: '8px 12px', background: 'rgba(0,20,40,0.8)',
    border: '1px solid #1a3a5c', borderRadius: 6, color: '#4488aa',
    fontSize: 14, cursor: 'pointer', minHeight: 40,
  },
  panel: {
    background: 'rgba(0,8,20,0.97)', borderTop: '1px solid #1a3a5c',
    padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 4,
  },
  slider: { width: '100%', accentColor: '#00aaff', cursor: 'pointer', height: 6 },
  btn: { ...base.btn, padding: '9px 4px', fontSize: 12, minHeight: 40 },
  pokeBtn: {
    ...base.pokeBtn,
    padding: '12px', fontSize: 15, marginTop: 4,
    minHeight: 48, borderRadius: 6,
  },
}
