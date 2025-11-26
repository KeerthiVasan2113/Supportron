'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageSquare, ChevronDown, Edit2, Trash2, X, Check } from 'lucide-react'
import { Message } from '@/types/chat'

interface Chat {
  id: string
  title: string
  messages: Message[]
}

interface ChatHistoryDropdownProps {
  chatHistory: Chat[]
  currentChatId: string | null
  onSelectChat: (chatId: string) => void
  onDeleteChat?: (chatId: string) => void
  onRenameChat?: (chatId: string, newTitle: string) => void
  onClearAllChats?: () => void
}

const ChatHistoryDropdown = ({ 
  chatHistory, 
  currentChatId, 
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  onClearAllChats
}: ChatHistoryDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        // Cancel any active editing when clicking outside
        if (editingId) {
          setEditingId(null)
          setEditTitle('')
        }
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, editingId])

  const currentChat = chatHistory.find(c => c.id === currentChatId)

  const handleStartRename = (chatId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(chatId)
    setEditTitle(currentTitle)
  }

  const handleSaveRename = (chatId: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (editTitle.trim() && onRenameChat) {
      onRenameChat(chatId, editTitle.trim())
    }
    setEditingId(null)
    setEditTitle('')
  }

  const handleCancelRename = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    setEditingId(null)
    setEditTitle('')
  }

  const handleDelete = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDeleteChat && confirm('Are you sure you want to delete this chat?')) {
      onDeleteChat(chatId)
    }
  }

  if (chatHistory.length === 0) {
    return null
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-controls="chat-history-menu"
        aria-label={`${isOpen ? 'Close' : 'Open'} chat history. Current chat: ${currentChat ? currentChat.title : 'none'}`}
        className="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-cyan-300 hover:text-cyan-200 hover:bg-cyan-500/20 rounded-lg transition-all duration-200 border border-cyan-500/30 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
      >
        <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
        <span className="max-w-[100px] sm:max-w-[200px] truncate hidden sm:inline">
          {currentChat ? currentChat.title : 'Chat History'}
        </span>
        <ChevronDown className={`w-3 h-3 sm:w-4 sm:h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
      </button>

      {isOpen && (
        <div 
          id="chat-history-menu"
          className="absolute top-full right-0 mt-2 w-[calc(100vw-2rem)] sm:w-72 md:w-80 glass-effect border border-cyan-500/30 rounded-lg shadow-2xl z-[100] max-h-[70vh] overflow-y-auto cyber-glow"
          role="menu"
          aria-label="Chat history"
        >
          <div className="p-2">
            {/* Clear All Chats */}
            {onClearAllChats && chatHistory.length > 0 && (
              <div className="mb-2 pb-2 border-b border-cyan-500/20">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onClearAllChats()
                    setIsOpen(false)
                  }}
                  aria-label="Clear all chat history"
                  className="w-full text-left px-2 sm:px-3 py-1.5 sm:py-2 text-xs sm:text-sm text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded-lg transition-colors flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-red-500/50"
                  role="menuitem"
                >
                  <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                  <span>Clear All Chats</span>
                </button>
              </div>
            )}

            {/* Chat List */}
            {chatHistory.length === 0 ? (
              <div className="px-3 py-4 text-center text-xs sm:text-sm text-cyan-400/50" role="status" aria-live="polite">
                No chat history yet
              </div>
            ) : (
              <ul className="space-y-1" role="list">
                {chatHistory.map((chat) => (
                  <li
                    key={chat.id}
                    className={`group relative rounded-lg transition-all duration-200 ${
                      currentChatId === chat.id
                        ? 'bg-cyan-500/20 border border-cyan-500/40 cyber-glow'
                        : 'hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/20'
                    }`}
                    role="listitem"
                  >
                    {editingId === chat.id ? (
                      <div className="flex items-center space-x-2 px-2 sm:px-3 py-1.5 sm:py-2" role="group" aria-label="Rename chat">
                        <label htmlFor={`rename-chat-${chat.id}`} className="sr-only">
                          Rename chat
                        </label>
                        <input
                          id={`rename-chat-${chat.id}`}
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(chat.id)
                            if (e.key === 'Escape') handleCancelRename()
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="flex-1 px-2 py-1 glass-effect-light text-slate-200 border border-cyan-500/30 rounded text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                          autoFocus
                          aria-label="Chat title"
                        />
                        <button
                          onClick={(e) => handleSaveRename(chat.id, e)}
                          aria-label="Save chat name"
                          className="p-1 hover:bg-cyan-500/20 rounded text-cyan-400 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                        >
                          <Check className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                        </button>
                        <button
                          onClick={(e) => handleCancelRename(e)}
                          aria-label="Cancel renaming"
                          className="p-1 hover:bg-red-500/20 rounded text-red-400 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/50"
                        >
                          <X className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center w-full">
                        <button
                          onClick={() => {
                            onSelectChat(chat.id)
                            setIsOpen(false)
                          }}
                          aria-label={`Select chat: ${chat.title}${currentChatId === chat.id ? ' (current)' : ''}`}
                          aria-current={currentChatId === chat.id ? 'true' : 'false'}
                          className="flex-1 text-left px-2 sm:px-3 py-1.5 sm:py-2 flex items-center space-x-2 min-w-0 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 rounded"
                          role="menuitem"
                        >
                          <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4 flex-shrink-0 text-cyan-400" aria-hidden="true" />
                          <span className="text-xs sm:text-sm truncate text-slate-200">{chat.title}</span>
                        </button>
                        {(onDeleteChat || onRenameChat) && (
                          <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 pr-2 focus-within:opacity-100" role="group" aria-label="Chat actions">
                            {onRenameChat && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleStartRename(chat.id, chat.title, e)
                                }}
                                aria-label={`Rename chat: ${chat.title}`}
                                className="p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded transition-colors focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                                title="Rename"
                              >
                                <Edit2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
                              </button>
                            )}
                            {onDeleteChat && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleDelete(chat.id, e)
                                }}
                                aria-label={`Delete chat: ${chat.title}`}
                                className="p-1.5 text-red-400/70 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500/50"
                                title="Delete"
                              >
                                <Trash2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatHistoryDropdown
