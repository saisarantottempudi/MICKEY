import { useEffect, useRef, useState, useCallback } from 'react'
import { io } from 'socket.io-client'
import { API_BASE } from '../utils/api'

export function useSocket() {
  const socketRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [streaming, setStreaming] = useState('')
  const [isThinking, setIsThinking] = useState(false)

  useEffect(() => {
    // Local: connect directly to Flask. Remote: nginx proxies /socket.io/
    const socketUrl = API_BASE || undefined  // undefined = same origin
    const socket = io(socketUrl, { transports: ['websocket', 'polling'] })
    socketRef.current = socket

    socket.on('connect', () => setConnected(true))
    socket.on('disconnect', () => setConnected(false))
    socket.on('token', (data) => {
      setStreaming(prev => prev + data.text)
    })
    socket.on('response_complete', () => {
      setIsThinking(false)
    })

    return () => socket.disconnect()
  }, [])

  const sendMessage = useCallback((message) => {
    setStreaming('')
    setIsThinking(true)
    socketRef.current?.emit('user_message', { message })
  }, [])

  return { connected, streaming, isThinking, sendMessage, setStreaming }
}
