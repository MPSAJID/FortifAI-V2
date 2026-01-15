'use client'

import { LucideIcon, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: string
  trendUp?: boolean
  trendLabel?: string
  color: 'red' | 'orange' | 'green' | 'blue' | 'purple' | 'indigo'
  href?: string
  subtitle?: string
}

const colorConfig = {
  red: {
    bg: 'bg-gradient-to-br from-red-50 to-red-100',
    iconBg: 'bg-gradient-to-br from-red-500 to-red-600',
    icon: 'text-white',
    value: 'text-red-700',
    ring: 'ring-red-500/20',
    glow: 'shadow-red-500/10',
  },
  orange: {
    bg: 'bg-gradient-to-br from-orange-50 to-amber-100',
    iconBg: 'bg-gradient-to-br from-orange-500 to-amber-600',
    icon: 'text-white',
    value: 'text-orange-700',
    ring: 'ring-orange-500/20',
    glow: 'shadow-orange-500/10',
  },
  green: {
    bg: 'bg-gradient-to-br from-emerald-50 to-green-100',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-green-600',
    icon: 'text-white',
    value: 'text-emerald-700',
    ring: 'ring-emerald-500/20',
    glow: 'shadow-emerald-500/10',
  },
  blue: {
    bg: 'bg-gradient-to-br from-blue-50 to-indigo-100',
    iconBg: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    icon: 'text-white',
    value: 'text-blue-700',
    ring: 'ring-blue-500/20',
    glow: 'shadow-blue-500/10',
  },
  purple: {
    bg: 'bg-gradient-to-br from-purple-50 to-violet-100',
    iconBg: 'bg-gradient-to-br from-purple-500 to-violet-600',
    icon: 'text-white',
    value: 'text-purple-700',
    ring: 'ring-purple-500/20',
    glow: 'shadow-purple-500/10',
  },
  indigo: {
    bg: 'bg-gradient-to-br from-indigo-50 to-blue-100',
    iconBg: 'bg-gradient-to-br from-indigo-500 to-blue-600',
    icon: 'text-white',
    value: 'text-indigo-700',
    ring: 'ring-indigo-500/20',
    glow: 'shadow-indigo-500/10',
  },
}

export default function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  trendUp,
  trendLabel,
  color,
  href,
  subtitle
}: StatsCardProps) {
  const config = colorConfig[color]
  
  const CardWrapper = href ? 'a' : 'div'
  const cardProps = href ? { href } : {}

  return (
    <CardWrapper
      {...cardProps}
      className={`
        group relative overflow-hidden rounded-xl bg-white p-6 
        shadow-sm hover:shadow-md transition-all duration-300
        border border-gray-100 hover:border-gray-200
        ${href ? 'cursor-pointer hover:-translate-y-0.5' : ''}
      `}
    >
      {/* Background Decoration */}
      <div className={`
        absolute -right-8 -top-8 h-32 w-32 rounded-full opacity-50
        ${config.bg} blur-2xl transition-all duration-500 group-hover:opacity-70 group-hover:scale-110
      `} />
      
      <div className="relative">
        {/* Header Row */}
        <div className="flex items-start justify-between">
          {/* Icon */}
          <div className={`
            flex h-12 w-12 items-center justify-center rounded-xl
            ${config.iconBg} shadow-lg ${config.glow}
            transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3
          `}>
            <Icon className={`h-6 w-6 ${config.icon}`} />
          </div>
          
          {/* Trend Badge */}
          {trend && (
            <div className={`
              flex items-center gap-1 rounded-full px-2.5 py-1 text-sm font-medium
              ${trendUp 
                ? 'bg-emerald-50 text-emerald-700' 
                : 'bg-red-50 text-red-700'
              }
            `}>
              {trendUp ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : (
                <TrendingDown className="h-3.5 w-3.5" />
              )}
              <span>{trend}</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="mt-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className={`mt-1 text-3xl font-bold tracking-tight ${config.value}`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-400">{subtitle}</p>
          )}
          {trendLabel && (
            <p className="mt-2 text-xs text-gray-500">{trendLabel}</p>
          )}
        </div>

        {/* Link Arrow */}
        {href && (
          <div className="absolute bottom-0 right-0 opacity-0 translate-x-2 
                        group-hover:opacity-100 group-hover:translate-x-0 
                        transition-all duration-300">
            <ArrowRight className="h-5 w-5 text-gray-400" />
          </div>
        )}
      </div>
    </CardWrapper>
  )
}
