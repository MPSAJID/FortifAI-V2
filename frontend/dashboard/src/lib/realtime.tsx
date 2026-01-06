'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useDashboardStore, useToastStore } from '@/lib/store'

interface UseRealtimeOptions {
  enabled?: boolean
  onAlert?: (alert: any) => void
  onThreat?: (threat: any) => void
  onConnection?: (connected: boolean) => void
}

/**
 * Hook for real-time updates via Server-Sent Events (SSE)
 * Falls back to polling if SSE is not available
 */
export function useRealtime(options: UseRealtimeOptions = {}) {
  const { enabled = true, onAlert, onThreat, onConnection } = options
  const queryClient = useQueryClient()
  const { setConnected, setLastUpdate } = useDashboardStore()
  const { addToast } = useToastStore()
  const eventSourceRef = useRef<EventSource | null>(null)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const handleAlert = useCallback((alert: any) => {
    // Invalidate alerts query to refetch
    queryClient.invalidateQueries({ queryKey: ['alerts'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
    
    // Show toast notification for high severity alerts
    if (['CRITICAL', 'HIGH'].includes(alert.severity)) {
      addToast({
        type: alert.severity === 'CRITICAL' ? 'error' : 'warning',
        title: `New ${alert.severity} Alert`,
        message: alert.title
      })
    }

    onAlert?.(alert)
    setLastUpdate(new Date().toISOString())
  }, [queryClient, addToast, onAlert, setLastUpdate])

  const handleThreat = useCallback((threat: any) => {
    queryClient.invalidateQueries({ queryKey: ['threats'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
    
    onThreat?.(threat)
    setLastUpdate(new Date().toISOString())
  }, [queryClient, onThreat, setLastUpdate])

  const connectSSE = useCallback(() => {
    if (!enabled) return

    const token = localStorage.getItem('token')
    if (!token) return

    try {
      // Create SSE connection with auth token as query param
      const url = `${API_URL}/api/v1/events/stream?token=${encodeURIComponent(token)}`
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        console.log('SSE connected')
        setConnected(true)
        onConnection?.(true)
      }

      eventSource.addEventListener('alert', (event) => {
        try {
          const data = JSON.parse(event.data)
          handleAlert(data)
        } catch (e) {
          console.error('Failed to parse alert event:', e)
        }
      })

      eventSource.addEventListener('threat', (event) => {
        try {
          const data = JSON.parse(event.data)
          handleThreat(data)
        } catch (e) {
          console.error('Failed to parse threat event:', e)
        }
      })

      eventSource.addEventListener('heartbeat', () => {
        setLastUpdate(new Date().toISOString())
      })

      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        setConnected(false)
        onConnection?.(false)
        eventSource.close()
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectSSE()
        }, 5000)
      }
    } catch (error) {
      console.error('Failed to create SSE connection:', error)
      // Fall back to polling
      startPolling()
    }
  }, [enabled, API_URL, handleAlert, handleThreat, setConnected, setLastUpdate, onConnection])

  const startPolling = useCallback(() => {
    if (pollingRef.current) return

    console.log('Starting polling fallback')
    
    pollingRef.current = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      setLastUpdate(new Date().toISOString())
    }, 30000) // Poll every 30 seconds
  }, [queryClient, setLastUpdate])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    setConnected(false)
  }, [setConnected])

  useEffect(() => {
    if (enabled) {
      connectSSE()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connectSSE, disconnect])

  return {
    disconnect,
    reconnect: connectSSE,
  }
}

/**
 * Hook for polling-based updates (simpler alternative)
 */
export function usePollingUpdates(interval: number = 30000) {
  const queryClient = useQueryClient()
  const { setLastUpdate } = useDashboardStore()

  useEffect(() => {
    const timer = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['threats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      setLastUpdate(new Date().toISOString())
    }, interval)

    return () => clearInterval(timer)
  }, [queryClient, interval, setLastUpdate])
}

/**
 * Connection status indicator component
 */
export function ConnectionStatus() {
  const { isConnected, lastUpdate } = useDashboardStore()

  return (
    <div className="flex items-center gap-2 text-sm">
      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-gray-500">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
      {lastUpdate && (
        <span className="text-gray-400 text-xs">
          Last update: {new Date(lastUpdate).toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}
