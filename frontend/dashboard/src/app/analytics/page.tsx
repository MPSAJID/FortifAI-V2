'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { Calendar, TrendingUp, Shield, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import { useState } from 'react'

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']

export default function AnalyticsPage() {
  const [days, setDays] = useState(7)

  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['timeline', days],
    queryFn: () => api.getTimeline(days),
  })

  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['risk-assessment'],
    queryFn: () => api.getRiskAssessment(),
  })

  const timelineData = timeline?.timeline 
    ? Object.entries(timeline.timeline).map(([date, data]: [string, any]) => ({
        date: new Date(date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
        alerts: data.alerts,
        threats: data.threats
      }))
    : []

  const severityData = [
    { name: 'Critical', value: riskData?.critical_count || 0 },
    { name: 'High', value: riskData?.high_count || 0 },
    { name: 'Medium', value: riskData?.medium_count || 0 },
    { name: 'Low', value: riskData?.low_count || 0 },
  ]

  if (timelineLoading || riskLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500 mt-1">Security metrics and trends</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-400" />
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <TrendingUp className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Risk Score</p>
              <p className="text-2xl font-bold">
                {((riskData?.overall_risk_score || 0) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Unresolved Critical</p>
              <p className="text-2xl font-bold">{riskData?.critical_count || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-50 rounded-lg">
              <Shield className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">High Risk Threats</p>
              <p className="text-2xl font-bold">{riskData?.high_risk_threats || 0}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-50 rounded-lg">
              <Shield className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Risk Level</p>
              <p className="text-2xl font-bold capitalize">{riskData?.risk_level || 'Unknown'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Timeline */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Activity Timeline</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" stroke="#888" fontSize={12} />
                <YAxis stroke="#888" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }} 
                />
                <Bar dataKey="alerts" fill="#ef4444" name="Alerts" radius={[4, 4, 0, 0]} />
                <Bar dataKey="threats" fill="#f97316" name="Threats" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Alert Severity Distribution</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Security Recommendations</h2>
        <div className="space-y-3">
          {riskData?.recommendations?.map((rec: string, idx: number) => (
            <div key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
              <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
              <p className="text-gray-700">{rec}</p>
            </div>
          )) || (
            <p className="text-gray-500">No recommendations at this time</p>
          )}
        </div>
      </div>
    </div>
  )
}
