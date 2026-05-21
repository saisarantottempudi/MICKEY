import { useState, useRef, useCallback } from 'react'
import { sendVoice } from '../utils/api'

export function useAudio() {
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const mediaRecorder = useRef(null)
  const chunks = useRef([])
  const analyserRef = useRef(null)
  const audioContextRef = useRef(null)

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContextRef.current = new AudioContext()
    const source = audioContextRef.current.createMediaStreamSource(stream)
    analyserRef.current = audioContextRef.current.createAnalyser()
    analyserRef.current.fftSize = 256
    source.connect(analyserRef.current)

    mediaRecorder.current = new MediaRecorder(stream)
    chunks.current = []
    mediaRecorder.current.ondataavailable = (e) => chunks.current.push(e.data)
    mediaRecorder.current.start()
    setIsRecording(true)
  }, [])

  const stopRecording = useCallback(async () => {
    return new Promise((resolve) => {
      mediaRecorder.current.onstop = async () => {
        const blob = new Blob(chunks.current, { type: 'audio/webm' })
        setIsRecording(false)
        mediaRecorder.current.stream.getTracks().forEach(t => t.stop())
        try {
          const audioBlob = await sendVoice(blob)
          playAudio(audioBlob)
          resolve(audioBlob)
        } catch {
          resolve(null)
        }
      }
      mediaRecorder.current.stop()
    })
  }, [])

  const playAudio = (blob) => {
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    setIsPlaying(true)
    audio.onended = () => {
      setIsPlaying(false)
      URL.revokeObjectURL(url)
    }
    audio.play()
  }

  return { isRecording, isPlaying, startRecording, stopRecording, analyser: analyserRef }
}
