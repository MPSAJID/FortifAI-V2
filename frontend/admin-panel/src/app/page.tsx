'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Users, 
  Settings, 
  Shield, 
  FileText, 
  Activity,
  AlertTriangle,
  Server,
  Database
} from 'lucide-react'
import { api } from '@/lib/api'

export default function AdminDashboard() {
  const { data: userStats } = useQuery({
    queryKey: ['admin-user-stats'],
    queryFn: api.getUserStats,
  })

  const { data: systemHealth } = useQuery({
    queryKey: ['admin-system-health'],
    queryFn: api.getSystemHealth,
  })

  const stats = [
    { 
      name: 'Total Users', 
      value: userStats?.total || 0, 
      icon: Users, 
      color: 'bg-blue-500',
      change: '+3 this week'
    },
    { 
      name: 'Active Users', 
      value: userStats?.active || 0, 
      icon: Activity, 
      color: 'bg-green-500',
      change: '95% of total'
    },
    { 
      name: 'Alert Rules', 
      value: 24, 
      icon: AlertTriangle, 
      color: 'bg-orange-500',
      change: '12 active'
    },
    { 
      name: 'System Health', 
      value: 'Operational', 
      icon: Server, 
      color: 'bg-emerald-500',
      change: '99.9% uptime'
    },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-500 mt-1">System administration and configuration</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.name}</p>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-xs text-gray-400">{stat.change}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-4">
            <a href="/users" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <Users className="h-8 w-8 text-blue-500 mb-2" />
              <p className="font-medium">Manage Users</p>
              <p className="text-sm text-gray-500">Add, edit, or remove users</p>
            </a>
            <a href="/alert-rules" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <AlertTriangle className="h-8 w-8 text-orange-500 mb-2" />
              <p className="font-medium">Alert Rules</p>
              <p className="text-sm text-gray-500">Configure detection rules</p>
            </a>
            <a href="/audit-logs" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <FileText className="h-8 w-8 text-purple-500 mb-2" />
              <p className="font-medium">Audit Logs</p>
              <p className="text-sm text-gray-500">View system activity</p>
            </a>
            <a href="/settings" className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
              <Settings className="h-8 w-8 text-gray-500 mb-2" />
              <p className="font-medium">Settings</p>
              <p className="text-sm text-gray-500">System configuration</p>
            </a>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">System Status</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-gray-500" />
                <span>Database</span>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded">Healthy</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Server className="h-5 w-5 text-gray-500" />
                <span>API Server</span>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded">Running</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Activity className="h-5 w-5 text-gray-500" />
                <span>ML Engine</span>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-gray-500" />
                <span>Data Collector</span>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 text-sm rounded">Collecting</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Recent Admin Activity</h2>
        <div className="space-y-3">
          {[
            { action: 'User created', user: 'admin', target: 'analyst@fortifai.com', time: '2 minutes ago' },
            { action: 'Alert rule updated', user: 'admin', target: 'Brute Force Detection', time: '15 minutes ago' },
            { action: 'Settings changed', user: 'admin', target: 'Email notifications', time: '1 hour ago' },
            { action: 'User deactivated', user: 'admin', target: 'viewer@fortifai.com', time: '3 hours ago' },
          ].map((activity, i) => (
            <div key={i} className="flex items-center justify-between py-3 border-b last:border-0">
              <div>
                <p className="font-medium">{activity.action}</p>
                <p className="text-sm text-gray-500">
                  by {activity.user} → {activity.target}
                </p>
              </div>
              <span className="text-sm text-gray-400">{activity.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
