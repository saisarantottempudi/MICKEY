import { motion } from 'framer-motion'

export default function ResponsePanel({ text, isThinking }) {
  return (
    <div className="panel" style={{
      flex: 1, padding: 16, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{
        fontFamily: "'Orbitron', sans-serif", fontSize: 10, letterSpacing: 2,
        color: 'var(--text-dim)', marginBottom: 12, textTransform: 'uppercase',
      }}>
        Response
      </div>
      <div style={{ flex: 1, overflowY: 'auto', fontSize: 15, lineHeight: 1.7 }}>
        {isThinking && !text && (
          <motion.div
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{ color: 'var(--primary)', fontFamily: "'Orbitron'", fontSize: 12 }}
          >
            Processing...
          </motion.div>
        )}
        {text && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {text}
          </motion.div>
        )}
        {!isThinking && !text && (
          <div style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: 13 }}>
            Awaiting input...
          </div>
        )}
      </div>
    </div>
  )
}
