'use client'

import { useState, useRef, KeyboardEvent, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
}

const ChatInput = ({ onSendMessage, isLoading }: ChatInputProps) => {
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustTextareaHeight = () => {
    if (!textareaRef.current) return
    
    const target = textareaRef.current
    // Calculate line height based on font size (text-sm = 0.875rem = 14px)
    // Plus padding (py-2 = 8px top + 8px bottom = 16px total)
    const lineHeight = 20 // Approximate line height for text-sm
    const padding = 16 // py-2 sm:py-3 = 8px top + 8px bottom
    const maxLines = 5
    const maxHeight = (lineHeight * maxLines) + padding
    
    // Reset height to auto to get accurate scrollHeight
    target.style.height = 'auto'
    const scrollHeight = target.scrollHeight
    
    if (scrollHeight <= maxHeight) {
      // Content fits within 5 lines, grow the textarea
      target.style.height = `${scrollHeight}px`
      target.style.overflowY = 'hidden'
    } else {
      // Content exceeds 5 lines, set to max height and show scrollbar
      target.style.height = `${maxHeight}px`
      target.style.overflowY = 'auto'
    }
  }

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      setIsSending(true)
      onSendMessage(input)
      setInput('')
      // Reset animation after a short delay
      setTimeout(() => setIsSending(false), 600)
      // Reset textarea height after clearing
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = '42px'
          textareaRef.current.style.overflowY = 'hidden'
        }
      }, 100)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Adjust height when input changes (including paste)
  useEffect(() => {
    adjustTextareaHeight()
  }, [input])

  // Initialize textarea height on mount
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '42px'
      textareaRef.current.style.overflowY = 'hidden'
    }
  }, [])

  return (
    <div className="glass-effect border-t border-cyan-500/20 px-3 sm:px-4 py-3 sm:py-4 flex-shrink-0">
      <div className="max-w-3xl mx-auto w-full">
        <div className="flex items-end space-x-2 sm:space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                adjustTextareaHeight()
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask about Linux server configuration, hosting, or system administration..."
              className="w-full px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-cyan-500/30 rounded-xl sm:rounded-2xl glass-effect-light text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 resize-none"
              rows={1}
              disabled={isLoading}
              style={{
                overflowY: 'hidden',
                minHeight: '42px',
                height: '42px'
              }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={`flex-shrink-0 w-auto aspect-square rounded-xl sm:rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all duration-200 cyber-glow disabled:shadow-none ${
              isSending ? 'animate-paperplane-fly' : ''
            }`}
            style={{
              height: '42px',
              width: '42px',
              padding: '0'
            }}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
            ) : (
              <Send className={`w-4 h-4 sm:w-5 sm:h-5 ${isSending ? 'animate-paperplane-icon' : ''}`} />
            )}
          </button>
        </div>
        <div className="mt-1 sm:mt-2 text-[10px] sm:text-xs text-cyan-400/50 text-center font-mono">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

export default ChatInput

