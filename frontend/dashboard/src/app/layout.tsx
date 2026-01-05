import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/Providers'
import Sidebar from '@/components/Sidebar'
import { AuthGuard } from '@/components/AuthGuard'
import { ToastContainer } from '@/components/Toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'FortifAI Security Dashboard',
  description: 'AI-Powered Cybersecurity Threat Detection',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <AuthGuard>
            <div className="flex h-screen bg-gray-100">
              <Sidebar />
              <main className="flex-1 overflow-y-auto p-8">
                {children}
              </main>
            </div>
          </AuthGuard>
          <ToastContainer />
        </Providers>
      </body>
    </html>
  )
}
