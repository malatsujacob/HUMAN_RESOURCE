import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function getPerformanceReviews() {
  const { data } = await api.get('/performance/')
  return data
}

export async function submitPerformanceReview(review) {
  const { data } = await api.post('/performance/', review)
  return data
}

export async function getDisciplinaryCases() {
  const { data } = await api.get('/disciplinary/')
  return data
}

export async function createDisciplinaryCase(caseDetails) {
  const { data } = await api.post('/disciplinary/', caseDetails)
  return data
}

export async function getEmployeeExits() {
  const { data } = await api.get('/exit/')
  return data
}

export async function initiateEmployeeExit(exitDetails) {
  const { data } = await api.post('/exit/', exitDetails)
  return data
}

export async function getAnalytics() {
  const { data } = await api.get('/analytics')
  return data
}

export function getModuleError(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean).join('; ')
    if (messages) return messages
  }
  return detail || error.message || 'Unable to load module data.'
}
