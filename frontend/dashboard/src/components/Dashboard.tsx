'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  AlertTriangle, 
  Shield, 
  Activity, 
  TrendingUp,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { api } from '@/lib/api'
import StatsCard from './StatsCard'
import AlertsTable from './AlertsTable'
import ThreatChart from './ThreatChart'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
        <p className="text-gray-500 mt-1">Real-time threat monitoring and analytics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Alerts"
          value={stats?.summary?.total_alerts || 0}
          icon={AlertTriangle}
          trend="+12%"
          trendUp={false}
          color="red"
        />
        <StatsCard
          title="Active Threats"
          value={stats?.summary?.total_threats || 0}
          icon={Shield}
          trend="+5%"
          trendUp={false}
          color="orange"
        />
        <StatsCard
          title="System Health"
          value={stats?.summary?.system_health === 'operational' ? 'Good' : 'Warning'}
          icon={Activity}
          color="green"
        />
        <StatsCard
          title="Resolved Today"
          value={24}
          icon={CheckCircle}
          trend="+18%"
          trendUp={true}
          color="blue"
        />
      </div>

      {/* Charts and Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Threat Trend Chart */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Threat Activity (7 Days)</h2>
          <ThreatChart />
        </div>

        {/* Risk Assessment */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Risk Assessment</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
              <div className="flex items-center gap-3">
                <XCircle className="h-6 w-6 text-red-500" />
                <span className="font-medium">Critical Alerts</span>
              </div>
              <span className="text-2xl font-bold text-red-600">3</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-orange-50 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-orange-500" />
                <span className="font-medium">High Priority</span>
              </div>
              <span className="text-2xl font-bold text-orange-600">8</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-green-500" />
                <span className="font-medium">Resolved</span>
              </div>
              <span className="text-2xl font-bold text-green-600">45</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Alerts</h2>
          <a href="/alerts" className="text-blue-600 hover:underline text-sm">
            View all
          </a>
        </div>
        <AlertsTable alerts={stats?.recent_alerts || []} />
      </div>
    </div>
  )
}
