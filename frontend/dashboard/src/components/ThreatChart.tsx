'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const data = [
  { name: 'Mon', alerts: 12, threats: 4 },
  { name: 'Tue', alerts: 19, threats: 7 },
  { name: 'Wed', alerts: 15, threats: 3 },
  { name: 'Thu', alerts: 25, threats: 8 },
  { name: 'Fri', alerts: 18, threats: 5 },
  { name: 'Sat', alerts: 8, threats: 2 },
  { name: 'Sun', alerts: 10, threats: 3 },
]

export default function ThreatChart() {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" stroke="#888" fontSize={12} />
          <YAxis stroke="#888" fontSize={12} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }} 
          />
          <Line 
            type="monotone" 
            dataKey="alerts" 
            stroke="#ef4444" 
            strokeWidth={2}
            dot={{ fill: '#ef4444' }}
            name="Alerts"
          />
          <Line 
            type="monotone" 
            dataKey="threats" 
            stroke="#f97316" 
            strokeWidth={2}
            dot={{ fill: '#f97316' }}
            name="Threats"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
