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
  onNewMessage: (message: Message, chatId?: string | null) => void
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
  const loadingChatIdRef = useRef<string | null>(null) // Track which chat is loading
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialQuestionSent = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Clear loading state if we switched to a different chat
  useEffect(() => {
    if (currentChatId && loadingChatIdRef.current && loadingChatIdRef.current !== currentChatId) {
      // We switched to a different chat while a request was in progress
      // Clear the loading state for the old chat
      setIsLoading(false)
      loadingChatIdRef.current = null
    }
  }, [currentChatId])

  // Send initial question ONLY once
  useEffect(() => {
    if (
      initialQuestion &&
      !initialQuestionSent.current &&
      messages.length === 0
    ) {
      initialQuestionSent.current = true
      handleSendMessage(initialQuestion)
    }
  }, [initialQuestion, messages])

  const handleSendMessage = async (content: string, regenerateMessageId?: string) => {
    if (!content.trim() || isLoading) return

    // Capture the chat ID at the time of sending
    const chatIdAtSendTime = currentChatId || 'new-chat'
    loadingChatIdRef.current = chatIdAtSendTime

    if (!regenerateMessageId) {
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date()
      }

      // Pass the chat ID so the response goes to the correct chat
      onNewMessage(userMessage, chatIdAtSendTime)

      // delay loader - only set if still on the same chat
      setTimeout(() => {
        if (loadingChatIdRef.current === chatIdAtSendTime) {
          setIsLoading(true)
        }
      }, 800)
    } else {
      setIsLoading(true)
    }

    const startTime = Date.now()

    try {
      let messagesToInclude = messages

      if (regenerateMessageId) {
        const regenerateIndex = messages.findIndex(m => m.id === regenerateMessageId)
        if (regenerateIndex !== -1) {
          messagesToInclude = messages.slice(0, regenerateIndex)
        }
      }

      const questionLower = content.toLowerCase()
      const isAboutConversation = [
        'first question', 'first message', 'earlier', 'previous',
        'what did i ask', 'what did you say', 'conversation', 'chat history',
        'earlier in', 'mentioned', 'discussed', 'talked about'
      ].some(keyword => questionLower.includes(keyword))

      const historyMessages = isAboutConversation
        ? messagesToInclude.map(msg => ({ role: msg.role, content: msg.content }))
        : messagesToInclude.slice(-30).map(msg => ({ role: msg.role, content: msg.content }))

      const data = await sendChatMessage(content.trim(), true, historyMessages)
      const endTime = Date.now()
      const timeTaken = ((endTime - startTime) / 1000).toFixed(2)

      const assistantMessage: Message = {
        id: regenerateMessageId || (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer || 'No response.',
        timestamp: new Date(),
        sources: data.sources || [],
        responseTime: parseFloat(timeTaken),
        isLoading: false
      }

      if (regenerateMessageId && onUpdateMessages) {
        const idx = messages.findIndex(m => m.id === regenerateMessageId)
        if (idx !== -1) {
          const updated = [...messages]
          updated[idx] = assistantMessage
          onUpdateMessages(updated)
          return
        }
      }

      // Always pass the original chat ID to ensure response goes to the correct chat
      onNewMessage(assistantMessage, chatIdAtSendTime)

    } catch (error: any) {
      console.error('Error sending message:', error)

      let errorContent = 'An unexpected error occurred. Please try again.'

      if (error instanceof Error) {
        if (error.message.includes('511')) {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          errorContent = `⚠️ Tunnel Connection Required\n\nVisit:\n${apiUrl}\n\nThen try again.`
        } else {
          errorContent = `Error: ${error.message}`
        }
      }

      const errorMessage: Message = {
        id: regenerateMessageId || Date.now().toString(),
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
        isLoading: false
      }

      if (regenerateMessageId && onUpdateMessages) {
        const idx = messages.findIndex(m => m.id === regenerateMessageId)
        if (idx !== -1) {
          const updated = [...messages]
          updated[idx] = errorMessage
          onUpdateMessages(updated)
          // Clear loading state
          if (loadingChatIdRef.current === chatIdAtSendTime) {
            setIsLoading(false)
            loadingChatIdRef.current = null
          }
          return
        }
      }

      // Always pass the original chat ID to ensure error goes to the correct chat
      onNewMessage(errorMessage, chatIdAtSendTime)

    } finally {
      // Only clear loading if this request belongs to the current chat
      if (loadingChatIdRef.current === chatIdAtSendTime) {
        setIsLoading(false)
        loadingChatIdRef.current = null
      }
    }
  }

  const handleEditMessage = (messageId: string, newContent: string) => {
    const index = messages.findIndex(m => m.id === messageId)
    if (index === -1) return

    const editedMessage = messages[index]
    if (editedMessage.role !== 'user') return

    const assistantIndex = index + 1
    let updated = messages.slice(0, index + 1)

    if (assistantIndex < messages.length && messages[assistantIndex].role === 'assistant') {
      updated.push({
        id: messages[assistantIndex].id,
        role: 'assistant' as const,
        content: '',
        timestamp: new Date(),
        isLoading: true,
        loadingStartTime: Date.now()
      })
    }

    updated[index] = { ...editedMessage, content: newContent }

    onUpdateMessages?.(updated)

    setTimeout(() => {
      handleSendMessage(
        newContent,
        assistantIndex < messages.length ? messages[assistantIndex].id : undefined
      )
    }, 100)
  }

  const handleRegenerate = (messageId: string) => {
    const index = messages.findIndex(m => m.id === messageId)
    if (index === -1) return

    const assistantMsg = messages[index]
    if (assistantMsg.role !== 'assistant') return

    const userMsg = messages[index - 1]
    if (!userMsg || userMsg.role !== 'user') return

    const loading: Message = {
      id: messageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
      loadingStartTime: Date.now()
    }

    const updated = [...messages]
    updated[index] = loading
    onUpdateMessages?.(updated)

    handleSendMessage(userMsg.content, messageId)
  }

  return (
    <div className="flex flex-col h-screen w-full bg-slate-950">
      
      {/* HEADER */}
      <header className="glass-effect border-b border-cyan-500/20 px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between z-20">
        <div className="flex items-center space-x-2 sm:space-x-3 flex-1 min-w-0">
          <h1
            onClick={() => router.push('/home')}
            tabIndex={0}
            className="text-lg sm:text-xl font-bold bg-gradient-to-r from-cyan-400 via-teal-400 to-cyan-300 bg-clip-text text-transparent truncate cursor-pointer hover:opacity-80 transition-opacity"
          >
            Supportron
          </h1>
        </div>

        <div className="flex items-center space-x-2 sm:space-x-3">
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
              className="flex items-center px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-teal-500 text-slate-950 rounded-lg disabled:opacity-40"
            >
              <Plus className="w-4 h-4" />
              <span className="ml-1 hidden sm:inline">New Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* MESSAGES */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
        {messages.length === 0 ? (
          <div className="flex justify-center items-center h-full text-center text-slate-300">
            <div>
              <h2 className="text-2xl mb-2 text-cyan-400">Welcome to Supportron</h2>
              <p>Ask me anything about Linux, hosting, and more.</p>
            </div>
          </div>
        ) : (
          <MessageList
            messages={messages}
            isLoading={isLoading && loadingChatIdRef.current === currentChatId}
            onEditMessage={handleEditMessage}
            onRegenerate={handleRegenerate}
          />
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* INPUT */}
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}

export default ChatInterface