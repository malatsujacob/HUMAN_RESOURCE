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


// ---- Exit Phase 2 API ----

export async function getExitDetail(exitId) {
  const { data } = await api.get(`/exit/${exitId}`)
  return data
}

export async function updateExitDetails(exitId, payload) {
  const { data } = await api.put(`/exit/${exitId}`, payload)
  return data
}

export async function upsertExitInterview(exitId, payload) {
  const { data } = await api.post(`/exit/${exitId}/interview`, payload)
  return data
}

export async function upsertExitFinalPay(exitId, payload) {
  const { data } = await api.post(`/exit/${exitId}/final-pay`, payload)
  return data
}

export async function revokeExitAccess(exitId) {
  const { data } = await api.post(`/exit/${exitId}/revoke-access`)
  return data
}

export async function deleteExitInterview(exitId) {
  const { data } = await api.delete(`/exit/${exitId}/interview`)
  return data
}

export async function deleteExitFinalPay(exitId) {
  const { data } = await api.delete(`/exit/${exitId}/final-pay`)
  return data
}

export async function checkExitComplete(exitId) {
  const { data } = await api.get(`/exit/${exitId}/complete-check`)
  return data
}

export async function getExitClearanceItems(exitId) {
  const { data } = await api.get(`/exit/${exitId}/clearance-items`)
  return data
}

export async function updateExitClearanceItem(itemId, payload) {
  const { data } = await api.put(`/exit/clearance-items/${itemId}`, payload)
  return data
}

export async function getExitClearanceProgress(exitId) {
  const { data } = await api.get(`/exit/${exitId}/clearance-progress`)
  return data
}

export async function deleteExitClearanceItem(itemId) {
  const { data } = await api.delete(`/exit/clearance-items/${itemId}`)
  return data
}
