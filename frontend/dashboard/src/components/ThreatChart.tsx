'use client'

import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts'

const data = [
  { name: 'Mon', alerts: 12, threats: 4, resolved: 10 },
  { name: 'Tue', alerts: 19, threats: 7, resolved: 15 },
  { name: 'Wed', alerts: 15, threats: 3, resolved: 12 },
  { name: 'Thu', alerts: 25, threats: 8, resolved: 20 },
  { name: 'Fri', alerts: 18, threats: 5, resolved: 16 },
  { name: 'Sat', alerts: 8, threats: 2, resolved: 7 },
  { name: 'Sun', alerts: 10, threats: 3, resolved: 9 },
]

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white px-4 py-3 rounded-xl shadow-lg border border-gray-100">
        <p className="text-sm font-semibold text-gray-900 mb-2">{label}</p>
        <div className="space-y-1.5">
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2">
              <span 
                className="w-2.5 h-2.5 rounded-full" 
                style={{ backgroundColor: entry.color }} 
              />
              <span className="text-sm text-gray-600">{entry.name}:</span>
              <span className="text-sm font-semibold text-gray-900">{entry.value}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }
  return null
}

interface ThreatChartProps {
  className?: string
}

export default function ThreatChart({ className = '' }: ThreatChartProps) {
  return (
    <div className={`h-72 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart 
          data={data}
          margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="alertsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="threatsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="resolvedGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#f1f5f9" 
            vertical={false}
          />
          <XAxis 
            dataKey="name" 
            stroke="#94a3b8" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            dy={10}
          />
          <YAxis 
            stroke="#94a3b8" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            dx={-10}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="alerts" 
            stroke="#ef4444" 
            strokeWidth={2.5}
            fill="url(#alertsGradient)"
            name="Alerts"
            dot={false}
            activeDot={{ r: 6, strokeWidth: 2, fill: '#fff' }}
          />
          <Area 
            type="monotone" 
            dataKey="threats" 
            stroke="#f97316" 
            strokeWidth={2.5}
            fill="url(#threatsGradient)"
            name="Threats"
            dot={false}
            activeDot={{ r: 6, strokeWidth: 2, fill: '#fff' }}
          />
          <Area 
            type="monotone" 
            dataKey="resolved" 
            stroke="#22c55e" 
            strokeWidth={2.5}
            fill="url(#resolvedGradient)"
            name="Resolved"
            dot={false}
            activeDot={{ r: 6, strokeWidth: 2, fill: '#fff' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
