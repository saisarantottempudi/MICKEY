import { useEffect, useRef, useState, useCallback } from 'react'
import { io } from 'socket.io-client'

export function useSocket() {
  const socketRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [streaming, setStreaming] = useState('')
  const [isThinking, setIsThinking] = useState(false)

  useEffect(() => {
    const socket = io('http://localhost:5050', { transports: ['websocket', 'polling'] })
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
