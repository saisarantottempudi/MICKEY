import { useState } from 'react'
import { motion } from 'framer-motion'

export default function InputBar({ onSend, onVoiceStart, onVoiceStop, isRecording, disabled }) {
  const [text, setText] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  return (
    <div className="input-bar" style={{
      display: 'flex', gap: 10, padding: '12px 20px',
      borderTop: '1px solid var(--border)',
      alignItems: 'center',
    }}>
      <motion.button
        whileTap={{ scale: 0.9 }}
        onMouseDown={onVoiceStart}
        onMouseUp={onVoiceStop}
        onTouchStart={onVoiceStart}
        onTouchEnd={onVoiceStop}
        style={{
          width: 48, height: 48, borderRadius: '50%',
          border: `2px solid ${isRecording ? 'var(--accent)' : 'var(--primary)'}`,
          background: isRecording ? 'rgba(255, 51, 102, 0.2)' : 'rgba(0, 240, 255, 0.1)',
          color: isRecording ? 'var(--accent)' : 'var(--primary)',
          cursor: 'pointer', fontSize: 20,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isRecording ? '⏹' : '🎙'}
      </motion.button>

      <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex', gap: 10 }}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Talk to MICKEY..."
          disabled={disabled}
          style={{
            flex: 1, padding: '10px 16px', borderRadius: 8,
            border: '1px solid var(--border)',
            background: 'rgba(10, 10, 20, 0.6)',
            color: 'var(--text)', fontSize: 14,
            fontFamily: "'Rajdhani', sans-serif",
            outline: 'none',
          }}
          onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
          onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
        />
        <motion.button
          whileTap={{ scale: 0.95 }}
          type="submit"
          disabled={disabled || !text.trim()}
          style={{
            padding: '10px 24px', borderRadius: 8,
            border: '1px solid var(--primary)',
            background: 'rgba(0, 240, 255, 0.1)',
            color: 'var(--primary)',
            fontFamily: "'Orbitron', sans-serif",
            fontSize: 11, letterSpacing: 2,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled || !text.trim() ? 0.4 : 1,
          }}
        >
          SEND
        </motion.button>
      </form>
    </div>
  )
}
