import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Supportron - AI Support Assistant',
    template: '%s | Supportron',
  },
  description: 'Your intelligent AI assistant for Linux server configuration, hosting support, and system administration',
  keywords: ['AI assistant', 'Linux support', 'server configuration', 'system administration', 'RAG', 'Ollama', 'local AI'],
  authors: [{ name: 'Supportron' }],
  creator: 'Supportron',
  publisher: 'Supportron',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: process.env.NEXT_PUBLIC_SITE_URL 
    ? new URL(process.env.NEXT_PUBLIC_SITE_URL)
    : undefined,
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: process.env.NEXT_PUBLIC_SITE_URL,
    siteName: 'Supportron',
    title: 'Supportron - AI Support Assistant',
    description: 'Your intelligent AI assistant for Linux server configuration, hosting support, and system administration',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Supportron - AI Support Assistant',
    description: 'Your intelligent AI assistant for Linux server configuration, hosting support, and system administration',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/icons/favicon.png',
    apple: '/icons/favicon.png',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
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

