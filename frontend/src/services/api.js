// Axios API client & WebSocket service

import axios from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-redirect on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ─── Auth ────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

// ─── Intelligence ─────────────────────────────────────
export const intelAPI = {
  getData: (params) => api.get('/intelligence/data', { params }),
  getMapData: () => api.get('/intelligence/map'),
  getStats: () => api.get('/intelligence/stats'),
}

// ─── Alerts ──────────────────────────────────────────
export const alertsAPI = {
  getAlerts: (params) => api.get('/alerts', { params }),
  getSummary: () => api.get('/alerts/summary'),
  acknowledge: (id) => api.patch(`/alerts/${id}/acknowledge`),
}

// ─── Uploads ─────────────────────────────────────────
export const uploadAPI = {
  uploadCSV: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/csv', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  uploadJSON: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/json', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  uploadImage: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/upload/image', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

// ─── AI ──────────────────────────────────────────────
export const aiAPI = {
  detectObjects: (dataId) => api.post(`/ai/cv/detect?data_id=${dataId}`),
  analyzeText: (text) => api.post('/ai/nlp/analyze', { text }),
  detectAnomalies: (features, feature_names) => api.post('/ai/anomaly', { features, feature_names }),
  cluster: (coordinates, algorithm = 'dbscan') => api.post('/ai/clustering', { coordinates, algorithm }),
  processRecord: (id) => api.post(`/ai/process/${id}`),
}

// ─── WebSocket ───────────────────────────────────────
export class IntelWebSocket {
  constructor(onMessage) {
    this.onMessage = onMessage
    this.ws = null
    this.reconnectDelay = 2000
    this.shouldReconnect = true
  }

  connect() {
    const token = localStorage.getItem('token')
    if (!token) return
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws')
      this.ws.onopen = () => console.log('[WS] Connected to Intel Feed')
      this.ws.onmessage = (e) => {
        try { this.onMessage(JSON.parse(e.data)) } catch {}
      }
      this.ws.onclose = () => {
        if (this.shouldReconnect) setTimeout(() => this.connect(), this.reconnectDelay)
      }
      this.ws.onerror = () => this.ws?.close()
    } catch {}
  }

  ping() { this.ws?.readyState === 1 && this.ws.send(JSON.stringify({ type: 'ping' })) }

  disconnect() {
    this.shouldReconnect = false
    this.ws?.close()
  }
}

export default api
