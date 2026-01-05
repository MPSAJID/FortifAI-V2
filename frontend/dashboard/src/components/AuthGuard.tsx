'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { api } from '@/lib/api'

// Public routes that don't require authentication
const publicRoutes = ['/login', '/forgot-password', '/reset-password']

interface AuthGuardProps {
  children: React.ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, isLoading, setAuth, logout, setLoading } = useAuthStore()

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      const refreshToken = localStorage.getItem('refresh_token')

      if (!token) {
        setLoading(false)
        if (!publicRoutes.includes(pathname)) {
          router.push('/login')
        }
        return
      }

      try {
        // Verify token by fetching current user
        const user = await api.getCurrentUser()
        setAuth(user, token, refreshToken || '')
      } catch (error) {
        // Token is invalid, logout
        logout()
        if (!publicRoutes.includes(pathname)) {
          router.push('/login')
        }
      }
    }

    checkAuth()
  }, [pathname])

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  // If on public route, render children
  if (publicRoutes.includes(pathname)) {
    return <>{children}</>
  }

  // If authenticated, render children
  if (isAuthenticated) {
    return <>{children}</>
  }

  // Otherwise show nothing (will redirect)
  return null
}

// Role-based access control component
interface RequireRoleProps {
  children: React.ReactNode
  allowedRoles: string[]
  fallback?: React.ReactNode
}

export function RequireRole({ children, allowedRoles, fallback }: RequireRoleProps) {
  const { user } = useAuthStore()

  if (!user || !allowedRoles.includes(user.role)) {
    return fallback ? <>{fallback}</> : (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">Access Denied</h2>
          <p className="text-gray-500 mt-2">You don't have permission to view this page.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
