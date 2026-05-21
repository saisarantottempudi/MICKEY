import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ChatPanel({ messages }) {
  const endRef = useRef()

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="panel" style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      padding: 16, overflow: 'hidden',
    }}>
      <div style={{
        fontFamily: "'Orbitron', sans-serif", fontSize: 10, letterSpacing: 2,
        color: 'var(--text-dim)', marginBottom: 12, textTransform: 'uppercase',
      }}>
        Conversation Log
      </div>
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
                padding: '8px 12px',
                borderRadius: 8,
                fontSize: 14,
                lineHeight: 1.5,
                background: msg.role === 'user'
                  ? 'rgba(0, 128, 255, 0.15)'
                  : 'rgba(0, 240, 255, 0.08)',
                border: `1px solid ${msg.role === 'user' ? 'rgba(0, 128, 255, 0.3)' : 'var(--border)'}`,
              }}
            >
              <span style={{ fontSize: 9, color: 'var(--text-dim)', fontFamily: "'Orbitron'" }}>
                {msg.role === 'user' ? 'YOU' : 'MICKEY'}
              </span>
              <div style={{ marginTop: 4 }}>{msg.content}</div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={endRef} />
      </div>
    </div>
  )
}
