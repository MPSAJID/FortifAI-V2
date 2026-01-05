'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setAuth: (user: User, token: string, refreshToken: string) => void
  logout: () => void
  setLoading: (loading: boolean) => void
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,

      setAuth: (user, token, refreshToken) => {
        localStorage.setItem('token', token)
        localStorage.setItem('refresh_token', refreshToken)
        set({ 
          user, 
          token, 
          refreshToken, 
          isAuthenticated: true,
          isLoading: false 
        })
      },

      logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        set({ 
          user: null, 
          token: null, 
          refreshToken: null, 
          isAuthenticated: false,
          isLoading: false 
        })
      },

      setLoading: (loading) => set({ isLoading: loading }),

      updateUser: (userData) => set((state) => ({
        user: state.user ? { ...state.user, ...userData } : null
      })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token, 
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)

// Toast notification store
interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
}

interface ToastState {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  
  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }]
    }))
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id)
      }))
    }, 5000)
  },
  
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter((t) => t.id !== id)
  })),
  
  clearToasts: () => set({ toasts: [] }),
}))

// Dashboard real-time state
interface DashboardState {
  lastUpdate: string | null
  isConnected: boolean
  setLastUpdate: (time: string) => void
  setConnected: (connected: boolean) => void
}

export const useDashboardStore = create<DashboardState>((set) => ({
  lastUpdate: null,
  isConnected: false,
  
  setLastUpdate: (time) => set({ lastUpdate: time }),
  setConnected: (connected) => set({ isConnected: connected }),
}))
