'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  AlertTriangle, 
  CheckCircle, 
  Eye, 
  Filter, 
  Search,
  Clock,
  Shield,
  Bell,
  XCircle,
  ChevronDown,
  MoreHorizontal,
  RefreshCw
} from 'lucide-react'
import { api } from '@/lib/api'
import { useState } from 'react'
import { format, formatDistanceToNow } from 'date-fns'
import { AlertCardSkeleton, EmptyState } from '@/components/Skeleton'

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
}

const severityConfig: Record<string, { class: string; icon: typeof AlertTriangle; label: string }> = {
  CRITICAL: { 
    class: 'bg-red-50 text-red-700 border-red-200', 
    icon: XCircle,
    label: 'Critical' 
  },
  HIGH: { 
    class: 'bg-orange-50 text-orange-700 border-orange-200', 
    icon: AlertTriangle,
    label: 'High' 
  },
  MEDIUM: { 
    class: 'bg-amber-50 text-amber-700 border-amber-200', 
    icon: Bell,
    label: 'Medium' 
  },
  LOW: { 
    class: 'bg-emerald-50 text-emerald-700 border-emerald-200', 
    icon: Shield,
    label: 'Low' 
  },
  INFO: { 
    class: 'bg-blue-50 text-blue-700 border-blue-200', 
    icon: Bell,
    label: 'Info' 
  }
}

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  const { data: alerts, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['alerts', severityFilter, statusFilter],
    queryFn: () => api.getAlerts({ 
      severity: severityFilter || undefined,
      status: statusFilter || undefined 
    }),
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => api.acknowledgeAlert(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] })
  })

  const resolveMutation = useMutation({
    mutationFn: (id: string) => api.resolveAlert(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] })
  })

  // Filter alerts by search query
  const filteredAlerts = alerts?.filter((alert: Alert) => 
    alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
    alert.alert_id.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  // Count alerts by severity
  const criticalCount = alerts?.filter((a: Alert) => a.severity === 'CRITICAL').length || 0
  const highCount = alerts?.filter((a: Alert) => a.severity === 'HIGH').length || 0
  const unresolvedCount = alerts?.filter((a: Alert) => !a.resolved).length || 0

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="page-header">
          <div className="skeleton h-8 w-32 mb-2" />
          <div className="skeleton h-4 w-64" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card">
              <div className="skeleton h-12 w-12 rounded-xl mb-4" />
              <div className="skeleton h-4 w-24 mb-2" />
              <div className="skeleton h-8 w-16" />
            </div>
          ))}
        </div>
        {[...Array(3)].map((_, i) => <AlertCardSkeleton key={i} />)}
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="page-title">Security Alerts</h1>
          <p className="page-description">Monitor and respond to security alerts in real-time</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => refetch()}
            disabled={isFetching}
            className="btn-secondary"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card border-l-4 border-l-red-500">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-red-600">
              <XCircle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Critical Alerts</p>
              <p className="text-2xl font-bold text-gray-900">{criticalCount}</p>
            </div>
          </div>
        </div>
        <div className="card border-l-4 border-l-orange-500">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-50 text-orange-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500">High Priority</p>
              <p className="text-2xl font-bold text-gray-900">{highCount}</p>
            </div>
          </div>
        </div>
        <div className="card border-l-4 border-l-blue-500">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <Bell className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Unresolved</p>
              <p className="text-2xl font-bold text-gray-900">{unresolvedCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search alerts by title, message, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-with-icon"
            />
          </div>
          
          {/* Severity Filter */}
          <div className="flex items-center gap-3">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <EmptyState 
            icon={Bell}
            title="No alerts found"
            description="There are no alerts matching your filters. Try adjusting your search criteria."
          />
        ) : (
          filteredAlerts.map((alert: Alert) => {
            const severity = severityConfig[alert.severity] || severityConfig.INFO
            const SeverityIcon = severity.icon
            
            return (
              <div 
                key={alert.alert_id} 
                className="card hover:shadow-md transition-all duration-200 group"
              >
                <div className="flex items-start gap-4">
                  {/* Severity Icon */}
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl flex-shrink-0
                                ${alert.severity === 'CRITICAL' ? 'bg-red-100 text-red-600' : ''}
                                ${alert.severity === 'HIGH' ? 'bg-orange-100 text-orange-600' : ''}
                                ${alert.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-600' : ''}
                                ${alert.severity === 'LOW' ? 'bg-emerald-100 text-emerald-600' : ''}
                                ${alert.severity === 'INFO' ? 'bg-blue-100 text-blue-600' : ''}`}
                  >
                    <SeverityIcon className="h-5 w-5" />
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className={`badge border ${severity.class}`}>
                        {severity.label}
                      </span>
                      <span className="text-sm text-gray-400 font-mono">{alert.alert_id}</span>
                      {alert.resolved && (
                        <span className="badge bg-emerald-50 text-emerald-700">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Resolved
                        </span>
                      )}
                      {alert.acknowledged && !alert.resolved && (
                        <span className="badge bg-blue-50 text-blue-700">
                          <Eye className="h-3 w-3 mr-1" />
                          Acknowledged
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{alert.title}</h3>
                    <p className="text-gray-600 mb-3">{alert.message}</p>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1.5">
                        <Shield className="h-4 w-4" />
                        {alert.source}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Clock className="h-4 w-4" />
                        {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a
                      href={`/alerts/${alert.alert_id}`}
                      className="btn-icon"
                      title="View details"
                    >
                      <Eye className="h-5 w-5" />
                    </a>
                    {!alert.acknowledged && (
                      <button
                        onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
                        disabled={acknowledgeMutation.isPending}
                        className="btn-sm bg-blue-50 text-blue-600 hover:bg-blue-100"
                      >
                        Acknowledge
                      </button>
                    )}
                    {!alert.resolved && (
                      <button
                        onClick={() => resolveMutation.mutate(alert.alert_id)}
                        disabled={resolveMutation.isPending}
                        className="btn-sm bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
