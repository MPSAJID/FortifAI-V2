import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/Providers'
import { ToastContainer } from '@/components/Toast'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: {
    default: 'FortifAI Security Dashboard',
    template: '%s | FortifAI',
  },
  description: 'AI-Powered Cybersecurity Threat Detection and Response Platform',
  keywords: ['cybersecurity', 'threat detection', 'security', 'AI', 'machine learning', 'UEBA'],
  authors: [{ name: 'FortifAI Team' }],
  creator: 'FortifAI',
  icons: {
    icon: '/favicon.ico',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#2563eb',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          {children}
          <ToastContainer />
        </Providers>
      </body>
    </html>
  )
}
