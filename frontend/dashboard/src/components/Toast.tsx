'use client'

import { useEffect } from 'react'
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import { useToastStore } from '@/lib/store'

const toastConfig = {
  success: {
    icon: CheckCircle,
    bg: 'bg-white',
    border: 'border-emerald-200',
    iconColor: 'text-emerald-500',
    iconBg: 'bg-emerald-50',
    titleColor: 'text-gray-900',
    messageColor: 'text-gray-500',
    progress: 'bg-emerald-500',
  },
  error: {
    icon: XCircle,
    bg: 'bg-white',
    border: 'border-red-200',
    iconColor: 'text-red-500',
    iconBg: 'bg-red-50',
    titleColor: 'text-gray-900',
    messageColor: 'text-gray-500',
    progress: 'bg-red-500',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-white',
    border: 'border-amber-200',
    iconColor: 'text-amber-500',
    iconBg: 'bg-amber-50',
    titleColor: 'text-gray-900',
    messageColor: 'text-gray-500',
    progress: 'bg-amber-500',
  },
  info: {
    icon: Info,
    bg: 'bg-white',
    border: 'border-blue-200',
    iconColor: 'text-blue-500',
    iconBg: 'bg-blue-50',
    titleColor: 'text-gray-900',
    messageColor: 'text-gray-500',
    progress: 'bg-blue-500',
  },
}

export function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-3 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => {
        const config = toastConfig[toast.type]
        const Icon = config.icon

        return (
          <div
            key={toast.id}
            className={`
              pointer-events-auto
              relative overflow-hidden
              flex items-start gap-3 p-4 rounded-xl shadow-lg border
              ${config.bg} ${config.border}
              animate-slide-in
            `}
          >
            {/* Icon */}
            <div className={`flex-shrink-0 p-2 rounded-lg ${config.iconBg}`}>
              <Icon className={`h-5 w-5 ${config.iconColor}`} />
            </div>
            
            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <p className={`font-semibold ${config.titleColor}`}>{toast.title}</p>
              {toast.message && (
                <p className={`text-sm mt-0.5 ${config.messageColor}`}>{toast.message}</p>
              )}
            </div>
            
            {/* Close Button */}
            <button
              onClick={() => removeToast(toast.id)}
              className="flex-shrink-0 p-1.5 -mt-1 -mr-1 text-gray-400 hover:text-gray-600 
                       hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Progress Bar */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 overflow-hidden">
              <div 
                className={`h-full ${config.progress} animate-[shrink_5s_linear_forwards]`}
                style={{ 
                  animation: 'shrink 5s linear forwards',
                }}
              />
            </div>
          </div>
        )
      })}
      
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  )
}

// Hook for easy toast usage
export function useToast() {
  const { addToast } = useToastStore()

  return {
    success: (title: string, message?: string) => 
      addToast({ type: 'success', title, message }),
    error: (title: string, message?: string) => 
      addToast({ type: 'error', title, message }),
    warning: (title: string, message?: string) => 
      addToast({ type: 'warning', title, message }),
    info: (title: string, message?: string) => 
      addToast({ type: 'info', title, message }),
  }
}
