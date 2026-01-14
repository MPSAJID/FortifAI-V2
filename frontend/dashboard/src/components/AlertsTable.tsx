'use client'

import { AlertTriangle, Eye, Clock, ExternalLink } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'

interface Alert {
  id: string
  alert_id?: string
  title: string
  severity: string
  source?: string
  created_at?: string
}

interface AlertsTableProps {
  alerts: Alert[]
  compact?: boolean
}

const severityConfig: Record<string, { class: string; dotColor: string; label: string }> = {
  CRITICAL: { 
    class: 'bg-red-50 text-red-700 ring-1 ring-red-600/10', 
    dotColor: 'bg-red-500',
    label: 'Critical'
  },
  HIGH: { 
    class: 'bg-orange-50 text-orange-700 ring-1 ring-orange-600/10', 
    dotColor: 'bg-orange-500',
    label: 'High'
  },
  MEDIUM: { 
    class: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/10', 
    dotColor: 'bg-amber-500',
    label: 'Medium'
  },
  LOW: { 
    class: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/10', 
    dotColor: 'bg-emerald-500',
    label: 'Low'
  },
  INFO: { 
    class: 'bg-blue-50 text-blue-700 ring-1 ring-blue-600/10', 
    dotColor: 'bg-blue-500',
    label: 'Info'
  }
}

export default function AlertsTable({ alerts, compact = false }: AlertsTableProps) {
  if (!alerts.length) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full 
                      bg-gray-100 text-gray-400 mb-3">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <p className="text-gray-500 font-medium">No alerts found</p>
        <p className="text-sm text-gray-400 mt-1">Your system is running smoothly</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="table-header py-3 px-4">Alert</th>
            <th className="table-header py-3 px-4">Severity</th>
            {!compact && <th className="table-header py-3 px-4">Source</th>}
            <th className="table-header py-3 px-4">Time</th>
            <th className="table-header py-3 px-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {alerts.map((alert, index) => {
            const severity = severityConfig[alert.severity] || severityConfig.INFO
            return (
              <tr 
                key={alert.id || alert.alert_id || index} 
                className="group hover:bg-gray-50/50 transition-colors"
              >
                <td className="py-4 px-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${severity.dotColor} flex-shrink-0`} />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {alert.title}
                      </p>
                      {(alert.id || alert.alert_id) && (
                        <p className="text-xs text-gray-400 font-mono">
                          {alert.alert_id || alert.id}
                        </p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${severity.class}`}>
                    {severity.label}
                  </span>
                </td>
                {!compact && (
                  <td className="py-4 px-4">
                    <span className="text-sm text-gray-600">{alert.source || 'System'}</span>
                  </td>
                )}
                <td className="py-4 px-4">
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Clock className="h-3.5 w-3.5" />
                    <span className="text-sm">
                      {alert.created_at 
                        ? formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })
                        : 'Just now'
                      }
                    </span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a
                      href={`/alerts/${alert.alert_id || alert.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium 
                               text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Eye className="h-4 w-4" />
                      View
                    </a>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
