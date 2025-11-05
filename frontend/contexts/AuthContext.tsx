'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User } from '@/types/user'

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const STORAGE_KEY = 'supportron_users'
const SESSION_KEY = 'supportron_session'

const defaultAdmin: User = {
  id: 'admin-1',
  name: 'Keerthi Vasan',
  email: 'keerthivasan.g@armiasystems.com',
  password: 'Keerthi@55',
  role: 'admin',
  createdAt: new Date().toISOString()
}

const initializeUsers = (): User[] => {
  if (typeof window === 'undefined') return [defaultAdmin]
  
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    return JSON.parse(stored)
  }
  
  const users = [defaultAdmin]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users))
  return users
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return
    
    initializeUsers()
    
    const session = localStorage.getItem(SESSION_KEY)
    if (session) {
      try {
        const userData = JSON.parse(session)
        setUser(userData)
      } catch (e) {
        localStorage.removeItem(SESSION_KEY)
      }
    }
    
    setIsInitialized(true)
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    const users = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    const foundUser = users.find((u: User) => u.email === email && u.password === password)
    
    if (foundUser) {
      const { password: _, ...userWithoutPassword } = foundUser
      setUser(foundUser)
      localStorage.setItem(SESSION_KEY, JSON.stringify(foundUser))
      return true
    }
    
    return false
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem(SESSION_KEY)
  }

  if (!isInitialized) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin'
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

