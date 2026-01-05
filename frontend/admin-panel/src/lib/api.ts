import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
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

  createUser: async (userData: { 
    username: string
    email: string
    password: string
    full_name?: string
    role?: string 
  }) => {
    const response = await apiClient.post('/api/v1/users', userData)
    return response.data
  },

  updateUser: async (id: number, userData: { 
    username?: string
    email?: string
    full_name?: string
    role?: string
    is_active?: boolean 
  }) => {
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

  // System Health
  getSystemHealth: async () => {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Audit Logs
  getAuditLogs: async (params?: { limit?: number; offset?: number }) => {
    const response = await apiClient.get('/api/v1/audit-logs', { params })
    return response.data
  },

  // Settings
  getSettings: async () => {
    const response = await apiClient.get('/api/v1/settings')
    return response.data
  },

  updateSettings: async (settings: Record<string, any>) => {
    const response = await apiClient.put('/api/v1/settings', settings)
    return response.data
  },
}
