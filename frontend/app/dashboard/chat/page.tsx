'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageBubble } from '@/components/MessageBubble'
import { LoadingIndicator } from '@/components/LoadingIndicator'
import { ChatInput } from '@/components/ChatInput'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const messageContent = input.trim()
    const userMessage: Message = {
      role: 'user',
      content: messageContent
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const messagesForAPI = [...messages, userMessage].map(m => ({
        role: m.role,
        content: m.content
      }))

      const response = await axios.post(`${API_URL}/api/chat`, {
        messages: messagesForAPI
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
  }

  return (
    <div className="h-full flex flex-col p-6">
      <div className="max-w-4xl mx-auto w-full flex flex-col h-full">
        <h1 className="text-3xl font-bold text-neon-cyan mb-6">Chat Assistant</h1>
        
        <div className="flex-1 glass-effect rounded-2xl p-6 tech-border overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-text-secondary py-8">
                <p className="text-lg mb-2">Welcome! Ask me anything.</p>
                <p className="text-sm">I'm here to help with your questions.</p>
              </div>
            )}
            {messages.map((message, index) => (
              <MessageBubble
                key={index}
                message={message}
              />
            ))}
            {isLoading && <LoadingIndicator />}
            <div ref={messagesEndRef} />
          </div>
          
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            isLoading={isLoading}
            placeholder="Type your question here..."
          />
        </div>
      </div>
    </div>
  )
}

