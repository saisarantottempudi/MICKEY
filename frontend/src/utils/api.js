const API_BASE = 'http://localhost:5050'

export async function sendMessage(message) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  return res.json()
}

export async function sendVoice(audioBlob) {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.wav')
  const res = await fetch(`${API_BASE}/api/voice`, { method: 'POST', body: form })
  return res.blob()
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/health`)
  return res.json()
}
