import { motion } from 'framer-motion'

const cornerStyle = {
  position: 'absolute',
  width: 30,
  height: 30,
  borderColor: 'var(--primary)',
  opacity: 0.4,
}

export default function HUDFrame() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.5 }}
      style={{ position: 'fixed', inset: 8, pointerEvents: 'none', zIndex: 0 }}
    >
      <div style={{ ...cornerStyle, top: 0, left: 0, borderTop: '2px solid', borderLeft: '2px solid' }} />
      <div style={{ ...cornerStyle, top: 0, right: 0, borderTop: '2px solid', borderRight: '2px solid' }} />
      <div style={{ ...cornerStyle, bottom: 0, left: 0, borderBottom: '2px solid', borderLeft: '2px solid' }} />
      <div style={{ ...cornerStyle, bottom: 0, right: 0, borderBottom: '2px solid', borderRight: '2px solid' }} />
      <div style={{
        position: 'absolute', top: 0, left: 40, right: 40, height: 1,
        background: 'linear-gradient(90deg, transparent, var(--primary-dim), transparent)',
      }} />
      <div style={{
        position: 'absolute', bottom: 0, left: 40, right: 40, height: 1,
        background: 'linear-gradient(90deg, transparent, var(--primary-dim), transparent)',
      }} />
    </motion.div>
  )
}
