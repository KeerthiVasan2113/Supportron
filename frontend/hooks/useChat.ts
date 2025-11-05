import { useState, useCallback } from 'react'
import axios from 'axios'
import { Message, ChatResponse } from '@/types/chat'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  sendMessage: (content: string) => Promise<void>
}

const initialMessage: Message = {
  role: 'assistant',
  content: 'Hello! I\'m Supportron, your IT tech support assistant. How can I help you with your technical issue today?'
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([initialMessage])
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: content.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await axios.post<ChatResponse>(`${API_URL}/api/chat`, {
        messages: [...messages, userMessage]
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Sorry, I encountered an error. Please try again or check if the backend server is running.'
      
      const errorResponse: Message = {
        role: 'assistant',
        content: errorMessage
      }
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }, [messages, isLoading])

  return {
    messages,
    isLoading,
    sendMessage
  }
}

