import { useState } from 'react'
import { setAuthToken } from '../utils/api'

export default function TokenGate({ onTokenSet }) {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!token.trim()) {
      setError('Enter a token')
      return
    }
    setAuthToken(token.trim())
    onTokenSet()
  }

  return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#0a0a0f', flexDirection: 'column', gap: 24,
    }}>
      <div style={{
        fontFamily: "'Orbitron', sans-serif", fontSize: 32, letterSpacing: 8,
        color: '#00f0ff', textShadow: '0 0 20px rgba(0, 240, 255, 0.5)',
      }}>
        MICKEY
      </div>
      <div style={{
        color: '#8888aa', fontSize: 14, fontFamily: "'Rajdhani', sans-serif",
      }}>
        Remote access — enter auth token
      </div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Paste auth token..."
          style={{
            background: 'rgba(10, 10, 20, 0.85)',
            border: '1px solid rgba(0, 240, 255, 0.2)',
            borderRadius: 6, padding: '10px 16px', color: '#e0e0e0',
            fontFamily: "'Rajdhani', sans-serif", fontSize: 16, width: 300,
            outline: 'none',
          }}
          autoFocus
        />
        <button type="submit" style={{
          background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.3)',
          borderRadius: 6, padding: '10px 20px', color: '#00f0ff', cursor: 'pointer',
          fontFamily: "'Rajdhani', sans-serif", fontSize: 16, fontWeight: 600,
        }}>
          CONNECT
        </button>
      </form>
      {error && <div style={{ color: '#ff3366', fontSize: 14 }}>{error}</div>}
      <div style={{ color: '#555', fontSize: 12, maxWidth: 360, textAlign: 'center' }}>
        Find your token on the server: run <code style={{ color: '#00f0ff' }}>
        curl localhost:5050/api/token</code> or check the startup log.
      </div>
    </div>
  )
}
