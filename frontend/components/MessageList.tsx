'use client'

import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import { Message } from '@/types/chat'
import { Loader2 } from 'lucide-react'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
  onEditMessage?: (messageId: string, newContent: string) => void
  onRegenerate?: (messageId: string) => void
}

const MessageList = ({ messages, isLoading, onEditMessage, onRegenerate }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Check if any message is in loading state
  const hasLoadingMessage = messages.some(msg => msg.isLoading)

  return (
    <div 
      className="flex flex-col space-y-3 sm:space-y-4 p-2 sm:p-4 pb-20 sm:pb-24"
      role="log"
      aria-label="Message list"
      aria-live="polite"
      aria-atomic="false"
    >
      {messages.map((message, index) => (
        <MessageBubble 
          key={message.id} 
          message={message}
          onEdit={onEditMessage}
          onRegenerate={onRegenerate}
        />
      ))}
      {/* Only show "Thinking..." if loading but no message is in loading state (for new messages) */}
      {isLoading && !hasLoadingMessage && (
        <div 
          className="group flex items-start max-w-3xl w-full px-2 sm:px-4 mr-auto space-x-2 sm:space-x-3"
          role="status"
          aria-live="polite"
          aria-label="Assistant is thinking"
        >
          <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-cyan-500 to-teal-500 cyber-glow" aria-hidden="true">
            <svg
              className="w-4 h-4 sm:w-5 sm:h-5 text-white"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div className="flex-1 glass-effect-light border border-cyan-500/20 rounded-xl sm:rounded-2xl px-3 sm:px-4 py-2 sm:py-3">
            <div className="flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" aria-hidden="true" />
              <span className="text-sm sm:text-base text-cyan-300 font-mono">Thinking...</span>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} aria-hidden="true" />
    </div>
  )
}

export default MessageList

