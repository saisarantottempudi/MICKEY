import { useRef, useEffect } from 'react'

export default function VoiceWaveform({ analyser, isActive }) {
  const canvasRef = useRef()

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    let animId

    const draw = () => {
      animId = requestAnimationFrame(draw)
      const w = canvas.width
      const h = canvas.height
      ctx.clearRect(0, 0, w, h)

      if (analyser?.current && isActive) {
        const bufLen = analyser.current.frequencyBinCount
        const data = new Uint8Array(bufLen)
        analyser.current.getByteFrequencyData(data)
        const barW = (w / bufLen) * 2.5
        const mid = h / 2
        for (let i = 0; i < bufLen; i++) {
          const val = data[i] / 255
          const barH = val * mid * 0.9
          const x = i * barW
          const gradient = ctx.createLinearGradient(x, mid - barH, x, mid + barH)
          gradient.addColorStop(0, 'rgba(0, 240, 255, 0.8)')
          gradient.addColorStop(0.5, 'rgba(0, 128, 255, 0.6)')
          gradient.addColorStop(1, 'rgba(0, 240, 255, 0.8)')
          ctx.fillStyle = gradient
          ctx.fillRect(x, mid - barH, barW - 1, barH * 2)
        }
      } else {
        const mid = h / 2
        const bars = 40
        const barW = w / bars
        for (let i = 0; i < bars; i++) {
          const val = Math.sin(Date.now() * 0.002 + i * 0.3) * 0.15 + 0.15
          const barH = val * mid
          ctx.fillStyle = 'rgba(0, 240, 255, 0.15)'
          ctx.fillRect(i * barW, mid - barH, barW - 2, barH * 2)
        }
      }
    }
    draw()
    return () => cancelAnimationFrame(animId)
  }, [analyser, isActive])

  return (
    <canvas
      ref={canvasRef}
      width={500}
      height={60}
      style={{ width: '100%', height: 60, display: 'block' }}
    />
  )
}
