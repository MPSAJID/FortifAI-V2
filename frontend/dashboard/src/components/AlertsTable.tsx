'use client'

interface Alert {
  id: string
  title: string
  severity: string
}

interface AlertsTableProps {
  alerts: Alert[]
}

const severityClasses: Record<string, string> = {
  CRITICAL: 'severity-critical',
  HIGH: 'severity-high',
  MEDIUM: 'severity-medium',
  LOW: 'severity-low',
  INFO: 'severity-info'
}

export default function AlertsTable({ alerts }: AlertsTableProps) {
  if (!alerts.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        No recent alerts
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 text-gray-500 font-medium">ID</th>
            <th className="text-left py-3 px-4 text-gray-500 font-medium">Title</th>
            <th className="text-left py-3 px-4 text-gray-500 font-medium">Severity</th>
            <th className="text-left py-3 px-4 text-gray-500 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => (
            <tr key={alert.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4 text-sm text-gray-600">{alert.id}</td>
              <td className="py-3 px-4 text-sm font-medium">{alert.title}</td>
              <td className="py-3 px-4">
                <span className={severityClasses[alert.severity] || severityClasses.INFO}>
                  {alert.severity}
                </span>
              </td>
              <td className="py-3 px-4">
                <button className="text-blue-600 hover:underline text-sm">
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
