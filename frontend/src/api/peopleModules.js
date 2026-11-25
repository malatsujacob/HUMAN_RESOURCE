import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('token') || window.localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function getPerformanceReviews() {
  const { data } = await api.get('/performance/')
  return data
}

export async function getQuarterlyPerformanceRanking(quarter) {
  const { data } = await api.get('/performance/quarterly-ranking', { params: { quarter } })
  return data
}

export async function submitPerformanceReview(review) {
  const { data } = await api.post('/performance/self', review)
  return data
}

export async function getDisciplinaryCases() {
  const { data } = await api.get('/disciplinary/')
  return data
}

export async function getEmployees() {
  const { data } = await api.get('/employees/')
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


// ---- Enhanced Disciplinary API (Step 4) ----

export async function getDisciplinaryAnalytics() {
  const { data } = await api.get('/disciplinary/analytics')
  return data
}

export async function getDisciplinaryCaseDetail(caseId) {
  const { data } = await api.get(`/disciplinary/${caseId}`)
  return data
}

export async function addDisciplinaryEvidence(caseId, payload) {
  const { data } = await api.post(`/disciplinary/${caseId}/evidence`, payload)
  return data
}

export async function listDisciplinaryEvidence(caseId) {
  const { data } = await api.get(`/disciplinary/${caseId}/evidence`)
  return data
}

export async function deleteDisciplinaryEvidence(evidenceId) {
  const { data } = await api.delete(`/disciplinary/evidence/${evidenceId}`)
  return data
}

export async function recordDisciplinaryOutcome(caseId, payload) {
  const { data } = await api.post(`/disciplinary/${caseId}/outcome`, payload)
  return data
}

export async function resolveDisciplinaryCase(caseId, payload) {
  const { data } = await api.put(`/disciplinary/${caseId}/resolve`, payload)
  return data
}

export async function updateDisciplinaryAppeal(caseId, payload) {
  const { data } = await api.put(`/disciplinary/${caseId}/appeal`, payload)
  return data
}
