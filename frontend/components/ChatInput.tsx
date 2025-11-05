import React, { useRef, useEffect } from 'react'
import { SendIcon } from './icons/SendIcon'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  isLoading?: boolean
  placeholder?: string
  'aria-label'?: string
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isLoading = false,
  placeholder = 'Ask about IT tech support issues...',
  'aria-label': ariaLabel = 'Chat input'
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '48px'
      const scrollHeight = textareaRef.current.scrollHeight
      textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`
    }
  }, [value])

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [isLoading])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isLoading && value.trim()) {
        handleSend()
      }
    }
  }

  const handleSend = () => {
    if (!isLoading && value.trim()) {
      onSend()
      if (textareaRef.current) {
        textareaRef.current.style.height = '48px'
      }
    }
  }

  const isDisabled = isLoading || !value.trim()

  return (
    <div className="border-t border-dark-border p-1.5 xs:p-2 sm:p-3 md:p-4 bg-chatgpt-dark/80 flex-shrink-0 w-full">
      <div className="flex gap-1.5 xs:gap-2 sm:gap-2.5 md:gap-3 items-end w-full">
        <div className="flex-1 relative min-w-0">
          <label htmlFor="chat-input" className="sr-only">
            {ariaLabel}
          </label>
          <textarea
            id="chat-input"
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full border border-dark-border rounded-xl px-3 xs:px-4 sm:px-4 md:px-5 py-2.5 xs:py-3 sm:py-3 md:py-3.5 text-white placeholder-text-muted focus:outline-none focus:border-telegram-blue focus:ring-2 focus:ring-telegram-blue/30 resize-none transition-all duration-200 text-xs xs:text-sm sm:text-sm md:text-base leading-normal chatgpt-input"
            rows={1}
            style={{
              minHeight: '44px',
              maxHeight: '120px',
              color: '#e4e4e7',
              backgroundColor: '#40414f',
            }}
            disabled={isLoading}
            aria-label={ariaLabel}
            aria-describedby="input-hint"
            aria-invalid={false}
            aria-required="false"
            aria-busy={isLoading}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={isDisabled}
          className="px-3 xs:px-4 sm:px-5 md:px-6 py-2 xs:py-2.5 sm:py-2.5 md:py-3 bg-telegram-blue text-white font-semibold rounded-xl hover:bg-primary-dark active:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-telegram-blue focus:ring-offset-2 focus:ring-offset-dark-bg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-telegram-blue flex items-center justify-center min-w-[44px] xs:min-w-[48px] sm:min-w-[52px] md:min-w-[56px] h-[44px] xs:h-[48px] sm:h-[48px] md:h-[48px] touch-manipulation flex-shrink-0 shadow-lg hover:shadow-xl"
          aria-label="Send message"
          aria-disabled={isDisabled}
          aria-busy={isLoading}
          type="button"
        >
          <SendIcon className="w-3.5 xs:w-4 sm:w-4.5 md:w-5 h-3.5 xs:h-4 sm:h-4.5 md:h-5" aria-hidden={true} />
          <span className="sr-only">Send message</span>
        </button>
      </div>
      <p id="input-hint" className="text-[10px] xs:text-xs sm:text-xs md:text-xs text-text-muted mt-1 xs:mt-1.5 sm:mt-2 text-center px-1 xs:px-2">
        Press Enter to send • Shift+Enter for new line
      </p>
    </div>
  )
}

