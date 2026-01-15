'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  AlertTriangle, 
  Shield, 
  Activity, 
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
  Zap,
  TrendingUp,
  Target,
  Eye
} from 'lucide-react'
import { api } from '@/lib/api'
import StatsCard from './StatsCard'
import AlertsTable from './AlertsTable'
import ThreatChart from './ThreatChart'
import { DashboardSkeleton } from './Skeleton'
import { format } from 'date-fns'

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.getDashboardStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return <DashboardSkeleton />
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 text-red-600 mb-4">
            <XCircle className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Failed to load dashboard</h3>
          <p className="text-gray-500 mt-1">Please try refreshing the page</p>
        </div>
      </div>
    )
  }

  const criticalAlerts = stats?.recent_alerts?.filter((a: any) => a.severity === 'CRITICAL').length || 0
  const highAlerts = stats?.recent_alerts?.filter((a: any) => a.severity === 'HIGH').length || 0
  const resolvedToday = 24 // This would come from API

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Security Dashboard</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full 
                           bg-emerald-50 text-emerald-700 text-xs font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </span>
          </div>
          <p className="text-gray-500 mt-1">
            Real-time threat monitoring and security analytics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-500">
            Last updated: {format(new Date(), 'MMM d, HH:mm:ss')}
          </div>
          <a 
            href="/scanner" 
            className="btn-primary"
          >
            <Zap className="h-4 w-4" />
            Quick Scan
          </a>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Alerts"
          value={stats?.summary?.total_alerts || 0}
          icon={AlertTriangle}
          trend="+12%"
          trendUp={false}
          trendLabel="vs last week"
          color="red"
          href="/alerts"
        />
        <StatsCard
          title="Active Threats"
          value={stats?.summary?.total_threats || 0}
          icon={Shield}
          trend="+5%"
          trendUp={false}
          trendLabel="vs last week"
          color="orange"
          href="/threats"
        />
        <StatsCard
          title="System Health"
          value={stats?.summary?.system_health === 'operational' ? 'Healthy' : 'Warning'}
          icon={Activity}
          color="green"
          subtitle="All systems operational"
        />
        <StatsCard
          title="Resolved Today"
          value={resolvedToday}
          icon={CheckCircle}
          trend="+18%"
          trendUp={true}
          trendLabel="vs yesterday"
          color="blue"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Threat Trend Chart - Takes 2 columns */}
        <div className="xl:col-span-2 card-hover">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Threat Activity</h2>
              <p className="text-sm text-gray-500">Last 7 days trend analysis</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-sm text-gray-600">Alerts</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-sm text-gray-600">Threats</span>
              </div>
            </div>
          </div>
          <ThreatChart />
        </div>

        {/* Risk Assessment - Takes 1 column */}
        <div className="card-hover">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Risk Overview</h2>
              <p className="text-sm text-gray-500">Current security status</p>
            </div>
            <Target className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-4">
            {/* Critical */}
            <div className="group p-4 rounded-xl bg-gradient-to-r from-red-50 to-red-50/50 
                          border border-red-100 hover:border-red-200 transition-all cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg 
                                bg-red-100 text-red-600">
                    <XCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Critical Alerts</p>
                    <p className="text-sm text-gray-500">Requires immediate action</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-red-600">{criticalAlerts}</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 
                                       transition-opacity inline-block ml-2" />
                </div>
              </div>
            </div>
            
            {/* High */}
            <div className="group p-4 rounded-xl bg-gradient-to-r from-orange-50 to-amber-50/50 
                          border border-orange-100 hover:border-orange-200 transition-all cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg 
                                bg-orange-100 text-orange-600">
                    <AlertTriangle className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">High Priority</p>
                    <p className="text-sm text-gray-500">Needs attention soon</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-orange-600">{highAlerts}</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 
                                       transition-opacity inline-block ml-2" />
                </div>
              </div>
            </div>
            
            {/* Resolved */}
            <div className="group p-4 rounded-xl bg-gradient-to-r from-emerald-50 to-green-50/50 
                          border border-emerald-100 hover:border-emerald-200 transition-all cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg 
                                bg-emerald-100 text-emerald-600">
                    <CheckCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Resolved</p>
                    <p className="text-sm text-gray-500">Successfully handled</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-emerald-600">45</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 
                                       transition-opacity inline-block ml-2" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card-hover">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
            <p className="text-sm text-gray-500">Latest security notifications</p>
          </div>
          <a 
            href="/alerts" 
            className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 
                     hover:text-blue-700 transition-colors"
          >
            View all
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
        <AlertsTable alerts={stats?.recent_alerts || []} />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a href="/scanner" className="group card-interactive">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl 
                          bg-blue-100 text-blue-600 group-hover:bg-blue-600 group-hover:text-white 
                          transition-colors">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Security Scanner</h3>
              <p className="text-sm text-gray-500">Scan URLs for vulnerabilities</p>
            </div>
          </div>
        </a>
        
        <a href="/analytics" className="group card-interactive">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl 
                          bg-purple-100 text-purple-600 group-hover:bg-purple-600 group-hover:text-white 
                          transition-colors">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Analytics</h3>
              <p className="text-sm text-gray-500">View detailed reports</p>
            </div>
          </div>
        </a>
        
        <a href="/threats" className="group card-interactive">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl 
                          bg-orange-100 text-orange-600 group-hover:bg-orange-600 group-hover:text-white 
                          transition-colors">
              <Eye className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Threat Monitor</h3>
              <p className="text-sm text-gray-500">Track detected threats</p>
            </div>
          </div>
        </a>
      </div>
    </div>
  )
}
