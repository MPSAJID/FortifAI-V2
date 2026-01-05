'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useRouter } from 'next/navigation'
import { 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Server, 
  Shield,
  Eye,
  XCircle
} from 'lucide-react'
import { api } from '@/lib/api'
import { useToastStore } from '@/lib/store'
import { format } from 'date-fns'

interface Alert {
  id: number
  alert_id: string
  title: string
  message: string
  severity: string
  source: string
  status: string
  acknowledged: boolean
  resolved: boolean
  created_at: string
  resolved_at?: string
  metadata?: Record<string, any>
}

const severityConfig: Record<string, { color: string; bg: string; icon: typeof AlertTriangle }> = {
  CRITICAL: { color: 'text-red-600', bg: 'bg-red-100', icon: XCircle },
  HIGH: { color: 'text-orange-600', bg: 'bg-orange-100', icon: AlertTriangle },
  MEDIUM: { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: AlertTriangle },
  LOW: { color: 'text-green-600', bg: 'bg-green-100', icon: Shield },
  INFO: { color: 'text-blue-600', bg: 'bg-blue-100', icon: Eye },
}

export default function AlertDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const { addToast } = useToastStore()
  const alertId = params.id as string

  const { data: alert, isLoading, error } = useQuery<Alert>({
    queryKey: ['alert', alertId],
    queryFn: () => api.getAlert(alertId),
  })

  const acknowledgeMutation = useMutation({
    mutationFn: () => api.acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert', alertId] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      addToast({ type: 'success', title: 'Alert Acknowledged', message: 'The alert has been marked as acknowledged.' })
    },
    onError: () => {
      addToast({ type: 'error', title: 'Error', message: 'Failed to acknowledge alert.' })
    }
  })

  const resolveMutation = useMutation({
    mutationFn: () => api.resolveAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert', alertId] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      addToast({ type: 'success', title: 'Alert Resolved', message: 'The alert has been marked as resolved.' })
    },
    onError: () => {
      addToast({ type: 'error', title: 'Error', message: 'Failed to resolve alert.' })
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !alert) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <XCircle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Alert Not Found</h2>
        <p className="text-gray-500 mt-2">The requested alert could not be found.</p>
        <button
          onClick={() => router.push('/alerts')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Back to Alerts
        </button>
      </div>
    )
  }

  const severity = severityConfig[alert.severity] || severityConfig.INFO
  const SeverityIcon = severity.icon

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push('/alerts')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{alert.title}</h1>
          <p className="text-gray-500 mt-1">Alert ID: {alert.alert_id}</p>
        </div>
        <div className="flex gap-2">
          {!alert.acknowledged && (
            <button
              onClick={() => acknowledgeMutation.mutate()}
              disabled={acknowledgeMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {acknowledgeMutation.isPending ? 'Acknowledging...' : 'Acknowledge'}
            </button>
          )}
          {!alert.resolved && (
            <button
              onClick={() => resolveMutation.mutate()}
              disabled={resolveMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {resolveMutation.isPending ? 'Resolving...' : 'Resolve'}
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Alert Info Card */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Alert Details</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-500">Message</label>
                <p className="mt-1 text-gray-900">{alert.message}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Severity</label>
                  <div className={`mt-1 inline-flex items-center gap-2 px-3 py-1 rounded-full ${severity.bg}`}>
                    <SeverityIcon className={`h-4 w-4 ${severity.color}`} />
                    <span className={`font-medium ${severity.color}`}>{alert.severity}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Status</label>
                  <div className="mt-1">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${
                      alert.resolved 
                        ? 'bg-green-100 text-green-700'
                        : alert.acknowledged
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {alert.resolved ? (
                        <>
                          <CheckCircle className="h-4 w-4" />
                          Resolved
                        </>
                      ) : alert.acknowledged ? (
                        <>
                          <Eye className="h-4 w-4" />
                          Acknowledged
                        </>
                      ) : (
                        <>
                          <Clock className="h-4 w-4" />
                          New
                        </>
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Source</label>
                  <div className="mt-1 flex items-center gap-2">
                    <Server className="h-4 w-4 text-gray-400" />
                    <span>{alert.source}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Created At</label>
                  <div className="mt-1 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-gray-400" />
                    <span>{format(new Date(alert.created_at), 'PPpp')}</span>
                  </div>
                </div>
              </div>

              {alert.resolved_at && (
                <div>
                  <label className="text-sm text-gray-500">Resolved At</label>
                  <div className="mt-1 flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>{format(new Date(alert.resolved_at), 'PPpp')}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Metadata Card */}
          {alert.metadata && Object.keys(alert.metadata).length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Additional Information</h2>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                {JSON.stringify(alert.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Right Column - Timeline */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Timeline</h2>
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <AlertTriangle className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="font-medium">Alert Created</p>
                  <p className="text-sm text-gray-500">
                    {format(new Date(alert.created_at), 'PPpp')}
                  </p>
                </div>
              </div>
              
              {alert.acknowledged && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Eye className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium">Acknowledged</p>
                    <p className="text-sm text-gray-500">Alert was reviewed</p>
                  </div>
                </div>
              )}
              
              {alert.resolved && alert.resolved_at && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium">Resolved</p>
                    <p className="text-sm text-gray-500">
                      {format(new Date(alert.resolved_at), 'PPpp')}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <button className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-3">
                <Shield className="h-5 w-5 text-gray-400" />
                <span>Create Incident</span>
              </button>
              <button className="w-full text-left px-4 py-3 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-3">
                <Server className="h-5 w-5 text-gray-400" />
                <span>View Related Threats</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
