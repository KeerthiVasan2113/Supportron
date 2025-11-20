'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Send, Loader2, Plus } from 'lucide-react'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import ChatHistoryDropdown from './ChatHistoryDropdown'
import { Message } from '@/types/chat'
import { sendChatMessage } from '@/lib/api'

interface Chat {
  id: string
  title: string
  messages: Message[]
}

interface ChatInterfaceProps {
  messages: Message[]
  onNewMessage: (message: Message) => void
  onClearChat: () => void
  onNewChat?: () => void
  onUpdateMessages?: (messages: Message[]) => void
  chatHistory?: Chat[]
  currentChatId?: string | null
  onSelectChat?: (chatId: string) => void
  onDeleteChat?: (chatId: string) => void
  onRenameChat?: (chatId: string, newTitle: string) => void
  onClearAllChats?: () => void
  initialQuestion?: string
}

const ChatInterface = ({ 
  messages, 
  onNewMessage, 
  onClearChat, 
  onNewChat,
  onUpdateMessages, 
  chatHistory, 
  currentChatId, 
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  onClearAllChats,
  initialQuestion 
}: ChatInterfaceProps) => {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialQuestionSent = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Ensure global loading indicator is scoped to the currently visible chat
  // Reset when switching chats or when messages for the current chat change
  useEffect(() => {
    // If the current chat has any per-message loading entries, keep the per-message UI.
    // Otherwise clear the global loading flag so other chats don't show the standalone "Brainstorming" bubble.
    const hasPerMessageLoading = messages.some(m => m.isLoading)
    if (!hasPerMessageLoading) {
      setIsLoading(false)
    }
  }, [messages, currentChatId])

  // Send initial question if provided
  useEffect(() => {
    if (initialQuestion && !initialQuestionSent.current && messages.length === 0) {
      initialQuestionSent.current = true
      handleSendMessage(initialQuestion)
    }
  }, [initialQuestion])

  const handleSendMessage = async (content: string, regenerateMessageId?: string) => {
    if (!content.trim() || isLoading) return

    // Add user message (unless regenerating)
    if (!regenerateMessageId) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      }
      onNewMessage(userMessage)
      
      // Wait for user message animation to complete (0.8s) before showing "Thinking..."
      setTimeout(() => {
        setIsLoading(true)
      }, 800)
    } else {
      // For regeneration, show loading immediately
      setIsLoading(true)
    }

    const startTime = Date.now()

    try {
      // Do NOT send conversation history by default. Only include history if user explicitly requests it.
      const data = await sendChatMessage(content.trim(), true)
      const endTime = Date.now()
      const timeTaken = ((endTime - startTime) / 1000).toFixed(2)

      // Add or update assistant message
      const assistantMessage: Message = {
        id: regenerateMessageId || (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        sources: data.sources,
        responseTime: parseFloat(timeTaken),
        isLoading: false
      }
      
      if (regenerateMessageId && onUpdateMessages) {
        // Replace existing message (which should be in loading state)
        const messageIndex = messages.findIndex(m => m.id === regenerateMessageId)
        if (messageIndex !== -1) {
          const updatedMessages = [...messages]
          updatedMessages[messageIndex] = assistantMessage
          onUpdateMessages(updatedMessages)
          return // Don't call onNewMessage for regenerated messages
        }
      }
      
      onNewMessage(assistantMessage)
    } catch (error) {
      console.error('Error sending message:', error)
      
      // Show user-friendly error message
      const errorMessage: Message = {
        id: regenerateMessageId || Date.now().toString(),
        role: 'assistant',
        content: error instanceof Error 
          ? `Error: ${error.message}` 
          : 'An unexpected error occurred. Please try again.',
        timestamp: new Date(),
        isLoading: false
      }
      
      // If regenerating, replace the loading message with error
      if (regenerateMessageId && onUpdateMessages) {
        const messageIndex = messages.findIndex(m => m.id === regenerateMessageId)
        if (messageIndex !== -1) {
          const updatedMessages = [...messages]
          updatedMessages[messageIndex] = errorMessage
          onUpdateMessages(updatedMessages)
        }
      } else {
        onNewMessage(errorMessage)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleEditMessage = (messageId: string, newContent: string) => {
    // Find the message and all subsequent messages
    const messageIndex = messages.findIndex(m => m.id === messageId)
    if (messageIndex === -1) return

    const editedMessage = messages[messageIndex]
    if (editedMessage.role !== 'user') return

    // Find the assistant message that follows this user message
    const assistantIndex = messageIndex + 1
    let updatedMessages = messages.slice(0, messageIndex + 1)
    
    // If there's an assistant message after this user message, replace it with loading state
    if (assistantIndex < messages.length && messages[assistantIndex].role === 'assistant') {
      const loadingMessage: Message = {
        id: messages[assistantIndex].id,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
        loadingStartTime: Date.now()
      }
      updatedMessages.push(loadingMessage)
    }

    // Update the user message content
    updatedMessages[messageIndex] = { ...editedMessage, content: newContent }

    // Update messages through parent
    if (onUpdateMessages) {
      onUpdateMessages(updatedMessages)
    }

    // Regenerate assistant response for the edited user message
    setTimeout(() => {
      handleSendMessage(newContent, assistantIndex < messages.length ? messages[assistantIndex].id : undefined)
    }, 100)
  }

  const handleRegenerate = (messageId: string) => {
    // Find the assistant message to regenerate
    const assistantIndex = messages.findIndex(m => m.id === messageId)
    if (assistantIndex === -1) return

    const assistantMessage = messages[assistantIndex]
    if (assistantMessage.role !== 'assistant') return

    const userMessage = messages[assistantIndex - 1]
    if (!userMessage || userMessage.role !== 'user') return

    // Replace the assistant message with loading state
    const loadingMessage: Message = {
      id: messageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
      loadingStartTime: Date.now()
    }

    const updatedMessages = [...messages]
    updatedMessages[assistantIndex] = loadingMessage

    if (onUpdateMessages) {
      onUpdateMessages(updatedMessages)
    }

    // Regenerate the response
    handleSendMessage(userMessage.content, messageId)
  }

  return (
    <div className="flex flex-col h-screen w-full bg-slate-950">
      {/* Header */}
      <div className="glass-effect border-b border-cyan-500/20 px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between flex-shrink-0 relative z-20">
        <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
          <h1 
            onClick={() => router.push('/home')}
            className="text-lg sm:text-xl font-bold bg-gradient-to-r from-cyan-400 via-teal-400 to-cyan-300 bg-clip-text text-transparent truncate cursor-pointer hover:opacity-80 transition-opacity"
          >
            Supportron
          </h1>
        </div>
        <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
          {onSelectChat && (
            <ChatHistoryDropdown
              chatHistory={chatHistory || []}
              currentChatId={currentChatId || null}
              onSelectChat={onSelectChat}
              onDeleteChat={onDeleteChat}
              onRenameChat={onRenameChat}
              onClearAllChats={onClearAllChats}
            />
          )}
          {onNewChat && (
            <button
              onClick={onNewChat}
              disabled={messages.length === 0}
              className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-950 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed rounded-lg transition-all duration-200 cyber-glow disabled:shadow-none"
            >
              <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto w-full bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 relative z-10">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full px-4">
            <div className="text-center max-w-md w-full">
              <div className="mb-6 flex justify-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 flex items-center justify-center cyber-glow">
                  <svg className="w-10 h-10 text-cyan-400" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent mb-2">
                Welcome to Supportron
              </h2>
              <p className="text-sm sm:text-base text-slate-300 mb-6">
                Ask me anything about Linux server configuration, hosting, system administration, and more.
              </p>
              <div className="space-y-2 text-left">
                <p className="text-xs sm:text-sm text-cyan-400/70 font-semibold">Try asking:</p>
                <ul className="text-xs sm:text-sm text-slate-400 space-y-2">
                  <li className="flex items-center space-x-2">
                    <span className="text-cyan-500">▸</span>
                    <span>How do I configure system settings?</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="text-cyan-500">▸</span>
                    <span>What is Red Hat Enterprise Linux?</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="text-cyan-500">▸</span>
                    <span>How to set up a web server?</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <MessageList 
            messages={messages} 
            isLoading={isLoading} 
            onEditMessage={handleEditMessage}
            onRegenerate={handleRegenerate}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}

export default ChatInterface

