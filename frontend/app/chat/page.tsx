'use client'

import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatInterface from '@/components/ChatInterface'
import { Message } from '@/types/chat'
import { useChatStorage } from '@/hooks/useChatStorage'

export default function ChatPage() {
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
  const isInitialLoad = useRef(true)
  const greetingSentRef = useRef(false)
  const createdGreetingChatRef = useRef<string | null>(null)

  // Check if we should start a new chat (from landing page)
  useEffect(() => {
    const shouldStartNew = sessionStorage.getItem('startNewChat') === 'true'
    if (shouldStartNew) {
      sessionStorage.removeItem('startNewChat')
      setCurrentChatId(null)
      setMessages([])
      pendingChatIdRef.current = null
      createdGreetingChatRef.current = null
      greetingSentRef.current = false
      localStorage.removeItem('supportron_last_chat_id')
      isInitialLoad.current = false
    }
  }, [setCurrentChatId])

  // Load chat messages when chat is selected or chat history changes
  useEffect(() => {
    if (currentChatId) {
      const chat = chatHistory.find((c) => c.id === currentChatId)
      if (chat && chat.messages && chat.messages.length > 0) {
        setMessages(chat.messages)
        pendingChatIdRef.current = currentChatId
        isInitialLoad.current = false
        // If chat has greeting, mark it as sent to prevent re-sending
        if (chat.greetingSent) {
          greetingSentRef.current = true
        }
      } else if (chat) {
        // Chat exists but has no messages yet
        setMessages([])
        pendingChatIdRef.current = currentChatId
        isInitialLoad.current = false
      }
    } else if (chatHistory.length > 0 && isInitialLoad.current) {
      // On initial load, wait for useChatStorage to restore the last chat
      // Don't clear messages yet
      isInitialLoad.current = false
      // Check if restored chat has greeting
      const lastChatId = localStorage.getItem('supportron_last_chat_id')
      if (lastChatId) {
        const restoredChat = chatHistory.find(c => c.id === lastChatId)
        if (restoredChat && restoredChat.greetingSent) {
          greetingSentRef.current = true
        }
      }
    } else if (!currentChatId && !isInitialLoad.current) {
      // Only clear messages if explicitly no chat selected (user action)
      // Don't clear on initial load
      setMessages([])
      pendingChatIdRef.current = null
      greetingSentRef.current = false
    }
  }, [currentChatId, chatHistory])

  // Send greeting message for new chats - only trigger on specific conditions
  useEffect(() => {
    // Only send greeting if:
    // 1. No current chat selected
    // 2. No messages yet
    // 3. Not loading an existing chat
    // 4. Initial load is complete
    // 5. No initial question (which would create a chat with user message)
    // 6. Greeting hasn't been sent yet in this session
    // 7. We haven't already created a greeting chat for this session
    if (
      !currentChatId &&
      messages.length === 0 &&
      !isInitialLoad.current &&
      !initialQuestion &&
      !greetingSentRef.current &&
      !createdGreetingChatRef.current
    ) {
      greetingSentRef.current = true
      
      const greetingMessage: Message = {
        id: `greeting-${Date.now()}`,
        role: 'assistant',
        content: "Hello! I'm Supportron, your AI assistant for Linux server configuration, hosting support, and system administration. How can I help you today?",
        timestamp: new Date(),
      }
      
      // Create a new chat with the greeting
      const newChatId = createChat([greetingMessage])
      createdGreetingChatRef.current = newChatId
      setCurrentChatId(newChatId)
      pendingChatIdRef.current = newChatId
      setMessages([greetingMessage])
    }
  }, [currentChatId, messages.length, isInitialLoad.current, initialQuestion, createChat, setCurrentChatId])
  
  // Reset greeting flag when a chat is selected or cleared
  useEffect(() => {
    if (currentChatId) {
      // Check if this chat already has a greeting
      const chat = chatHistory.find(c => c.id === currentChatId)
      if (chat && chat.greetingSent) {
        greetingSentRef.current = true
      } else {
        greetingSentRef.current = false
      }
    } else {
      greetingSentRef.current = false
    }
  }, [currentChatId, chatHistory])

  // Load initial question if provided (only if no existing messages)
  useEffect(() => {
    if (initialQuestion && messages.length === 0 && !currentChatId) {
      // This will be handled by ChatInterface when it mounts
    }
  }, [initialQuestion, messages.length, currentChatId])

  const handleNewMessage = (message: Message) => {
    setMessages((prev) => {
      const newMessages = [...prev, message]
      
      // Use ref as source of truth (it's always up-to-date)
      // Fall back to currentChatId if ref is null
      const chatIdToUse = pendingChatIdRef.current || currentChatId
      
      if (chatIdToUse) {
        // Chat exists, update it
        updateChat(chatIdToUse, newMessages)
        // Ensure ref and state are in sync
        if (pendingChatIdRef.current !== chatIdToUse) {
          pendingChatIdRef.current = chatIdToUse
        }
        if (currentChatId !== chatIdToUse) {
          setCurrentChatId(chatIdToUse)
        }
      } else {
        // No chat exists, create a new one
        const newChatId = createChat(newMessages)
        // Immediately set the ref so subsequent messages use the same chat
        pendingChatIdRef.current = newChatId
        setCurrentChatId(newChatId)
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
    localStorage.removeItem('supportron_last_chat_id')
  }

  const handleNewChat = () => {
    setMessages([])
    setCurrentChatId(null)
    pendingChatIdRef.current = null
    greetingSentRef.current = false
    createdGreetingChatRef.current = null
  }

  const handleSelectChat = (chatId: string) => {
    selectChat(chatId)
    setCurrentChatId(chatId)
    pendingChatIdRef.current = chatId
  }

  const handleDeleteChat = (chatId: string) => {
    deleteChat(chatId)
    if (currentChatId === chatId) {
      // Find the next chat to display
      const remainingChats = chatHistory.filter(chat => chat.id !== chatId)
      
      if (remainingChats.length > 0) {
        // Open the most recent chat (first one in the list)
        const nextChat = remainingChats[0]
        selectChat(nextChat.id)
        setCurrentChatId(nextChat.id)
        pendingChatIdRef.current = nextChat.id
        if (nextChat.messages && nextChat.messages.length > 0) {
          setMessages(nextChat.messages)
        } else {
          setMessages([])
        }
      } else {
        // No chats left, clear everything
        setMessages([])
        setCurrentChatId(null)
        pendingChatIdRef.current = null
      }
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

