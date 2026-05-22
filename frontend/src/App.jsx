import { useState, useCallback, useEffect } from 'react'
import './styles/global.css'
import HUDFrame from './components/HUDFrame'
import StatusBar from './components/StatusBar'
import ArcReactor from './components/ArcReactor'
import VoiceWaveform from './components/VoiceWaveform'
import ChatPanel from './components/ChatPanel'
import ResponsePanel from './components/ResponsePanel'
import InputBar from './components/InputBar'
import TokenGate from './components/TokenGate'
import { useSocket } from './hooks/useSocket'
import { useAudio } from './hooks/useAudio'
import { sendMessage, getAuthToken } from './utils/api'

export default function App() {
  const { connected, streaming, isThinking, setStreaming } = useSocket()
  const { isRecording, isPlaying, startRecording, stopRecording, analyser } = useAudio()
  const [messages, setMessages] = useState([])
  const [currentResponse, setCurrentResponse] = useState('')
  const [state, setState] = useState('idle')

  // Remote access: require token if not on localhost
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  const [hasToken, setHasToken] = useState(isLocal || !!getAuthToken())

  useEffect(() => {
    if (isRecording) setState('listening')
    else if (isThinking) setState('thinking')
    else if (isPlaying) setState('speaking')
    else if (!connected) setState('offline')
    else setState('idle')
  }, [isRecording, isThinking, isPlaying, connected])

  useEffect(() => {
    if (streaming) setCurrentResponse(streaming)
  }, [streaming])

  const handleSend = useCallback(async (text) => {
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setCurrentResponse('')
    setState('thinking')
    try {
      const result = await sendMessage(text)
      const reply = result.spoken || result.result
      setCurrentResponse(reply)
      setMessages(prev => [...prev, { role: 'assistant', content: reply }])
      setState('idle')
    } catch (e) {
      if (e.message.includes('Unauthorized')) {
        setCurrentResponse('Auth failed. Check your token.')
        setHasToken(false)
      } else {
        setCurrentResponse('Connection error. Is the backend running?')
      }
      setState('offline')
    }
  }, [])

  const handleVoiceStart = useCallback(() => {
    startRecording()
  }, [startRecording])

  const handleVoiceStop = useCallback(() => {
    stopRecording()
  }, [stopRecording])

  // Show token input if remote and no token
  if (!hasToken) {
    return <TokenGate onTokenSet={() => setHasToken(true)} />
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <HUDFrame />
      <StatusBar state={state} connected={connected} />

      <div className="main-grid" style={{
        flex: 1, display: 'grid',
        gridTemplateColumns: '1fr 1.2fr 1fr',
        gap: 12, padding: '12px 20px',
        overflow: 'hidden', position: 'relative', zIndex: 1,
      }}>
        <div className="chat-panel">
          <ChatPanel messages={messages} />
        </div>

        <div className="center-col" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="reactor-area" style={{ flex: 1, position: 'relative' }}>
            <ArcReactor isThinking={isThinking || state === 'thinking'} />
            <div className="mickey-title" style={{
              position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
              fontFamily: "'Orbitron', sans-serif", fontSize: 24, letterSpacing: 8,
              color: 'var(--primary)', textShadow: '0 0 20px rgba(0, 240, 255, 0.5)',
              textAlign: 'center', whiteSpace: 'nowrap',
            }}>
              MICKEY
            </div>
          </div>
          <div className="panel" style={{ padding: '8px 16px' }}>
            <VoiceWaveform analyser={analyser} isActive={isRecording} />
          </div>
        </div>

        <div className="response-panel">
          <ResponsePanel text={currentResponse} isThinking={state === 'thinking'} />
        </div>
      </div>

      <InputBar
        onSend={handleSend}
        onVoiceStart={handleVoiceStart}
        onVoiceStop={handleVoiceStop}
        isRecording={isRecording}
        disabled={state === 'thinking'}
      />
    </div>
  )
}
