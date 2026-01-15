'use client'

import { useState, useEffect } from 'react'
import { 
  Bell, 
  Search, 
  Command,
  Sun,
  Moon,
  User,
  Settings,
  LogOut,
  HelpCircle,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react'
import { useAuthStore, useDashboardStore } from '@/lib/store'
import { format } from 'date-fns'

interface HeaderProps {
  title?: string
  subtitle?: string
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const { user, logout } = useAuthStore()
  const { isConnected, lastUpdate } = useDashboardStore()

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowNotifications(false)
      setShowProfile(false)
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  const notifications = [
    { id: 1, type: 'critical', title: 'Critical Alert', message: 'Suspicious login attempt detected', time: '2 min ago' },
    { id: 2, type: 'warning', title: 'High CPU Usage', message: 'Server load exceeded 90%', time: '15 min ago' },
    { id: 3, type: 'info', title: 'Scan Complete', message: 'URL scan finished successfully', time: '1 hour ago' },
  ]

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-gray-200/50">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left section - Title & Breadcrumb */}
        <div className="flex items-center gap-4">
          {title && (
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
              {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
            </div>
          )}
        </div>

        {/* Center section - Search */}
        <div className="hidden lg:flex flex-1 max-w-xl mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search alerts, threats, or users..."
              className="w-full pl-10 pr-12 py-2 bg-gray-100 border-0 rounded-lg text-sm 
                       placeholder:text-gray-400 focus:bg-white focus:ring-2 focus:ring-blue-500/20 
                       focus:outline-none transition-all duration-200"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-0.5">
              <kbd className="text-xs text-gray-400 bg-gray-200 px-1.5 py-0.5 rounded">⌘</kbd>
              <kbd className="text-xs text-gray-400 bg-gray-200 px-1.5 py-0.5 rounded">K</kbd>
            </div>
          </div>
        </div>

        {/* Right section - Actions */}
        <div className="flex items-center gap-2">
          {/* Connection Status */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100">
            {isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-emerald-500" />
                <span className="text-xs text-gray-600">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-gray-400" />
                <span className="text-xs text-gray-500">Offline</span>
              </>
            )}
          </div>

          {/* Last Updated */}
          {lastUpdate && (
            <div className="hidden xl:flex items-center gap-1.5 text-xs text-gray-500">
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Updated {format(new Date(lastUpdate), 'HH:mm')}</span>
            </div>
          )}

          {/* Divider */}
          <div className="hidden md:block h-6 w-px bg-gray-200 mx-2" />

          {/* Time Display */}
          <div className="hidden md:block text-sm text-gray-600 font-medium">
            {format(currentTime, 'EEE, MMM d • HH:mm')}
          </div>

          {/* Divider */}
          <div className="hidden md:block h-6 w-px bg-gray-200 mx-2" />

          {/* Notifications */}
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => {
                setShowNotifications(!showNotifications)
                setShowProfile(false)
              }}
              className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 
                       rounded-lg transition-colors"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center 
                             rounded-full bg-red-500 text-2xs font-semibold text-white">
                3
              </span>
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-soft-lg 
                            border border-gray-200 overflow-hidden animate-scale-in">
                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">Notifications</h3>
                    <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">
                      Mark all read
                    </button>
                  </div>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className="px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors 
                               border-b border-gray-100 last:border-0"
                    >
                      <div className="flex gap-3">
                        <div className={`
                          mt-0.5 w-2 h-2 rounded-full flex-shrink-0
                          ${notification.type === 'critical' ? 'bg-red-500' : ''}
                          ${notification.type === 'warning' ? 'bg-amber-500' : ''}
                          ${notification.type === 'info' ? 'bg-blue-500' : ''}
                        `} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                          <p className="text-xs text-gray-500 mt-0.5 truncate">{notification.message}</p>
                          <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
                  <a href="/alerts" className="block text-center text-sm text-blue-600 
                                              hover:text-blue-700 font-medium">
                    View all notifications
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Profile Dropdown */}
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => {
                setShowProfile(!showProfile)
                setShowNotifications(false)
              }}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 
                            flex items-center justify-center text-white text-sm font-medium">
                {user?.full_name?.charAt(0) || user?.username?.charAt(0) || 'U'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-900">
                  {user?.full_name || user?.username || 'User'}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user?.role || 'Admin'}</p>
              </div>
            </button>

            {/* Profile Dropdown */}
            {showProfile && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-soft-lg 
                            border border-gray-200 overflow-hidden animate-scale-in">
                <div className="px-4 py-3 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.full_name || user?.username}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>
                <div className="py-1">
                  <a href="/profile" className="flex items-center gap-3 px-4 py-2.5 text-sm 
                                               text-gray-700 hover:bg-gray-50 transition-colors">
                    <User className="h-4 w-4 text-gray-400" />
                    Your Profile
                  </a>
                  <a href="/settings" className="flex items-center gap-3 px-4 py-2.5 text-sm 
                                                text-gray-700 hover:bg-gray-50 transition-colors">
                    <Settings className="h-4 w-4 text-gray-400" />
                    Settings
                  </a>
                  <a href="/help" className="flex items-center gap-3 px-4 py-2.5 text-sm 
                                            text-gray-700 hover:bg-gray-50 transition-colors">
                    <HelpCircle className="h-4 w-4 text-gray-400" />
                    Help & Support
                  </a>
                </div>
                <div className="border-t border-gray-100 py-1">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm 
                             text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
