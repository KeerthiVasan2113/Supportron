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
    <div className="border-t border-tech-border p-1.5 xs:p-2 sm:p-3 md:p-4 bg-tech-surface/90 flex-shrink-0 w-full relative">
      <div className="relative w-full">
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
          className="w-full bg-tech-darker text-text-primary border border-tech-border rounded-xl pl-3 xs:pl-4 sm:pl-4 md:pl-5 pr-10 xs:pr-11 sm:pr-12 md:pr-14 py-2.5 xs:py-3 sm:py-3 md:py-3.5 placeholder:text-text-muted focus:outline-none focus:border-neon-cyan focus:ring-2 focus:ring-neon-cyan/50 focus:shadow-[0_0_0_2px_rgba(0,240,255,0.3)] resize-none transition-all duration-200 text-xs xs:text-sm sm:text-sm md:text-base leading-normal min-h-[44px] max-h-[120px]"
          rows={1}
          disabled={isLoading}
          aria-label={ariaLabel}
          aria-describedby="input-hint"
          aria-invalid={false}
          aria-required="false"
          aria-busy={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isDisabled}
          className="absolute right-2 xs:right-2.5 sm:right-3 md:right-3.5 bottom-2 xs:bottom-2.5 sm:bottom-3 md:bottom-3.5 bg-gradient-to-br from-neon-cyan to-cyber-blue text-white rounded-lg hover:from-neon-cyan/90 hover:to-cyber-blue/90 active:from-neon-cyan/80 active:to-cyber-blue/80 focus:outline-none focus:ring-2 focus:ring-neon-cyan focus:ring-offset-2 focus:ring-offset-tech-darker transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-neon-cyan disabled:hover:to-cyber-blue flex items-center justify-center w-7 xs:w-8 sm:w-8 md:w-9 h-7 xs:h-8 sm:h-8 md:h-9 touch-manipulation flex-shrink-0 neon-glow hover:shadow-[0_0_20px_rgba(0,240,255,0.6)]"
          aria-label="Send message"
          aria-disabled={isDisabled}
          aria-busy={isLoading}
          type="button"
        >
          <SendIcon className="w-3.5 xs:w-4 sm:w-4 md:w-4.5 h-3.5 xs:h-4 sm:h-4 md:h-4.5" aria-hidden={true} />
          <span className="sr-only">Send message</span>
        </button>
      </div>
      <p id="input-hint" className="text-[10px] xs:text-xs sm:text-xs md:text-xs text-text-muted mt-1 xs:mt-1.5 sm:mt-2 text-center px-1 xs:px-2">
        <span className="text-neon-cyan">[</span> Press Enter to send • Shift+Enter for new line <span className="text-neon-cyan">]</span>
      </p>
    </div>
  )
}

