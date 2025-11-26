'use client'

import { useEffect, useRef } from 'react'
import Image from 'next/image'
import MessageBubble from './MessageBubble'
import { Message } from '@/types/chat'
import { Loader2 } from 'lucide-react'
import { useTimer } from '@/hooks/useTimer'

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
  
  // Use universal timer for "Thinking..." message
  const isThinkingActive = isLoading && !hasLoadingMessage
  const { formattedTime } = useTimer(isThinkingActive)

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
          className="group flex items-start w-full px-2 sm:px-4 mr-auto space-x-2 sm:space-x-3"
          role="status"
          aria-live="polite"
          aria-label="Assistant is thinking"
        >
          <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full overflow-hidden bg-gradient-to-br from-cyan-500 to-teal-500 cyber-glow ring-2 ring-cyan-500/50" aria-hidden="true">
            <Image
              src="/icons/AI.png"
              alt="AI Assistant"
              width={32}
              height={32}
              className="w-full h-full object-cover"
              aria-hidden="true"
            />
          </div>
          <div className="flex-1 glass-effect-light border border-cyan-500/20 rounded-xl sm:rounded-2xl px-3 sm:px-4 py-2 sm:py-3 max-w-full" style={{ maxWidth: 'min(100%, 48rem)' }}>
            <div className="flex items-center space-x-3">
              <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 text-cyan-400 animate-spin flex-shrink-0" aria-hidden="true" />
              <span className="text-sm sm:text-base text-cyan-300 font-mono whitespace-nowrap">🧠 Brainstorming Solutions...</span>
              <span className="text-xs text-cyan-400/70 whitespace-nowrap" aria-label={`Elapsed time: ${formattedTime}`}>{formattedTime}</span>
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} aria-hidden="true" />
    </div>
  )
}

export default MessageList

