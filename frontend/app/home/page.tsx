'use client'

import { useRouter } from 'next/navigation'
import { MessageSquare, Zap, Shield, BookOpen, Users, Sparkles } from 'lucide-react'

export default function HomePage() {
  const router = useRouter()

  const handleGetStarted = () => {
    sessionStorage.setItem('startNewChat', 'true')
    router.push('/chat')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-200">
      <div className="container mx-auto px-6 py-20">
        <header className="flex flex-col lg:flex-row items-center gap-8 mb-12">
          <div className="flex-shrink-0">
            <div className="w-28 h-28 rounded-full bg-gradient-to-br from-cyan-500/10 to-teal-500/10 border border-cyan-500/20 flex items-center justify-center shadow-lg">
              <MessageSquare className="w-12 h-12 text-cyan-400" />
            </div>
          </div>

          <div className="flex-1 text-center lg:text-left">
            <h1 className="text-5xl font-extrabold leading-tight mb-3 bg-gradient-to-r from-cyan-400 via-teal-400 to-cyan-300 bg-clip-text text-transparent">
              Supportron — AI for Linux & Server Support
            </h1>
            <p className="text-lg text-slate-300 max-w-2xl">
              Empowered by local Ollama models and RAG docs. Fast answers, accurate guidance, and curated documentation — without sending your data to the cloud.
            </p>

            <div className="mt-6 flex items-center justify-center lg:justify-start gap-4">
              <button
                onClick={handleGetStarted}
                className="inline-flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-white font-semibold rounded-lg shadow-lg transition-transform transform hover:-translate-y-0.5"
              >
                <Sparkles className="w-5 h-5" />
                <span>Get Started</span>
              </button>

              <a
                href="#features"
                className="inline-flex items-center px-4 py-3 text-sm bg-slate-800/50 rounded-lg border border-slate-700 hover:bg-slate-800/70 transition"
              >
                Learn More
              </a>
            </div>
          </div>
        </header>

        {/* Features */}
        <section id="features" className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="glass-effect-light border border-cyan-500/10 p-6 rounded-xl hover:shadow-xl transition">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/10 to-teal-500/10 border border-cyan-500/20 rounded-lg flex items-center justify-center mb-3">
              <Zap className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-lg font-semibold mb-1">Fast & Accurate</h3>
            <p className="text-slate-300 text-sm">Instant answers powered by local LLMs and curated documentation for reliable results.</p>
          </div>

          <div className="glass-effect-light border border-cyan-500/10 p-6 rounded-xl hover:shadow-xl transition">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/10 to-teal-500/10 border border-cyan-500/20 rounded-lg flex items-center justify-center mb-3">
              <Shield className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-lg font-semibold mb-1">Private & Local</h3>
            <p className="text-slate-300 text-sm">Run models on your machine with Ollama — data never leaves your environment.</p>
          </div>

          <div className="glass-effect-light border border-cyan-500/10 p-6 rounded-xl hover:shadow-xl transition">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-500/10 to-teal-500/10 border border-cyan-500/20 rounded-lg flex items-center justify-center mb-3">
              <BookOpen className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-lg font-semibold mb-1">Documentation Aware</h3>
            <p className="text-slate-300 text-sm">RAG-powered answers that reference exact documentation snippets when available.</p>
          </div>
        </section>

        {/* Product Highlights */}
        <section className="mb-12 grid md:grid-cols-2 gap-8 items-center">
          <div className="p-6 rounded-xl bg-gradient-to-br from-slate-900/40 to-slate-900/30 border border-slate-800 shadow-md">
            <h3 className="text-2xl font-bold mb-2">Built for operators</h3>
            <p className="text-slate-300 mb-4">Supportron is designed to help system administrators and DevOps engineers find precise, actionable guidance — fast. Use it for configuration steps, troubleshooting, and command examples.</p>

            <ul className="space-y-2">
              <li className="flex items-start gap-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded bg-cyan-700/20 text-cyan-400">✓</span>
                <span className="text-slate-300 text-sm">Accurate command-level examples</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded bg-cyan-700/20 text-cyan-400">✓</span>
                <span className="text-slate-300 text-sm">Policy-friendly, AWS/Red Hat best practices</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded bg-cyan-700/20 text-cyan-400">✓</span>
                <span className="text-slate-300 text-sm">Offline-first workflow with local embeddings</span>
              </li>
            </ul>
          </div>

          <div className="p-6 rounded-xl bg-gradient-to-br from-slate-950/20 border border-slate-800 shadow-inner text-slate-200">
            <h4 className="text-lg font-semibold mb-2">Try examples</h4>
            <div className="grid grid-cols-1 gap-3">
              {[
                'How do I configure system settings?',
                'How to set up a web server?',
                'How to configure firewall rules?',
              ].map((q, i) => (
                <button key={i} onClick={() => router.push(`/chat?q=${encodeURIComponent(q)}`)} className="text-left p-3 bg-slate-900/40 rounded hover:bg-slate-900/60 transition">{q}</button>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials / Trust */}
        <section className="mb-12 text-center">
          <div className="max-w-3xl mx-auto">
            <h3 className="text-2xl font-bold mb-4">Loved by operators</h3>
            <p className="text-slate-300 mb-6">"Saved us hours debugging system issues — the responses are concise and accurate." — Infrastructure Team</p>
            <div className="flex items-center justify-center gap-6">
              <div className="text-center">
                <Users className="w-10 h-10 mx-auto text-cyan-400" />
                <div className="text-sm text-slate-300 mt-2">Enterprise-ready</div>
              </div>
              <div className="text-center">
                <Sparkles className="w-10 h-10 mx-auto text-cyan-400" />
                <div className="text-sm text-slate-300 mt-2">Local-first</div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="pt-12 border-t border-slate-800 text-center text-sm text-slate-400">
          <div className="max-w-2xl mx-auto">© {new Date().getFullYear()} Supportron — Local AI for system admins.</div>
        </footer>
      </div>
    </div>
  )
}
