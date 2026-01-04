'use client'

import { LucideIcon } from 'lucide-react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: string
  trendUp?: boolean
  color: 'red' | 'orange' | 'green' | 'blue'
}

const colorClasses = {
  red: {
    bg: 'bg-red-50',
    icon: 'text-red-600',
    value: 'text-red-700'
  },
  orange: {
    bg: 'bg-orange-50',
    icon: 'text-orange-600',
    value: 'text-orange-700'
  },
  green: {
    bg: 'bg-green-50',
    icon: 'text-green-600',
    value: 'text-green-700'
  },
  blue: {
    bg: 'bg-blue-50',
    icon: 'text-blue-600',
    value: 'text-blue-700'
  }
}

export default function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  trendUp,
  color 
}: StatsCardProps) {
  const colors = colorClasses[color]

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className={`p-3 rounded-lg ${colors.bg}`}>
          <Icon className={`h-6 w-6 ${colors.icon}`} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm ${
            trendUp ? 'text-green-600' : 'text-red-600'
          }`}>
            {trendUp ? (
              <TrendingUp className="h-4 w-4" />
            ) : (
              <TrendingDown className="h-4 w-4" />
            )}
            {trend}
          </div>
        )}
      </div>
      <div className="mt-4">
        <h3 className="text-gray-500 text-sm">{title}</h3>
        <p className={`text-2xl font-bold mt-1 ${colors.value}`}>
          {value}
        </p>
      </div>
    </div>
  )
}
