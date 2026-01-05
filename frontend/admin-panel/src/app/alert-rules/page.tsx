'use client'

import { useState } from 'react'
import { 
  AlertTriangle, 
  Plus, 
  Edit, 
  Trash2, 
  ToggleLeft, 
  ToggleRight,
  Search,
  Zap
} from 'lucide-react'

interface AlertRule {
  id: number
  name: string
  description: string
  condition: string
  severity: string
  enabled: boolean
  trigger_count: number
  last_triggered?: string
}

const mockRules: AlertRule[] = [
  { id: 1, name: 'Brute Force Detection', description: 'Detect multiple failed login attempts', condition: 'failed_logins > 5 in 5 minutes', severity: 'HIGH', enabled: true, trigger_count: 24, last_triggered: '2026-01-06T10:00:00Z' },
  { id: 2, name: 'Suspicious Process', description: 'Alert on known malicious process names', condition: 'process_name matches malware_signatures', severity: 'CRITICAL', enabled: true, trigger_count: 3, last_triggered: '2026-01-05T15:30:00Z' },
  { id: 3, name: 'Network Anomaly', description: 'Unusual outbound traffic patterns', condition: 'outbound_traffic > 3x baseline', severity: 'MEDIUM', enabled: true, trigger_count: 12 },
  { id: 4, name: 'File Integrity', description: 'Critical system file modifications', condition: 'file_hash changed in /etc/', severity: 'HIGH', enabled: false, trigger_count: 0 },
  { id: 5, name: 'Port Scan Detection', description: 'Detect port scanning activity', condition: 'unique_ports > 100 in 1 minute', severity: 'MEDIUM', enabled: true, trigger_count: 8 },
]

const severityColors: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-700',
  HIGH: 'bg-orange-100 text-orange-700',
  MEDIUM: 'bg-yellow-100 text-yellow-700',
  LOW: 'bg-green-100 text-green-700',
}

export default function AlertRulesPage() {
  const [rules, setRules] = useState(mockRules)
  const [search, setSearch] = useState('')

  const toggleRule = (id: number) => {
    setRules(rules.map(rule => 
      rule.id === id ? { ...rule, enabled: !rule.enabled } : rule
    ))
  }

  const deleteRule = (id: number) => {
    if (confirm('Are you sure you want to delete this rule?')) {
      setRules(rules.filter(rule => rule.id !== id))
    }
  }

  const filteredRules = rules.filter(rule =>
    rule.name.toLowerCase().includes(search.toLowerCase()) ||
    rule.description.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Rules</h1>
          <p className="text-gray-500 mt-1">Configure threat detection rules</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Create Rule
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-orange-500" />
            <div>
              <p className="text-sm text-gray-500">Total Rules</p>
              <p className="text-2xl font-bold">{rules.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <Zap className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-sm text-gray-500">Active Rules</p>
              <p className="text-2xl font-bold">{rules.filter(r => r.enabled).length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-sm text-gray-500">Triggers Today</p>
              <p className="text-2xl font-bold">{rules.reduce((sum, r) => sum + r.trigger_count, 0)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search rules..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* Rules List */}
      <div className="space-y-4">
        {filteredRules.map((rule) => (
          <div key={rule.id} className={`card ${!rule.enabled ? 'opacity-60' : ''}`}>
            <div className="flex items-start gap-4">
              <div className="p-3 bg-orange-50 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-orange-500" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-lg">{rule.name}</h3>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[rule.severity]}`}>
                    {rule.severity}
                  </span>
                  {!rule.enabled && (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                      DISABLED
                    </span>
                  )}
                </div>
                <p className="text-gray-500 mt-1">{rule.description}</p>
                <div className="flex items-center gap-4 mt-3 text-sm">
                  <span className="text-gray-500">
                    Condition: <code className="bg-gray-100 px-2 py-0.5 rounded">{rule.condition}</code>
                  </span>
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span>Triggers: {rule.trigger_count}</span>
                  {rule.last_triggered && (
                    <span>Last: {new Date(rule.last_triggered).toLocaleString()}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => toggleRule(rule.id)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                  title={rule.enabled ? 'Disable' : 'Enable'}
                >
                  {rule.enabled ? (
                    <ToggleRight className="h-6 w-6 text-green-500" />
                  ) : (
                    <ToggleLeft className="h-6 w-6 text-gray-400" />
                  )}
                </button>
                <button className="p-2 hover:bg-gray-100 rounded-lg" title="Edit">
                  <Edit className="h-5 w-5 text-gray-500" />
                </button>
                <button 
                  onClick={() => deleteRule(rule.id)}
                  className="p-2 hover:bg-gray-100 rounded-lg" 
                  title="Delete"
                >
                  <Trash2 className="h-5 w-5 text-red-500" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {filteredRules.length === 0 && (
          <div className="card text-center py-12 text-gray-500">
            No alert rules found
          </div>
        )}
      </div>
    </div>
  )
}
