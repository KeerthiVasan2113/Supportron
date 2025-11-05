'use client'

import { useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const success = await login(email, password)
    
    if (success) {
      router.push('/dashboard')
    } else {
      setError('Invalid email or password')
    }
    
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-tech-dark relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-neon-cyan/10 via-accent/10 to-neon-purple/10 animate-gradient"></div>
      
      <div className="relative z-10 w-full max-w-md p-8">
        <div className="glass-effect rounded-2xl p-8 space-y-6 tech-border">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-neon-cyan mb-2 animate-glow-cyan">
              SUPPORTRON
            </h1>
            <p className="text-text-secondary">IT Tech Support System</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-3 focus:outline-none focus:border-neon-cyan focus:ring-2 focus:ring-neon-cyan/50 transition-all"
                placeholder="Enter your email"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl px-4 py-3 focus:outline-none focus:border-neon-cyan focus:ring-2 focus:ring-neon-cyan/50 transition-all"
                placeholder="Enter your password"
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-br from-neon-cyan to-cyber-blue text-white font-semibold py-3 rounded-xl hover:from-neon-cyan/90 hover:to-cyber-blue/90 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed neon-glow"
            >
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

