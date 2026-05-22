// Auto-detect backend URL:
// - localhost dev: direct to Flask on 5050
// - Remote via nginx: same origin (nginx proxies /api/ to Flask)
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
const API_BASE = isLocal
  ? 'http://localhost:5050'
  : ''  // Same origin — nginx proxies /api/ to Flask

// Auth token — set via localStorage for remote access
function getHeaders(extra = {}) {
  const headers = { ...extra }
  const token = localStorage.getItem('mickey_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export function setAuthToken(token) {
  localStorage.setItem('mickey_token', token)
}

export function getAuthToken() {
  return localStorage.getItem('mickey_token')
}

export async function sendMessage(message) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ message }),
  })
  if (res.status === 401) throw new Error('Unauthorized — set auth token')
  return res.json()
}

export async function sendVoice(audioBlob) {
  const form = new FormData()
  form.append('audio', audioBlob, 'recording.wav')
  const res = await fetch(`${API_BASE}/api/voice`, {
    method: 'POST',
    headers: getHeaders(),
    body: form,
  })
  if (res.status === 401) throw new Error('Unauthorized — set auth token')
  return res.blob()
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/api/health`, {
    headers: getHeaders(),
  })
  return res.json()
}

export { API_BASE }
