'use client'

import { useState } from 'react'
import { Menu, X, Plus, MessageSquare, Trash2, Edit2, MoreVertical, Check } from 'lucide-react'
import { Message } from '@/types/chat'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  chatHistory: { id: string; title: string; messages: Message[] }[]
  onNewChat: () => void
  onSelectChat: (chatId: string) => void
  onDeleteChat?: (chatId: string) => void
  onRenameChat?: (chatId: string, newTitle: string) => void
  currentChatId: string | null
}

const Sidebar = ({
  isOpen,
  onToggle,
  chatHistory,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
  currentChatId,
}: SidebarProps) => {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)

  const handleStartRename = (chatId: string, currentTitle: string) => {
    setEditingId(chatId)
    setEditTitle(currentTitle)
    setMenuOpenId(null)
  }

  const handleSaveRename = (chatId: string) => {
    if (editTitle.trim() && onRenameChat) {
      onRenameChat(chatId, editTitle.trim())
    }
    setEditingId(null)
    setEditTitle('')
  }

  const handleCancelRename = () => {
    setEditingId(null)
    setEditTitle('')
  }

  const handleDelete = (chatId: string) => {
    if (onDeleteChat && confirm('Are you sure you want to delete this chat?')) {
      onDeleteChat(chatId)
    }
    setMenuOpenId(null)
  }
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-800">
            <button
              onClick={onNewChat}
              className="flex items-center space-x-2 px-3 py-2 bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors w-full"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">New Chat</span>
            </button>
            <button
              onClick={onToggle}
              className="lg:hidden ml-2 p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-2">
            {chatHistory.length === 0 ? (
              <div className="text-center text-gray-400 mt-8 px-4">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No chat history</p>
                <p className="text-xs mt-1">Start a new conversation</p>
              </div>
            ) : (
              <div className="space-y-1">
                {chatHistory.map((chat) => (
                  <div
                    key={chat.id}
                    className={`group relative w-full rounded-lg transition-colors ${
                      currentChatId === chat.id
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    {editingId === chat.id ? (
                      <div className="flex items-center space-x-2 px-3 py-2">
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(chat.id)
                            if (e.key === 'Escape') handleCancelRename()
                          }}
                          className="flex-1 px-2 py-1 bg-gray-700 text-white rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                          autoFocus
                        />
                        <button
                          onClick={() => handleSaveRename(chat.id)}
                          className="p-1 hover:bg-gray-700 rounded text-green-400"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleCancelRename}
                          className="p-1 hover:bg-gray-700 rounded text-red-400"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => onSelectChat(chat.id)}
                          className="w-full text-left px-3 py-2 flex items-center space-x-2"
                        >
                          <MessageSquare className="w-4 h-4 flex-shrink-0" />
                          <span className="text-sm truncate flex-1">{chat.title}</span>
                        </button>
                        {(onDeleteChat || onRenameChat) && (
                          <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="relative">
                              <button
                                onClick={() => setMenuOpenId(menuOpenId === chat.id ? null : chat.id)}
                                className="p-1 hover:bg-gray-700 rounded"
                              >
                                <MoreVertical className="w-4 h-4" />
                              </button>
                              {menuOpenId === chat.id && (
                                <div className="absolute right-0 mt-1 w-32 bg-gray-800 rounded-lg shadow-lg z-10 border border-gray-700">
                                  {onRenameChat && (
                                    <button
                                      onClick={() => handleStartRename(chat.id, chat.title)}
                                      className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 flex items-center space-x-2"
                                    >
                                      <Edit2 className="w-3 h-3" />
                                      <span>Rename</span>
                                    </button>
                                  )}
                                  {onDeleteChat && (
                                    <button
                                      onClick={() => handleDelete(chat.id)}
                                      className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-gray-700 flex items-center space-x-2"
                                    >
                                      <Trash2 className="w-3 h-3" />
                                      <span>Delete</span>
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-800">
            <div className="text-xs text-gray-400 text-center">
              Supportron
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile menu button */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed top-4 left-4 z-50 lg:hidden p-2 bg-gray-900 text-white rounded-lg shadow-lg"
        >
          <Menu className="w-5 h-5" />
        </button>
      )}
    </>
  )
}

export default Sidebar

