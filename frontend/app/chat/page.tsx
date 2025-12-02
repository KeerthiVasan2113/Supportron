'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatInterface from '@/components/ChatInterface'
import { Message } from '@/types/chat'
import { useChatStorage } from '@/hooks/useChatStorage'
import { getSessionItem, removeSessionItem, removeStorageItem, StorageKeys } from '@/utils/storage'

function ChatPageContent() {
  const searchParams = useSearchParams()
  const initialQuestion = searchParams.get('q')
  
  const {
    chatHistory,
    currentChatId,
    setCurrentChatId,
    createChat,
    updateChat,
    deleteChat,
    renameChat,
    selectChat,
    clearAllChats: clearAllChatsStorage,
  } = useChatStorage()

  const [messages, setMessages] = useState<Message[]>([])
  const pendingChatIdRef = useRef<string | null>(null)
  const isInitializedRef = useRef(false)
  const greetingSentRef = useRef(false)

  // Initialize: Check for new chat request and load chat state
  useEffect(() => {
    if (isInitializedRef.current) return
    
    // Check if we should start a new chat (from home page)
    const shouldStartNew = getSessionItem(StorageKeys.START_NEW_CHAT) === 'true'
    if (shouldStartNew) {
      removeSessionItem(StorageKeys.START_NEW_CHAT)
      setCurrentChatId(null)
      setMessages([])
      pendingChatIdRef.current = null
      removeStorageItem(StorageKeys.LAST_CHAT_ID)
      greetingSentRef.current = false
      isInitializedRef.current = true
      return
    }

    // Load messages for current chat if it exists
    if (currentChatId) {
      const chat = chatHistory.find((c) => c.id === currentChatId)
      if (chat) {
        setMessages(chat.messages || [])
        pendingChatIdRef.current = currentChatId
        greetingSentRef.current = chat.greetingSent || false
      }
    }
    
    isInitializedRef.current = true
  }, [currentChatId, chatHistory, setCurrentChatId])

  // Sync messages when chat selection changes (after initialization)
  useEffect(() => {
    if (!isInitializedRef.current) return

    if (currentChatId) {
      const chat = chatHistory.find((c) => c.id === currentChatId)
      if (chat) {
        setMessages(chat.messages || [])
        pendingChatIdRef.current = currentChatId
        greetingSentRef.current = chat.greetingSent || false
      } else {
        // Chat ID exists but chat not found - clear state
        setMessages([])
        pendingChatIdRef.current = null
        greetingSentRef.current = false
      }
    } else {
      // No chat selected - clear messages and send greeting if needed
      setMessages([])
      pendingChatIdRef.current = null
      
      // Send greeting for new empty chats (only once, no initial question)
      if (!greetingSentRef.current && !initialQuestion) {
        greetingSentRef.current = true
        
        const greetingMessage: Message = {
          id: `greeting-${Date.now()}`,
          role: 'assistant',
          content: "Hello! I'm Supportron, your AI assistant for Linux server configuration, hosting support, and system administration. How can I help you today?",
          timestamp: new Date(),
        }
        
        const newChatId = createChat([greetingMessage])
        setCurrentChatId(newChatId)
        pendingChatIdRef.current = newChatId
        setMessages([greetingMessage])
      } else {
        greetingSentRef.current = false
      }
    }
  }, [currentChatId, chatHistory, initialQuestion, createChat])

  const handleNewMessage = (message: Message, specifiedChatId?: string | null) => {
    // Determine which chat this message belongs to
    const chatIdToUse = specifiedChatId || pendingChatIdRef.current || currentChatId
    
    // Only update local messages if we're viewing the target chat
    const isViewingTargetChat = !currentChatId || currentChatId === chatIdToUse
    
    setMessages((prev) => {
      // Only update if viewing the target chat
      if (!isViewingTargetChat) {
        return prev
      }
      
      const newMessages = [...prev, message]
      
      if (chatIdToUse && chatIdToUse !== 'new-chat') {
        // Chat exists, update it
        updateChat(chatIdToUse, newMessages)
        pendingChatIdRef.current = chatIdToUse
        
        // Sync currentChatId if needed
        if (!currentChatId || currentChatId !== chatIdToUse) {
          setCurrentChatId(chatIdToUse)
        }
      } else {
        // No chat exists, create a new one
        const newChatId = createChat(newMessages)
        pendingChatIdRef.current = newChatId
        
        if (!currentChatId) {
          setCurrentChatId(newChatId)
        }
      }
      
      return newMessages
    })
  }

  const handleClearChat = () => {
    // Only clear current view, don't delete the chat from history
    // User can still access it from chat history
    setMessages([])
    setCurrentChatId(null)
    pendingChatIdRef.current = null
    removeStorageItem(StorageKeys.LAST_CHAT_ID)
  }

  const handleNewChat = () => {
    setMessages([])
    setCurrentChatId(null)
    pendingChatIdRef.current = null
  }

  const handleSelectChat = (chatId: string) => {
    // Update chat selection synchronously
    selectChat(chatId)
    setCurrentChatId(chatId)
    pendingChatIdRef.current = chatId
    // Messages will be synced by the useEffect that watches currentChatId
  }

  const handleDeleteChat = (chatId: string) => {
    deleteChat(chatId)
    if (currentChatId === chatId) {
      setMessages([])
      setCurrentChatId(null)
      pendingChatIdRef.current = null
    }
  }

  const handleRenameChat = (chatId: string, newTitle: string) => {
    renameChat(chatId, newTitle)
  }

  const handleClearAllChats = () => {
    if (confirm('Are you sure you want to delete all chats? This action cannot be undone.')) {
      clearAllChatsStorage()
      setMessages([])
      setCurrentChatId(null)
      pendingChatIdRef.current = null
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 w-full">
      <ChatInterface
        messages={messages}
        onNewMessage={handleNewMessage}
        onClearChat={handleClearChat}
        onNewChat={handleNewChat}
        onUpdateMessages={(updatedMessages) => {
          setMessages(updatedMessages)
          if (currentChatId) {
            updateChat(currentChatId, updatedMessages)
          }
        }}
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
        onClearAllChats={handleClearAllChats}
        initialQuestion={initialQuestion || undefined}
      />
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900 w-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading chat...</p>
        </div>
      </div>
    }>
      <ChatPageContent />
    </Suspense>
  )
}

