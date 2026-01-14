'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Shield, Eye, EyeOff, Loader2, Lock, User, ArrowRight, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/lib/store'
import { useToast } from '@/components/Toast'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const { login, isLoading } = useAuthStore()
  const toast = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      await login(username, password)
      toast.success('Welcome back!', 'Login successful')
      router.push('/')
    } catch (err: any) {
      const message = err.message || 'Login failed. Please try again.'
      setError(message)
      toast.error('Authentication failed', message)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-gray-900 via-gray-900 to-blue-900 
                    relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] 
                        bg-gradient-to-br from-blue-600/10 to-transparent rounded-full blur-3xl" />
        </div>
        
        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />
        
        {/* Content */}
        <div className="relative flex flex-col justify-center px-12 xl:px-20">
          <div className="max-w-lg">
            {/* Logo */}
            <div className="flex items-center gap-4 mb-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl 
                            bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30">
                <Shield className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">FortifAI</h1>
                <p className="text-blue-400 text-sm">Security Platform</p>
              </div>
            </div>
            
            {/* Tagline */}
            <h2 className="text-4xl xl:text-5xl font-bold text-white leading-tight mb-6">
              AI-Powered
              <span className="block text-transparent bg-clip-text bg-gradient-to-r 
                             from-blue-400 to-cyan-400">
                Threat Detection
              </span>
            </h2>
            
            <p className="text-lg text-gray-400 mb-10 leading-relaxed">
              Protect your infrastructure with advanced machine learning algorithms 
              that detect and respond to cyber threats in real-time.
            </p>
            
            {/* Features */}
            <div className="space-y-4">
              {[
                'Real-time threat monitoring & analytics',
                'Advanced URL & domain scanning',
                'User behavior analytics (UEBA)',
                'Multi-channel alert notifications'
              ].map((feature, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full 
                                bg-blue-500/20 text-blue-400">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                  <span className="text-gray-300">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex flex-col justify-center bg-gray-50 px-6 py-12 lg:px-12 xl:px-20">
        <div className="w-full max-w-md mx-auto">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-10">
            <div className="inline-flex items-center justify-center p-4 bg-gradient-to-br 
                          from-blue-500 to-blue-600 rounded-2xl mb-4 shadow-lg shadow-blue-500/30">
              <Shield className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">FortifAI</h1>
            <p className="text-gray-500">Security Platform</p>
          </div>

          {/* Form Header */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
            <p className="text-gray-500 mt-2">Sign in to access your security dashboard</p>
          </div>
          
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <div className="flex-shrink-0 w-5 h-5 rounded-full bg-red-100 flex items-center justify-center mt-0.5">
                <span className="text-red-600 text-xs">!</span>
              </div>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 
                           text-gray-900 placeholder-gray-400 
                           focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500
                           transition-all duration-200"
                  placeholder="Enter your username"
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white border border-gray-200 rounded-xl pl-12 pr-12 py-3.5 
                           text-gray-900 placeholder-gray-400 
                           focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500
                           transition-all duration-200"
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 
                           hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2.5 cursor-pointer">
                <input 
                  type="checkbox" 
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 
                           focus:ring-blue-500 focus:ring-offset-0" 
                />
                <span className="text-sm text-gray-600">Remember me</span>
              </label>
              <a href="#" className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r 
                       from-blue-600 to-blue-700 text-white py-3.5 rounded-xl font-semibold 
                       hover:from-blue-700 hover:to-blue-800 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 
                       disabled:opacity-50 disabled:cursor-not-allowed 
                       transition-all duration-200 shadow-lg shadow-blue-500/25"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight className="h-5 w-5" />
                </>
              )}
            </button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-100 rounded-xl">
            <p className="text-sm text-blue-800 font-medium mb-2">Demo Credentials</p>
            <div className="flex gap-4 text-sm text-blue-600">
              <span className="font-mono bg-blue-100 px-2 py-1 rounded">admin</span>
              <span className="font-mono bg-blue-100 px-2 py-1 rounded">admin123</span>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-gray-500 mt-8">
            Protected by FortifAI Security • v1.0.0
          </p>
        </div>
      </div>
    </div>
  )
}
