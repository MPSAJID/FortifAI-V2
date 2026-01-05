'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  FileText, 
  Filter, 
  Search,
  User,
  Settings,
  Shield,
  AlertTriangle,
  Key,
  Download
} from 'lucide-react'
import { useState } from 'react'
import { format } from 'date-fns'

interface AuditLog {
  id: number
  action: string
  actor: string
  target: string
  details: string
  ip_address: string
  timestamp: string
}

const actionIcons: Record<string, typeof User> = {
  user_created: User,
  user_updated: User,
  user_deleted: User,
  settings_changed: Settings,
  alert_rule_created: AlertTriangle,
  alert_rule_updated: AlertTriangle,
  login_success: Key,
  login_failed: Shield,
}

const actionColors: Record<string, string> = {
  user_created: 'bg-green-100 text-green-700',
  user_updated: 'bg-blue-100 text-blue-700',
  user_deleted: 'bg-red-100 text-red-700',
  settings_changed: 'bg-purple-100 text-purple-700',
  alert_rule_created: 'bg-orange-100 text-orange-700',
  login_success: 'bg-green-100 text-green-700',
  login_failed: 'bg-red-100 text-red-700',
}

// Mock data for demonstration
const mockAuditLogs: AuditLog[] = [
  { id: 1, action: 'user_created', actor: 'admin', target: 'analyst@fortifai.com', details: 'New user created with analyst role', ip_address: '192.168.1.100', timestamp: '2026-01-06T10:30:00Z' },
  { id: 2, action: 'settings_changed', actor: 'admin', target: 'notification_settings', details: 'Email notifications enabled', ip_address: '192.168.1.100', timestamp: '2026-01-06T09:15:00Z' },
  { id: 3, action: 'login_success', actor: 'analyst', target: 'analyst@fortifai.com', details: 'Successful login', ip_address: '192.168.1.50', timestamp: '2026-01-06T08:00:00Z' },
  { id: 4, action: 'alert_rule_created', actor: 'admin', target: 'Brute Force Detection', details: 'New alert rule created', ip_address: '192.168.1.100', timestamp: '2026-01-05T16:45:00Z' },
  { id: 5, action: 'user_deleted', actor: 'admin', target: 'olduser@fortifai.com', details: 'User account removed', ip_address: '192.168.1.100', timestamp: '2026-01-05T14:20:00Z' },
  { id: 6, action: 'login_failed', actor: 'unknown', target: 'admin', details: 'Invalid password attempt', ip_address: '10.0.0.55', timestamp: '2026-01-05T12:00:00Z' },
]

export default function AuditLogsPage() {
  const [search, setSearch] = useState('')
  const [actionFilter, setActionFilter] = useState('')

  // In production, this would fetch from the API
  const logs = mockAuditLogs.filter(log => {
    const matchesSearch = search === '' || 
      log.actor.toLowerCase().includes(search.toLowerCase()) ||
      log.target.toLowerCase().includes(search.toLowerCase()) ||
      log.details.toLowerCase().includes(search.toLowerCase())
    const matchesAction = actionFilter === '' || log.action === actionFilter
    return matchesSearch && matchesAction
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-500 mt-1">Track all administrative actions</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Download className="h-5 w-5" />
          Export Logs
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search logs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">All Actions</option>
            <option value="user_created">User Created</option>
            <option value="user_updated">User Updated</option>
            <option value="user_deleted">User Deleted</option>
            <option value="settings_changed">Settings Changed</option>
            <option value="login_success">Login Success</option>
            <option value="login_failed">Login Failed</option>
          </select>
        </div>
      </div>

      {/* Logs List */}
      <div className="card">
        <div className="space-y-4">
          {logs.map((log) => {
            const Icon = actionIcons[log.action] || FileText
            const colorClass = actionColors[log.action] || 'bg-gray-100 text-gray-700'

            return (
              <div key={log.id} className="flex items-start gap-4 p-4 border rounded-lg hover:bg-gray-50">
                <div className={`p-2 rounded-lg ${colorClass}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
                      {log.action.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-500">by {log.actor}</span>
                  </div>
                  <p className="font-medium mt-1">{log.details}</p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                    <span>Target: {log.target}</span>
                    <span>IP: {log.ip_address}</span>
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {format(new Date(log.timestamp), 'PPp')}
                </div>
              </div>
            )
          })}
          {logs.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No audit logs found
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
