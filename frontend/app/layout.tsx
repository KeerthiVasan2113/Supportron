import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Supportron - AI Support Assistant',
  description: 'Your intelligent AI assistant for Linux server configuration, hosting support, and system administration',
  icons: {
    icon: '/icons/favicon.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Skip to main content link for screen readers */}
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-cyan-500 focus:text-white focus:rounded-lg focus:ring-2 focus:ring-cyan-300"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  )
}

