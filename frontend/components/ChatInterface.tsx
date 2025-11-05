'use client'

import { useState, useRef, useEffect } from 'react'
import { useChat } from '@/hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { LoadingIndicator } from './LoadingIndicator'
import { ChatInput } from './ChatInput'

const ChatInterface = () => {
  const { messages, isLoading, sendMessage } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return
    
    const messageContent = input.trim()
    setInput('')
    await sendMessage(messageContent)
  }

  return (
    <div 
      className="h-full w-full flex flex-col glass-effect rounded-2xl overflow-hidden shadow-2xl relative scan-line"
      role="log"
      aria-label="Chat conversation"
      aria-live="polite"
      aria-atomic="false"
      aria-busy={isLoading}
    >
      {/* Messages Area */}
      <div 
        className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2 xs:p-3 sm:p-4 md:p-5 lg:p-6 focus:outline-none"
        tabIndex={-1}
        aria-label="Messages"
      >
        <div className="flex flex-col w-full max-w-full">
          {messages.map((message, index) => (
            <MessageBubble
              key={`message-${index}`}
              message={message}
              aria-label={`Message ${index + 1} from ${message.role === 'user' ? 'You' : 'Supportron'}`}
            />
          ))}
          
          {isLoading && <LoadingIndicator />}
          
          <div ref={messagesEndRef} aria-hidden="true" className="h-1" />
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 w-full">
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}

export default ChatInterface
