import axios from 'axios'

const API_URL = process.env.API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    const response = await apiClient.post('/api/v1/auth/token', formData)
    return response.data
  },

  // Dashboard
  getDashboardStats: async () => {
    const response = await apiClient.get('/api/v1/analytics/dashboard')
    return response.data
  },

  // Alerts
  getAlerts: async (params?: { severity?: string; status?: string }) => {
    const response = await apiClient.get('/api/v1/alerts', { params })
    return response.data
  },

  getAlert: async (id: string) => {
    const response = await apiClient.get(`/api/v1/alerts/${id}`)
    return response.data
  },

  acknowledgeAlert: async (id: string) => {
    const response = await apiClient.patch(`/api/v1/alerts/${id}`, { acknowledged: true })
    return response.data
  },

  resolveAlert: async (id: string) => {
    const response = await apiClient.patch(`/api/v1/alerts/${id}`, { resolved: true })
    return response.data
  },

  // Threats
  getThreats: async (params?: { threat_type?: string }) => {
    const response = await apiClient.get('/api/v1/threats', { params })
    return response.data
  },

  analyzeThreat: async (logData: object) => {
    const response = await apiClient.post('/api/v1/threats/analyze', { log_data: logData })
    return response.data
  },

  // Analytics
  getTimeline: async (days: number = 7) => {
    const response = await apiClient.get('/api/v1/analytics/timeline', { params: { days } })
    return response.data
  },

  getRiskAssessment: async () => {
    const response = await apiClient.get('/api/v1/analytics/risk-assessment')
    return response.data
  },

  // Users
  getUsers: async (params?: { role?: string; is_active?: boolean; search?: string }) => {
    const response = await apiClient.get('/api/v1/users', { params })
    return response.data
  },

  getUser: async (id: number) => {
    const response = await apiClient.get(`/api/v1/users/${id}`)
    return response.data
  },

  getUserStats: async () => {
    const response = await apiClient.get('/api/v1/users/stats')
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/api/v1/users/me')
    return response.data
  },

  createUser: async (userData: { username: string; email: string; password: string; full_name?: string; role?: string }) => {
    const response = await apiClient.post('/api/v1/users', userData)
    return response.data
  },

  updateUser: async (id: number, userData: { username?: string; email?: string; full_name?: string; role?: string; is_active?: boolean }) => {
    const response = await apiClient.put(`/api/v1/users/${id}`, userData)
    return response.data
  },

  deleteUser: async (id: number) => {
    const response = await apiClient.delete(`/api/v1/users/${id}`)
    return response.data
  },

  deactivateUser: async (id: number) => {
    const response = await apiClient.post(`/api/v1/users/${id}/deactivate`)
    return response.data
  },

  activateUser: async (id: number) => {
    const response = await apiClient.post(`/api/v1/users/${id}/activate`)
    return response.data
  },
}

export default apiClient
