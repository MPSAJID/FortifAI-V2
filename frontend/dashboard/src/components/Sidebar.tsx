'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  AlertTriangle, 
  Shield, 
  Activity, 
  Users,
  Settings,
  LogOut,
  Search,
  ChevronLeft,
  ChevronRight,
  Bell,
  HelpCircle,
  Zap
} from 'lucide-react'
import { useAuthStore } from '@/lib/store'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, description: 'Overview & metrics' },
  { name: 'Scanner', href: '/scanner', icon: Search, description: 'URL security analysis' },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle, description: 'Security alerts', badge: 3 },
  { name: 'Threats', href: '/threats', icon: Shield, description: 'Detected threats' },
  { name: 'Analytics', href: '/analytics', icon: Activity, description: 'Reports & insights' },
]

const bottomNavigation = [
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <aside 
      className={`
        relative flex flex-col bg-gray-900 text-white transition-all duration-300 ease-out-expo
        ${isCollapsed ? 'w-20' : 'w-72'}
      `}
    >
      {/* Collapse Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-20 z-10 flex h-6 w-6 items-center justify-center 
                   rounded-full bg-gray-800 border border-gray-700 text-gray-400 
                   hover:bg-gray-700 hover:text-white transition-all duration-200
                   shadow-lg"
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? (
          <ChevronRight className="h-3.5 w-3.5" />
        ) : (
          <ChevronLeft className="h-3.5 w-3.5" />
        )}
      </button>

      {/* Logo */}
      <div className={`flex items-center gap-3 px-6 py-5 border-b border-gray-800 ${isCollapsed ? 'justify-center px-4' : ''}`}>
        <div className="relative">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/25">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-gray-900" />
        </div>
        {!isCollapsed && (
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight">FortifAI</span>
            <span className="text-xs text-gray-500">Security Platform</span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {!isCollapsed && (
        <div className="px-4 py-4 border-b border-gray-800">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-gray-800/50 
                           text-gray-400 text-sm hover:bg-gray-800 hover:text-white transition-colors">
            <Search className="h-4 w-4" />
            <span>Quick search...</span>
            <kbd className="ml-auto text-xs bg-gray-700 px-1.5 py-0.5 rounded">⌘K</kbd>
          </button>
        </div>
      )}

      {/* Main Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <div className={`text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 ${isCollapsed ? 'text-center' : 'px-3'}`}>
          {isCollapsed ? '•' : 'Main Menu'}
        </div>
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`
                    group relative flex items-center gap-3 rounded-lg px-3 py-2.5 
                    font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-600/20'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                >
                  <item.icon className={`h-5 w-5 flex-shrink-0 ${isActive ? '' : 'group-hover:scale-110'} transition-transform`} />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1">{item.name}</span>
                      {item.badge && (
                        <span className="flex h-5 min-w-5 items-center justify-center rounded-full 
                                       bg-red-500 px-1.5 text-xs font-semibold text-white">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                  {isCollapsed && item.badge && (
                    <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center 
                                   rounded-full bg-red-500 px-1 text-2xs font-semibold text-white">
                      {item.badge}
                    </span>
                  )}
                  
                  {/* Tooltip for collapsed state */}
                  {isCollapsed && (
                    <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-gray-800 text-white text-sm 
                                  rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible 
                                  transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
                      {item.name}
                      <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 
                                    border-4 border-transparent border-r-gray-800" />
                    </div>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>

        {/* Divider */}
        <div className="my-4 mx-3 border-t border-gray-800" />

        {/* Bottom Navigation */}
        <div className={`text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 ${isCollapsed ? 'text-center' : 'px-3'}`}>
          {isCollapsed ? '•' : 'Settings'}
        </div>
        <ul className="space-y-1">
          {bottomNavigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`
                    group relative flex items-center gap-3 rounded-lg px-3 py-2.5 
                    font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    }
                    ${isCollapsed ? 'justify-center' : ''}
                  `}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && <span>{item.name}</span>}
                  
                  {isCollapsed && (
                    <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-gray-800 text-white text-sm 
                                  rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible 
                                  transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
                      {item.name}
                    </div>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* System Status */}
      {!isCollapsed && (
        <div className="mx-3 mb-3 p-3 rounded-lg bg-gradient-to-r from-emerald-500/10 to-emerald-600/10 border border-emerald-500/20">
          <div className="flex items-center gap-2 text-sm">
            <div className="status-online animate-pulse" />
            <span className="text-emerald-400 font-medium">System Operational</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">All services running normally</p>
        </div>
      )}

      {/* User section */}
      <div className={`border-t border-gray-800 p-4 ${isCollapsed ? 'px-2' : ''}`}>
        <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''}`}>
          <div className="relative">
            <div className="flex h-10 w-10 items-center justify-center rounded-full 
                          bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-semibold">
              {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
            </div>
            <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-emerald-500 
                          border-2 border-gray-900" />
          </div>
          {!isCollapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {user?.full_name || user?.username || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.email || 'user@fortifai.local'}
                </p>
              </div>
              <button 
                onClick={handleLogout}
                className="p-2 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-lg transition-colors"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
