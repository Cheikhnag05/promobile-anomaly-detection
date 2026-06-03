import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = {
  health: () => axios.get(`${BASE}/health`).then(r => r.data),
  stats: () => axios.get(`${BASE}/stats`).then(r => r.data),
  anomalies: (params = {}) => axios.get(`${BASE}/anomalies`, { params }).then(r => r.data),
  predict: (payload) => axios.post(`${BASE}/predict`, payload).then(r => r.data),
}
