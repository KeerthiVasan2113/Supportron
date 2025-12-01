'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Message } from '@/types/chat'
import { 
  getStorageItem, 
  setStorageItem, 
  removeStorageItem,
  StorageKeys 
} from '@/utils/storage'

export interface Chat {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  greetingSent?: boolean
}

const STORAGE_KEY = StorageKeys.CHATS
const LAST_CHAT_KEY = StorageKeys.LAST_CHAT_ID

export const useChatStorage = () => {
  const [chatHistory, setChatHistory] = useState<Chat[]>([])
  const [currentChatId, setCurrentChatId] = useState<string | null>(null)
  const hasLoadedFromStorage = useRef(false)

  // Load chats from localStorage on mount
  useEffect(() => {
    try {
      const stored = getStorageItem<Chat[]>(STORAGE_KEY, [])
      if (Array.isArray(stored) && stored.length > 0) {
        const chats = stored.map((chat) => ({
          ...chat,
          messages: chat.messages?.map((msg) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })) || [],
          createdAt: new Date(chat.createdAt),
          updatedAt: new Date(chat.updatedAt),
        }))
        setChatHistory(chats)
        hasLoadedFromStorage.current = true
        
        // Restore last active chat if available
        const lastChatId = getStorageItem<string | null>(LAST_CHAT_KEY, null)
        if (lastChatId) {
          const chatExists = chats.find((c) => c.id === lastChatId)
          if (chatExists) {
            setCurrentChatId(lastChatId)
          } else if (chats.length > 0) {
            // Last chat ID doesn't exist, use most recent chat
            const mostRecent = [...chats].sort(
              (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
            )[0]
            setCurrentChatId(mostRecent.id)
            setStorageItem(LAST_CHAT_KEY, mostRecent.id)
          }
        } else if (chats.length > 0) {
          // No last chat ID, use most recent chat
          const mostRecent = [...chats].sort(
            (a, b) => b.updatedAt.getTime() - a.updatedAt.getTime()
          )[0]
          setCurrentChatId(mostRecent.id)
          setStorageItem(LAST_CHAT_KEY, mostRecent.id)
        }
      } else {
        hasLoadedFromStorage.current = true
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error loading chats from storage:', error)
      }
      hasLoadedFromStorage.current = true
    }
  }, [])
  
  // Save chats to localStorage whenever chatHistory changes
  useEffect(() => {
    // Don't save until we've loaded from storage (prevents overwriting on initial mount)
    if (!hasLoadedFromStorage.current) {
      return
    }
    
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
      setStorageItem(STORAGE_KEY, serialized)
    } else {
      // Only remove if explicitly cleared by user (after initial load)
      removeStorageItem(STORAGE_KEY)
    }
    
    if (currentChatId) {
      setStorageItem(LAST_CHAT_KEY, currentChatId)
    } else {
      removeStorageItem(LAST_CHAT_KEY)
    }
  }, [chatHistory, currentChatId])

  const createChat = useCallback((messages: Message[]): string => {
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
      greetingSent: isGreetingChat,
    }
    
    setChatHistory((prev) => {
      const updated = [newChat, ...prev]
      // Immediately save to localStorage
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
      setStorageItem(STORAGE_KEY, serialized)
      setStorageItem(LAST_CHAT_KEY, newChatId)
      return updated
    })
    setCurrentChatId(newChatId)
    return newChatId
  }, [])

  const updateChat = useCallback((chatId: string, messages: Message[]) => {
    setChatHistory((prev) => {
      const updated = prev.map((chat) => {
        if (chat.id === chatId) {
          // Update title only if there's a user message and title is still "New Chat"
          const firstUserMessage = messages.find(msg => msg.role === 'user')
          let title = chat.title
          
          if (chat.title === 'New Chat' && firstUserMessage) {
            title = firstUserMessage.content.substring(0, 50).trim() || 'New Chat'
          } else if (chat.title !== 'New Chat') {
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
      setStorageItem(STORAGE_KEY, serialized)
      
      return updated
    })
  }, [])

  const deleteChat = useCallback((chatId: string) => {
    setChatHistory((prev) => {
      const updated = prev.filter((chat) => chat.id !== chatId)
      
      // Immediately save to localStorage
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
        setStorageItem(STORAGE_KEY, serialized)
      } else {
        removeStorageItem(STORAGE_KEY)
      }
      
      return updated
    })
    
    if (currentChatId === chatId) {
      setCurrentChatId(null)
      removeStorageItem(LAST_CHAT_KEY)
    }
  }, [currentChatId])

  const renameChat = useCallback((chatId: string, newTitle: string) => {
    setChatHistory((prev) => {
      const updated = prev.map((chat) =>
        chat.id === chatId
          ? { ...chat, title: newTitle, updatedAt: new Date() }
          : chat
      )
      
      // Immediately save to localStorage
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
      setStorageItem(STORAGE_KEY, serialized)
      
      return updated
    })
  }, [])

  const selectChat = useCallback((chatId: string) => {
    setCurrentChatId(chatId)
  }, [])

  const clearAllChats = useCallback(() => {
    setChatHistory([])
    setCurrentChatId(null)
    removeStorageItem(STORAGE_KEY)
    removeStorageItem(LAST_CHAT_KEY)
  }, [])

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

