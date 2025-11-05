'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { ChatSession, Message } from '@/types/user'
import { useAuth } from './AuthContext'

interface ChatContextType {
  sessions: ChatSession[]
  currentSession: ChatSession | null
  createNewSession: () => void
  selectSession: (sessionId: string) => void
  addMessage: (content: string, role: 'user' | 'assistant') => void
  updateSessionTitle: (sessionId: string, title: string) => void
  deleteSession: (sessionId: string) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

const STORAGE_KEY = 'supportron_chat_sessions'

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)

  useEffect(() => {
    if (!user) return

    const stored = localStorage.getItem(`${STORAGE_KEY}_${user.id}`)
    if (stored) {
      const parsed = JSON.parse(stored)
      setSessions(parsed)
      if (parsed.length > 0) {
        setCurrentSession(parsed[0])
      }
    }
  }, [user])

  const saveSessions = (newSessions: ChatSession[]) => {
    if (!user) return
    setSessions(newSessions)
    localStorage.setItem(`${STORAGE_KEY}_${user.id}`, JSON.stringify(newSessions))
  }

  const createNewSession = () => {
    if (!user) return

    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      userId: user.id,
      title: `Chat ${sessions.length + 1}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messages: []
    }

    const newSessions = [newSession, ...sessions]
    saveSessions(newSessions)
    setCurrentSession(newSession)
  }

  const selectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSession(session)
    }
  }

  const addMessage = (content: string, role: 'user' | 'assistant') => {
    if (!user) return

    setCurrentSession(prevSession => {
      if (!prevSession) return prevSession

      const newMessage: Message = {
        role,
        content,
        timestamp: new Date().toISOString()
      }

      const updatedSession: ChatSession = {
        ...prevSession,
        messages: [...prevSession.messages, newMessage],
        updatedAt: new Date().toISOString()
      }

      setSessions(prevSessions => {
        const updatedSessions = prevSessions.map(s =>
          s.id === prevSession.id ? updatedSession : s
        )
        if (user) {
          localStorage.setItem(`${STORAGE_KEY}_${user.id}`, JSON.stringify(updatedSessions))
        }
        return updatedSessions
      })

      return updatedSession
    })
  }

  const updateSessionTitle = (sessionId: string, title: string) => {
    const updatedSessions = sessions.map(s =>
      s.id === sessionId ? { ...s, title } : s
    )
    saveSessions(updatedSessions)
    if (currentSession?.id === sessionId) {
      setCurrentSession({ ...currentSession, title })
    }
  }

  const deleteSession = (sessionId: string) => {
    const updatedSessions = sessions.filter(s => s.id !== sessionId)
    saveSessions(updatedSessions)
    if (currentSession?.id === sessionId) {
      setCurrentSession(updatedSessions[0] || null)
    }
  }

  return (
    <ChatContext.Provider
      value={{
        sessions,
        currentSession,
        createNewSession,
        selectSession,
        addMessage,
        updateSessionTitle,
        deleteSession
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export const useChatContext = () => {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider')
  }
  return context
}

