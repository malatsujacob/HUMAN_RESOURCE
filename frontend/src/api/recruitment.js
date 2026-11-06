import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function getActiveRequisitions() {
  const { data } = await api.get('/recruitment/requisitions/active')
  return data
}

export async function getRequisitions() {
  const { data } = await api.get('/recruitment/requisitions')
  return data
}

export async function getPipelineCandidates() {
  const { data } = await api.get('/recruitment/candidates')
  return data
}

export async function submitApplication(formData) {
  const { data } = await api.post('/recruitment/apply', formData)
  return data
}

export async function updateCandidateStatus(candidateId, status) {
  const { data } = await api.patch(
    `/recruitment/candidates/${candidateId}/status`,
    { status },
  )
  return data
}

export async function downloadCandidateCv(candidateId) {
  const { data } = await api.get(
    `/recruitment/candidates/${candidateId}/cv`,
    { responseType: 'blob' },
  )
  const url = window.URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = 'candidate-cv.pdf'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => window.URL.revokeObjectURL(url), 30000)
}

export function getRecruitmentError(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean).join('; ')
    if (messages) return messages
  }
  return detail || error.message || 'Something went wrong.'
}
