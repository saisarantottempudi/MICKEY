import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getHealth } from '../utils/api'

const states = {
  idle: { label: 'IDLE', color: 'var(--primary)' },
  listening: { label: 'LISTENING', color: 'var(--success)' },
  thinking: { label: 'THINKING', color: 'var(--secondary)' },
  speaking: { label: 'SPEAKING', color: 'var(--accent)' },
  offline: { label: 'OFFLINE', color: '#ff4444' },
}

export default function StatusBar({ state = 'idle', connected }) {
  const [uptime, setUptime] = useState(0)
  const [health, setHealth] = useState(null)
  const s = states[state] || states.idle

  useEffect(() => {
    const timer = setInterval(() => setUptime(t => t + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null))
    const interval = setInterval(() => {
      getHealth().then(setHealth).catch(() => setHealth(null))
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  const fmt = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div className="status-bar" style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '8px 20px', borderBottom: '1px solid var(--border)',
      fontFamily: "'Orbitron', sans-serif", fontSize: 11, letterSpacing: 2,
      textTransform: 'uppercase',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <motion.div
          animate={{ opacity: [1, 0.4, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{ width: 6, height: 6, borderRadius: '50%', background: connected ? 'var(--success)' : '#ff4444' }}
        />
        <span style={{ color: 'var(--text-dim)' }}>MICKEY v0.1</span>
      </div>
      <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
        <span style={{ color: 'var(--text-dim)' }}>UPTIME {fmt(uptime)}</span>
        <span style={{ color: 'var(--text-dim)' }}>MODEL {health?.assistant || '...'}</span>
        <motion.span
          key={state}
          initial={{ scale: 1.2 }}
          animate={{ scale: 1 }}
          style={{ color: s.color, fontWeight: 700 }}
        >
          {s.label}
        </motion.span>
      </div>
    </div>
  )
}
