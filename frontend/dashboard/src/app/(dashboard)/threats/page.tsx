'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  Shield, 
  AlertTriangle, 
  Activity, 
  Search, 
  Filter,
  Eye,
  Globe,
  Server,
  Clock,
  Target,
  Zap,
  RefreshCw
} from 'lucide-react'
import { api } from '@/lib/api'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { TableSkeleton, EmptyState } from '@/components/Skeleton'

interface Threat {
  id: number
  threat_id: string
  threat_type: string
  confidence: number
  source_ip: string | null
  destination_ip: string | null
  process_name: string | null
  classification: string
  risk_score: number
  detected_at: string
}

const riskConfig = {
  high: { 
    class: 'bg-red-50 text-red-700 ring-1 ring-red-600/10', 
    barColor: 'bg-red-500',
    label: 'High Risk' 
  },
  medium: { 
    class: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/10', 
    barColor: 'bg-amber-500',
    label: 'Medium Risk' 
  },
  low: { 
    class: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/10', 
    barColor: 'bg-emerald-500',
    label: 'Low Risk' 
  },
}

function getRiskLevel(score: number): 'high' | 'medium' | 'low' {
  if (score >= 0.7) return 'high'
  if (score >= 0.4) return 'medium'
  return 'low'
}

export default function ThreatsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  
  const { data: threats, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['threats'],
    queryFn: () => api.getThreats(),
    refetchInterval: 30000,
  })

  // Filter threats
  const filteredThreats = threats?.filter((threat: Threat) => {
    const matchesSearch = 
      threat.threat_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      threat.threat_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      threat.classification.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (threat.source_ip && threat.source_ip.includes(searchQuery))
    
    const matchesType = !typeFilter || threat.threat_type === typeFilter
    
    return matchesSearch && matchesType
  }) || []

  // Get unique threat types for filter
  const threatTypes: string[] = Array.from(new Set(threats?.map((t: Threat) => t.threat_type) || []))

  // Count by risk level
  const highRisk = threats?.filter((t: Threat) => t.risk_score >= 0.7).length || 0
  const mediumRisk = threats?.filter((t: Threat) => t.risk_score >= 0.4 && t.risk_score < 0.7).length || 0
  const lowRisk = threats?.filter((t: Threat) => t.risk_score < 0.4).length || 0

  if (isLoading) {
    return <TableSkeleton rows={8} />
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="page-title">Threat Intelligence</h1>
          <p className="page-description">Detected security threats and incident analysis</p>
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
          <a href="/scanner" className="btn-primary">
            <Zap className="h-4 w-4" />
            New Scan
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-hover border-l-4 border-l-red-500">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl 
                          bg-gradient-to-br from-red-50 to-red-100 text-red-600">
              <AlertTriangle className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">High Risk</p>
              <p className="text-3xl font-bold text-gray-900">{highRisk}</p>
              <p className="text-xs text-gray-400 mt-1">Requires immediate action</p>
            </div>
          </div>
        </div>
        <div className="card-hover border-l-4 border-l-amber-500">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl 
                          bg-gradient-to-br from-amber-50 to-amber-100 text-amber-600">
              <Activity className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Medium Risk</p>
              <p className="text-3xl font-bold text-gray-900">{mediumRisk}</p>
              <p className="text-xs text-gray-400 mt-1">Monitor closely</p>
            </div>
          </div>
        </div>
        <div className="card-hover border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl 
                          bg-gradient-to-br from-emerald-50 to-emerald-100 text-emerald-600">
              <Shield className="h-7 w-7" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Low Risk</p>
              <p className="text-3xl font-bold text-gray-900">{lowRisk}</p>
              <p className="text-xs text-gray-400 mt-1">For your awareness</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by ID, type, classification, or IP address..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-with-icon"
            />
          </div>
          
          {/* Type Filter */}
          <div className="flex items-center gap-3">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="">All Types</option>
              {threatTypes.map((type: string) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Threats Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">All Detected Threats</h2>
            <p className="text-sm text-gray-500">{filteredThreats.length} threats found</p>
          </div>
        </div>
        
        {filteredThreats.length === 0 ? (
          <EmptyState 
            icon={Shield}
            title="No threats detected"
            description="Your system appears to be secure. No threats match your current filters."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="table-header py-3 px-4">Threat</th>
                  <th className="table-header py-3 px-4">Type</th>
                  <th className="table-header py-3 px-4">Risk Score</th>
                  <th className="table-header py-3 px-4">Source</th>
                  <th className="table-header py-3 px-4">Detected</th>
                  <th className="table-header py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredThreats.map((threat: Threat) => {
                  const riskLevel = getRiskLevel(threat.risk_score)
                  const risk = riskConfig[riskLevel]
                  
                  return (
                    <tr key={threat.threat_id} className="group hover:bg-gray-50/50 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className={`flex h-10 w-10 items-center justify-center rounded-lg
                                        ${riskLevel === 'high' ? 'bg-red-100 text-red-600' : ''}
                                        ${riskLevel === 'medium' ? 'bg-amber-100 text-amber-600' : ''}
                                        ${riskLevel === 'low' ? 'bg-emerald-100 text-emerald-600' : ''}`}
                          >
                            <Target className="h-5 w-5" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{threat.classification}</p>
                            <p className="text-xs text-gray-400 font-mono">{threat.threat_id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="badge bg-gray-100 text-gray-700">
                          {threat.threat_type}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${risk.barColor} rounded-full transition-all`}
                              style={{ width: `${threat.risk_score * 100}%` }}
                            />
                          </div>
                          <span className={`badge ${risk.class}`}>
                            {(threat.risk_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        {threat.source_ip ? (
                          <div className="flex items-center gap-2">
                            <Globe className="h-4 w-4 text-gray-400" />
                            <span className="text-sm font-mono text-gray-600">{threat.source_ip}</span>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-1.5 text-gray-500">
                          <Clock className="h-4 w-4" />
                          <span className="text-sm">
                            {formatDistanceToNow(new Date(threat.detected_at), { addSuffix: true })}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="btn-icon" title="View details">
                            <Eye className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
