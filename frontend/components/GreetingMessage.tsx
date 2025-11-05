'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useEffect, useState } from 'react'

export const GreetingMessage = () => {
  const { user } = useAuth()
  const [showGreeting, setShowGreeting] = useState(false)

  useEffect(() => {
    const hasSeenGreeting = sessionStorage.getItem('hasSeenGreeting')
    if (!hasSeenGreeting && user) {
      setShowGreeting(true)
      sessionStorage.setItem('hasSeenGreeting', 'true')
      setTimeout(() => setShowGreeting(false), 5000)
    }
  }, [user])

  if (!showGreeting || !user) return null

  return (
    <div className="fixed top-4 right-4 z-50 glass-effect rounded-xl p-4 tech-border animate-pulse">
      <p className="text-text-primary">
        Welcome back, <span className="text-neon-cyan font-semibold">{user.name}</span>!
      </p>
    </div>
  )
}

