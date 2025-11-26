'use client'

import { useRouter } from 'next/navigation'
import { MessageSquare, Zap, Shield, BookOpen } from 'lucide-react'
import { setSessionItem, StorageKeys } from '@/utils/storage'

export default function LandingPage() {
  const router = useRouter()

  const handleGetStarted = () => {
    // Set flag to start a new chat instead of restoring last one
    setSessionItem(StorageKeys.START_NEW_CHAT, 'true')
    router.push('/chat')
  }

  return (
    <div id="main-content" className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" role="main" tabIndex={-1}>
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <header className="text-center mb-16" role="banner">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 rounded-full mb-6 cyber-glow" aria-hidden="true">
            <MessageSquare className="w-10 h-10 text-cyan-400" aria-hidden="true" />
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-teal-400 to-cyan-300 bg-clip-text text-transparent mb-4">
            Supportron
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Your intelligent AI assistant for Linux server configuration, hosting support, and system administration
          </p>
        </header>

        {/* Features */}
        <section className="grid md:grid-cols-3 gap-8 mb-16 max-w-5xl mx-auto" aria-label="Features">
          <article className="glass-effect-light border border-cyan-500/20 p-6 rounded-lg cyber-glow hover:border-cyan-500/40 transition-all duration-200">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 rounded-lg flex items-center justify-center mb-4" aria-hidden="true">
              <Zap className="w-6 h-6 text-cyan-400" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
              Fast & Accurate
            </h3>
            <p className="text-slate-300">
              Get instant, accurate answers powered by advanced AI and comprehensive documentation
            </p>
          </article>

          <article className="glass-effect-light border border-cyan-500/20 p-6 rounded-lg cyber-glow hover:border-cyan-500/40 transition-all duration-200">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 rounded-lg flex items-center justify-center mb-4" aria-hidden="true">
              <Shield className="w-6 h-6 text-cyan-400" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
              Reliable Support
            </h3>
            <p className="text-slate-300">
              Trusted information from official documentation and best practices
            </p>
          </article>

          <article className="glass-effect-light border border-cyan-500/20 p-6 rounded-lg cyber-glow hover:border-cyan-500/40 transition-all duration-200">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 rounded-lg flex items-center justify-center mb-4" aria-hidden="true">
              <BookOpen className="w-6 h-6 text-cyan-400" aria-hidden="true" />
            </div>
            <h3 className="text-xl font-semibold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
              Comprehensive
            </h3>
            <p className="text-slate-300">
              Covers Linux server configuration, hosting, networking, and system administration
            </p>
          </article>
        </section>

        {/* CTA */}
        <section className="text-center" aria-label="Get started">
          <button
            onClick={handleGetStarted}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                handleGetStarted()
              }
            }}
            aria-label="Get started with Supportron"
            className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-105 cyber-glow-strong focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:ring-offset-2 focus:ring-offset-slate-950"
          >
            <MessageSquare className="w-5 h-5" aria-hidden="true" />
            <span>Get Started</span>
          </button>
        </section>

        {/* Example Questions */}
        <section className="mt-16 max-w-3xl mx-auto" aria-label="Example questions">
          <h2 className="text-2xl font-semibold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent mb-6 text-center">
            Try asking:
          </h2>
          <div className="grid md:grid-cols-2 gap-4" role="list">
            {[
              'How do I configure system settings?',
              'What is Red Hat Enterprise Linux?',
              'How to set up a web server?',
              'How to configure firewall rules?',
            ].map((question, index) => (
              <button
                key={index}
                onClick={() => {
                  router.push(`/chat?q=${encodeURIComponent(question)}`)
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    router.push(`/chat?q=${encodeURIComponent(question)}`)
                  }
                }}
                aria-label={`Ask: ${question}`}
                role="listitem"
                className="text-left p-4 glass-effect-light border border-cyan-500/20 rounded-lg hover:border-cyan-500/40 transition-all duration-200 text-slate-200 hover:text-cyan-300 cyber-glow focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              >
                {question}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

