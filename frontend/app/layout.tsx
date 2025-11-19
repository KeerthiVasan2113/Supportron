import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Supportron - AI Support Assistant',
  description: 'Your intelligent AI assistant for Linux server configuration, hosting support, and system administration',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}

