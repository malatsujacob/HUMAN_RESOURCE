import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function requestLeave(leaveRequest) {
  const { data } = await api.post('/leave/request', leaveRequest)
  return data
}

export async function getPendingLeave() {
  const { data } = await api.get('/leave/pending')
  return data
}

export async function reviewLeave(leaveId, decision) {
  const { data } = await api.put(`/leave/${leaveId}/${decision}`)
  return data
}

export function getLeaveError(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean).join('; ')
    if (messages) return messages
  }
  return detail || error.message || 'Unable to load leave information.'
}
