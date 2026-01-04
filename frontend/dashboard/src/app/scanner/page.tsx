'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { 
  Search, 
  Shield, 
  Globe, 
  Lock, 
  Unlock, 
  Server, 
  Wifi, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Loader2,
  ExternalLink
} from 'lucide-react'
import { api } from '@/lib/api'

interface ScanResult {
  success: boolean
  target?: string
  hostname?: string
  scan_time?: string
  security_score?: number
  security_grade?: string
  ssl_analysis?: {
    enabled: boolean
    valid: boolean
    issuer?: string
    subject?: string
    expires?: string
    days_until_expiry?: number
    protocol?: string
  }
  security_headers?: {
    present_count: number
    total_headers: number
    score: number
    headers: Record<string, { present: boolean; value?: string; recommendation: string }>
  }
  dns_records?: {
    a_records: string[]
    aaaa_records: string[]
    mx_records: string[]
    ns_records: string[]
  }
  technology?: {
    server?: string
    framework?: string
    cms?: string
    cdn?: string
    javascript_libraries: string[]
    analytics: string[]
    detected: string[]
  }
  open_ports?: {
    open_ports: Array<{ port: number; service: string; status: string }>
    scanned: number
  }
  findings?: Array<{ type: string; message: string }>
  error?: string
}

interface UrlInfo {
  protocol: string
  domain_name: string
  subdomain: string
  tld: string
  port: number
  path: string
  ip_address: string
  secure: string
  whois?: {
    registrar: string
    organization: string
    creation_date: string
    expiry_date: string
    domain_age: string
    trust_score: number
    risk_level: string
  }
}

const gradeColors: Record<string, string> = {
  'A+': 'text-green-600 bg-green-100',
  'A': 'text-green-600 bg-green-100',
  'B': 'text-blue-600 bg-blue-100',
  'C': 'text-yellow-600 bg-yellow-100',
  'D': 'text-orange-600 bg-orange-100',
  'F': 'text-red-600 bg-red-100',
}

const riskColors: Record<string, string> = {
  'Low': 'text-green-600 bg-green-50',
  'Medium': 'text-yellow-600 bg-yellow-50',
  'High': 'text-orange-600 bg-orange-50',
  'Critical': 'text-red-600 bg-red-50',
}

export default function ScannerPage() {
  const [url, setUrl] = useState('')
  const [scanType, setScanType] = useState<'quick' | 'deep' | 'extract'>('deep')
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [urlInfo, setUrlInfo] = useState<UrlInfo | null>(null)

  const deepScanMutation = useMutation({
    mutationFn: (url: string) => api.deepScanUrl(url),
    onSuccess: (data) => {
      setScanResult(data)
      setUrlInfo(null)
    },
  })

  const quickScanMutation = useMutation({
    mutationFn: (url: string) => api.quickScanUrl(url),
    onSuccess: (data) => {
      setScanResult(data)
      setUrlInfo(null)
    },
  })

  const extractMutation = useMutation({
    mutationFn: (url: string) => api.extractUrl(url),
    onSuccess: (data) => {
      if (data.success) {
        setUrlInfo(data.data)
        setScanResult(null)
      }
    },
  })

  const isLoading = deepScanMutation.isPending || quickScanMutation.isPending || extractMutation.isPending

  const handleScan = () => {
    if (!url.trim()) return
    
    setScanResult(null)
    setUrlInfo(null)
    
    switch (scanType) {
      case 'deep':
        deepScanMutation.mutate(url)
        break
      case 'quick':
        quickScanMutation.mutate(url)
        break
      case 'extract':
        extractMutation.mutate(url)
        break
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleScan()
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Security Scanner</h1>
        <p className="text-gray-500 mt-1">
          Scan URLs and domains for security vulnerabilities and intelligence gathering
        </p>
      </div>

      {/* Scanner Input */}
      <div className="card">
        <div className="space-y-4">
          {/* Scan Type Selection */}
          <div className="flex gap-4">
            <button
              onClick={() => setScanType('deep')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                scanType === 'deep'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Shield className="inline-block w-4 h-4 mr-2" />
              Deep Scan
            </button>
            <button
              onClick={() => setScanType('quick')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                scanType === 'quick'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Search className="inline-block w-4 h-4 mr-2" />
              Quick Scan
            </button>
            <button
              onClick={() => setScanType('extract')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                scanType === 'extract'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Globe className="inline-block w-4 h-4 mr-2" />
              URL Info
            </button>
          </div>

          {/* URL Input */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter URL to scan (e.g., https://example.com)"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleScan}
              disabled={isLoading || !url.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Search className="h-5 w-5" />
                  Scan
                </>
              )}
            </button>
          </div>

          {/* Scan Type Description */}
          <p className="text-sm text-gray-500">
            {scanType === 'deep' && 'Comprehensive security analysis including SSL, headers, ports, and technology detection.'}
            {scanType === 'quick' && 'Fast security check focusing on SSL certificate and security headers.'}
            {scanType === 'extract' && 'Extract URL components, WHOIS data, and domain intelligence.'}
          </p>
        </div>
      </div>

      {/* Scan Results */}
      {scanResult && (
        <div className="space-y-6">
          {/* Security Score Card */}
          {scanResult.security_score !== undefined && (
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">Security Analysis</h2>
                  <p className="text-gray-500">{scanResult.target}</p>
                </div>
                <div className="text-center">
                  <div className={`inline-block px-6 py-3 rounded-xl text-3xl font-bold ${gradeColors[scanResult.security_grade || 'F']}`}>
                    {scanResult.security_grade}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Score: {scanResult.security_score}/100</p>
                </div>
              </div>
            </div>
          )}

          {/* Findings */}
          {scanResult.findings && scanResult.findings.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Findings</h3>
              <div className="space-y-2">
                {scanResult.findings.map((finding, index) => (
                  <div
                    key={index}
                    className={`flex items-center gap-3 p-3 rounded-lg ${
                      finding.type === 'success' ? 'bg-green-50' :
                      finding.type === 'warning' ? 'bg-yellow-50' :
                      finding.type === 'danger' ? 'bg-red-50' : 'bg-blue-50'
                    }`}
                  >
                    {finding.type === 'success' && <CheckCircle className="h-5 w-5 text-green-600" />}
                    {finding.type === 'warning' && <AlertTriangle className="h-5 w-5 text-yellow-600" />}
                    {finding.type === 'danger' && <XCircle className="h-5 w-5 text-red-600" />}
                    {finding.type === 'info' && <Info className="h-5 w-5 text-blue-600" />}
                    <span className={
                      finding.type === 'success' ? 'text-green-700' :
                      finding.type === 'warning' ? 'text-yellow-700' :
                      finding.type === 'danger' ? 'text-red-700' : 'text-blue-700'
                    }>
                      {finding.message}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SSL Analysis */}
          {scanResult.ssl_analysis && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                {scanResult.ssl_analysis.valid ? (
                  <Lock className="h-5 w-5 text-green-600" />
                ) : (
                  <Unlock className="h-5 w-5 text-red-600" />
                )}
                SSL/TLS Certificate
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <p className={`font-medium ${scanResult.ssl_analysis.valid ? 'text-green-600' : 'text-red-600'}`}>
                    {scanResult.ssl_analysis.valid ? 'Valid' : 'Invalid'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Issuer</p>
                  <p className="font-medium">{scanResult.ssl_analysis.issuer || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expires</p>
                  <p className="font-medium">{scanResult.ssl_analysis.expires || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Protocol</p>
                  <p className="font-medium">{scanResult.ssl_analysis.protocol || 'N/A'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Security Headers */}
          {scanResult.security_headers && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Server className="h-5 w-5 text-blue-600" />
                Security Headers ({scanResult.security_headers.present_count}/{scanResult.security_headers.total_headers})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(scanResult.security_headers.headers || {}).map(([header, data]) => (
                  <div
                    key={header}
                    className={`p-3 rounded-lg ${data.present ? 'bg-green-50' : 'bg-red-50'}`}
                  >
                    <div className="flex items-center gap-2">
                      {data.present ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                      <span className="font-medium text-sm">{header}</span>
                    </div>
                    {!data.present && (
                      <p className="text-xs text-gray-500 mt-1">{data.recommendation}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Open Ports */}
          {scanResult.open_ports && scanResult.open_ports.open_ports.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Wifi className="h-5 w-5 text-purple-600" />
                Open Ports ({scanResult.open_ports.open_ports.length} found)
              </h3>
              <div className="flex flex-wrap gap-2">
                {scanResult.open_ports.open_ports.map((port) => (
                  <span
                    key={port.port}
                    className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm font-medium"
                  >
                    {port.port} ({port.service})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Technology Detection */}
          {scanResult.technology && scanResult.technology.detected.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Detected Technologies</h3>
              <div className="flex flex-wrap gap-2">
                {scanResult.technology.detected.map((tech, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* DNS Records */}
          {scanResult.dns_records && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">DNS Records</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scanResult.dns_records.a_records.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">A Records (IPv4)</p>
                    <div className="flex flex-wrap gap-1">
                      {scanResult.dns_records.a_records.map((ip) => (
                        <span key={ip} className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">{ip}</span>
                      ))}
                    </div>
                  </div>
                )}
                {scanResult.dns_records.mx_records.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">MX Records</p>
                    <div className="flex flex-wrap gap-1">
                      {scanResult.dns_records.mx_records.map((mx) => (
                        <span key={mx} className="px-2 py-1 bg-gray-100 rounded text-sm">{mx}</span>
                      ))}
                    </div>
                  </div>
                )}
                {scanResult.dns_records.ns_records.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">NS Records</p>
                    <div className="flex flex-wrap gap-1">
                      {scanResult.dns_records.ns_records.map((ns) => (
                        <span key={ns} className="px-2 py-1 bg-gray-100 rounded text-sm">{ns}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* URL Info Results */}
      {urlInfo && (
        <div className="space-y-6">
          {/* URL Components */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">URL Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">Protocol</p>
                <p className="font-medium">{urlInfo.protocol}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Domain</p>
                <p className="font-medium">{urlInfo.domain_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Subdomain</p>
                <p className="font-medium">{urlInfo.subdomain}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">TLD</p>
                <p className="font-medium">{urlInfo.tld}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Port</p>
                <p className="font-medium">{urlInfo.port}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">IP Address</p>
                <p className="font-medium font-mono">{urlInfo.ip_address}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Secure</p>
                <p className={`font-medium ${urlInfo.secure === 'Yes' ? 'text-green-600' : 'text-red-600'}`}>
                  {urlInfo.secure}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Path</p>
                <p className="font-medium">{urlInfo.path}</p>
              </div>
            </div>
          </div>

          {/* WHOIS Information */}
          {urlInfo.whois && urlInfo.whois.registrar !== 'Not Available' && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Domain Intelligence</h3>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskColors[urlInfo.whois.risk_level] || 'bg-gray-100'}`}>
                  {urlInfo.whois.risk_level} Risk
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Registrar</p>
                  <p className="font-medium">{urlInfo.whois.registrar}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Organization</p>
                  <p className="font-medium">{urlInfo.whois.organization}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Created</p>
                  <p className="font-medium">{urlInfo.whois.creation_date}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expires</p>
                  <p className="font-medium">{urlInfo.whois.expiry_date}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Domain Age</p>
                  <p className="font-medium">{urlInfo.whois.domain_age}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Trust Score</p>
                  <p className="font-medium">{urlInfo.whois.trust_score}/100</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {(deepScanMutation.isError || quickScanMutation.isError || extractMutation.isError) && (
        <div className="card bg-red-50 border border-red-200">
          <div className="flex items-center gap-3">
            <XCircle className="h-6 w-6 text-red-600" />
            <div>
              <p className="font-medium text-red-800">Scan Failed</p>
              <p className="text-sm text-red-600">
                {(deepScanMutation.error || quickScanMutation.error || extractMutation.error)?.message || 
                 'An error occurred while scanning the URL'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
