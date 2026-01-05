'use client'

import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle, Activity } from 'lucide-react'
import { api } from '@/lib/api'

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

const riskColors: Record<string, string> = {
  high: 'text-red-600 bg-red-50',
  medium: 'text-orange-600 bg-orange-50',
  low: 'text-green-600 bg-green-50'
}

function getRiskLevel(score: number): string {
  if (score >= 0.7) return 'high'
  if (score >= 0.4) return 'medium'
  return 'low'
}

export default function ThreatsPage() {
  const { data: threats, isLoading } = useQuery({
    queryKey: ['threats'],
    queryFn: () => api.getThreats(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Threats</h1>
        <p className="text-gray-500 mt-1">Detected security threats and incidents</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">High Risk</p>
              <p className="text-2xl font-bold">
                {threats?.filter((t: Threat) => t.risk_score >= 0.7).length || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-50 rounded-lg">
              <Activity className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Medium Risk</p>
              <p className="text-2xl font-bold">
                {threats?.filter((t: Threat) => t.risk_score >= 0.4 && t.risk_score < 0.7).length || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-50 rounded-lg">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Low Risk</p>
              <p className="text-2xl font-bold">
                {threats?.filter((t: Threat) => t.risk_score < 0.4).length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Threats Table */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">All Detected Threats</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-gray-500 font-medium">ID</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Type</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Classification</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Risk Score</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Source IP</th>
                <th className="text-left py-3 px-4 text-gray-500 font-medium">Detected</th>
              </tr>
            </thead>
            <tbody>
              {threats?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    No threats detected
                  </td>
                </tr>
              ) : (
                threats?.map((threat: Threat) => {
                  const riskLevel = getRiskLevel(threat.risk_score)
                  return (
                    <tr key={threat.threat_id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm text-gray-600">{threat.threat_id}</td>
                      <td className="py-3 px-4 text-sm font-medium">{threat.threat_type}</td>
                      <td className="py-3 px-4 text-sm">{threat.classification}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${riskColors[riskLevel]}`}>
                          {(threat.risk_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {threat.source_ip || 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {new Date(threat.detected_at).toLocaleString()}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
