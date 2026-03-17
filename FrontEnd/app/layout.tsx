import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Precedent Brief',
  description: 'AI-powered legal research triage app',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
