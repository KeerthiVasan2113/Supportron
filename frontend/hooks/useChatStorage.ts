'use client'

import { useState, useEffect, useRef } from 'react'
import { Message } from '@/types/chat'

export interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  greetingSent?: boolean
}

const STORAGE_KEY = 'supportron_chats'

export const useChatStorage = () => {
  const [chatHistory, setChatHistory] = useState<Chat[]>([])
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const hasLoadedFromStorage = useRef(false)

  // Load chats from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length > 0) {
          const chats = parsed.map((chat: any) => ({
            ...chat,
            messages: chat.messages?.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            })) || [],
            createdAt: new Date(chat.createdAt),
            updatedAt: new Date(chat.updatedAt),
          }))
          setChatHistory(chats)
          hasLoadedFromStorage.current = true
          
          // Restore last active chat if available
          const lastChatId = localStorage.getItem('supportron_last_chat_id')
          if (lastChatId) {
            const chatExists = chats.find((c: Chat) => c.id === lastChatId)
            if (chatExists) {
              setCurrentChatId(lastChatId)
            } else {
              // Last chat ID doesn't exist, use most recent chat
              if (chats.length > 0) {
                const mostRecent = chats.sort((a: Chat, b: Chat) => 
                  new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
                )[0]
                setCurrentChatId(mostRecent.id)
                localStorage.setItem('supportron_last_chat_id', mostRecent.id)
              }
            }
          } else if (chats.length > 0) {
            // No last chat ID, use most recent chat
            const mostRecent = chats.sort((a: Chat, b: Chat) => 
              new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
            )[0]
            setCurrentChatId(mostRecent.id)
            localStorage.setItem('supportron_last_chat_id', mostRecent.id)
          }
        } else {
          hasLoadedFromStorage.current = true
        }
      } else {
        hasLoadedFromStorage.current = true
      }
    } catch (error) {
      console.error('Error loading chats from storage:', error)
      hasLoadedFromStorage.current = true
    }
  }, [])
  
  // Save chats to localStorage whenever chatHistory changes
  useEffect(() => {
    // Don't save until we've loaded from storage (prevents overwriting on initial mount)
    if (!hasLoadedFromStorage.current) {
      return
    }
    
    try {
      // Serialize dates properly
      const serialized = chatHistory.map((chat) => ({
        ...chat,
        messages: chat.messages.map((msg) => ({
          ...msg,
          timestamp: msg.timestamp.toISOString(),
        })),
        createdAt: chat.createdAt.toISOString(),
        updatedAt: chat.updatedAt.toISOString(),
      }))
      
      if (chatHistory.length > 0) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized))
      } else {
        // Only remove if explicitly cleared by user (after initial load)
        localStorage.removeItem(STORAGE_KEY)
      }
      
      if (currentChatId) {
        localStorage.setItem('supportron_last_chat_id', currentChatId)
      } else {
        localStorage.removeItem('supportron_last_chat_id')
      }
    } catch (error) {
      console.error('Error saving chats to storage:', error)
      // Handle quota exceeded error
      if (error instanceof Error && error.name === 'QuotaExceededError') {
        console.warn('localStorage quota exceeded. Consider clearing old chats.')
      }
    }
  }, [chatHistory, currentChatId])

  const createChat = (messages: Message[]): string => {
    const newChatId = Date.now().toString()
    // Keep "New Chat" until first user message is sent
    const firstUserMessage = messages.find(msg => msg.role === 'user')
    const title = firstUserMessage 
      ? firstUserMessage.content.substring(0, 50).trim() || 'New Chat'
      : 'New Chat'
    const now = new Date()
    
    // Check if first message is a greeting (assistant message)
    const isGreetingChat = messages.length === 1 && messages[0]?.role === 'assistant'
    
    const newChat: Chat = {
      id: newChatId,
      title,
      messages,
      createdAt: now,
      updatedAt: now,
      greetingSent: isGreetingChat, // Mark as sent if this is a greeting chat
    }
    
    setChatHistory((prev) => {
      const updated = [newChat, ...prev]
      // Immediately save to localStorage
      try {
        const serialized = updated.map((chat) => ({
          ...chat,
          messages: chat.messages.map((msg) => ({
            ...msg,
            timestamp: msg.timestamp.toISOString(),
          })),
          createdAt: chat.createdAt.toISOString(),
          updatedAt: chat.updatedAt.toISOString(),
          greetingSent: chat.greetingSent || false,
        }))
        localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized))
        localStorage.setItem('supportron_last_chat_id', newChatId)
      } catch (error) {
        console.error('Error saving chat to storage:', error)
      }
      return updated
    })
    setCurrentChatId(newChatId)
    return newChatId
  }

  const updateChat = (chatId: string, messages: Message[]) => {
    setChatHistory((prev) => {
      const updated = prev.map((chat) => {
        if (chat.id === chatId) {
          // Update title only if there's a user message and title is still "New Chat"
          const firstUserMessage = messages.find(msg => msg.role === 'user')
          let title = chat.title
          
          if (chat.title === 'New Chat' && firstUserMessage) {
            // Update title to first user message (shortened)
            title = firstUserMessage.content.substring(0, 50).trim() || 'New Chat'
          } else if (chat.title !== 'New Chat') {
            // Keep existing title if it's not "New Chat"
            title = chat.title
          }
          
          return {
            ...chat,
            messages,
            title,
            updatedAt: new Date(),
          }
        }
        return chat
      })
      
      // Immediately save to localStorage
      try {
        const serialized = updated.map((chat) => ({
          ...chat,
          messages: chat.messages.map((msg) => ({
            ...msg,
            timestamp: msg.timestamp.toISOString(),
          })),
          createdAt: chat.createdAt.toISOString(),
          updatedAt: chat.updatedAt.toISOString(),
          greetingSent: chat.greetingSent || false,
        }))
        localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized))
      } catch (error) {
        console.error('Error saving chat update to storage:', error)
      }
      
      return updated
    })
  }

  const deleteChat = (chatId: string) => {
    setChatHistory((prev) => {
      const updated = prev.filter((chat) => chat.id !== chatId)
      
      // Immediately save to localStorage
      try {
        if (updated.length > 0) {
          const serialized = updated.map((chat) => ({
            ...chat,
            messages: chat.messages.map((msg) => ({
              ...msg,
              timestamp: msg.timestamp.toISOString(),
            })),
            createdAt: chat.createdAt.toISOString(),
            updatedAt: chat.updatedAt.toISOString(),
            greetingSent: chat.greetingSent || false,
          }))
          localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized))
        } else {
          localStorage.removeItem(STORAGE_KEY)
        }
      } catch (error) {
        console.error('Error saving chat deletion to storage:', error)
      }
      
      return updated
    })
    
    if (currentChatId === chatId) {
      setCurrentChatId(null)
      localStorage.removeItem('supportron_last_chat_id')
    }
  }

  const renameChat = (chatId: string, newTitle: string) => {
    setChatHistory((prev) => {
      const updated = prev.map((chat) =>
        chat.id === chatId
          ? { ...chat, title: newTitle, updatedAt: new Date() }
          : chat
      )
      
      // Immediately save to localStorage
      try {
        const serialized = updated.map((chat) => ({
          ...chat,
          messages: chat.messages.map((msg) => ({
            ...msg,
            timestamp: msg.timestamp.toISOString(),
          })),
          createdAt: chat.createdAt.toISOString(),
          updatedAt: chat.updatedAt.toISOString(),
          greetingSent: chat.greetingSent || false,
        }))
        localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized))
      } catch (error) {
        console.error('Error saving chat rename to storage:', error)
      }
      
      return updated
    })
  }

  const selectChat = (chatId: string) => {
    setCurrentChatId(chatId)
  }

  const clearAllChats = () => {
    setChatHistory([])
    setCurrentChatId(null)
    try {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem('supportron_last_chat_id')
    } catch (error) {
      console.error('Error clearing all chats from storage:', error)
    }
  }

  return {
    chatHistory,
    currentChatId,
    setCurrentChatId,
    createChat,
    updateChat,
    deleteChat,
    renameChat,
    selectChat,
    clearAllChats,
  }
}

