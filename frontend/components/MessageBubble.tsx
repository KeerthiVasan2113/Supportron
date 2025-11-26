'use client'

import { useState, useEffect } from 'react'
import { Message } from '@/types/chat'
import { FileText, ChevronDown, ChevronUp, Copy, RefreshCw, Edit2, Check, X, Loader2 } from 'lucide-react'

interface MessageBubbleProps {
  message: Message
  onEdit?: (messageId: string, newContent: string) => void
  onRegenerate?: (messageId: string) => void
}

const MessageBubble = ({ message, onEdit, onRegenerate }: MessageBubbleProps) => {
  const isUser = message.role === 'user'
  const isGreeting = !isUser && message.id.startsWith('greeting-')
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(message.content)
  const [isCopied, setIsCopied] = useState(false)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [shouldAnimate, setShouldAnimate] = useState(false)

  // Trigger animation for new user messages
  useEffect(() => {
    if (isUser && message.content) {
      setShouldAnimate(true)
      // Remove animation class after animation completes to allow re-animation on edit
      const timer = setTimeout(() => setShouldAnimate(false), 800)
      return () => clearTimeout(timer)
    }
  }, [isUser, message.id])

  // Timer for loading state
  useEffect(() => {
    if (message.isLoading && message.loadingStartTime) {
      const interval = setInterval(() => {
        const elapsed = ((Date.now() - message.loadingStartTime!) / 1000).toFixed(1)
        setElapsedTime(parseFloat(elapsed))
      }, 100)
      return () => clearInterval(interval)
    } else {
      setElapsedTime(0)
    }
  }, [message.isLoading, message.loadingStartTime])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
    setEditContent(message.content)
  }

  const handleSaveEdit = () => {
    if (onEdit && editContent.trim()) {
      onEdit(message.id, editContent.trim())
      setIsEditing(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditContent(message.content)
  }

  // Simple markdown renderer
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n')
    const elements: JSX.Element[] = []
    let inCodeBlock = false
    let codeBlockContent: string[] = []
    let codeBlockLanguage = ''

    lines.forEach((line, index) => {
      // Handle code blocks
      if (line.startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          elements.push(
            <pre key={`code-${index}`} className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-2 sm:p-4 rounded-lg overflow-x-auto my-2 sm:my-4 text-xs sm:text-sm font-mono cyber-glow">
              <code>{codeBlockContent.join('\n')}</code>
            </pre>
          )
          codeBlockContent = []
          inCodeBlock = false
          codeBlockLanguage = ''
        } else {
          // Start code block
          codeBlockLanguage = line.replace('```', '').trim()
          inCodeBlock = true
        }
        return
      }

      if (inCodeBlock) {
        codeBlockContent.push(line)
        return
      }

      // Handle headings
      if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${index}`} className="text-lg sm:text-xl font-bold mt-4 sm:mt-6 mb-2 sm:mb-3 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
            {line.replace('## ', '')}
          </h2>
        )
        return
      }

      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${index}`} className="text-base sm:text-lg font-semibold mt-3 sm:mt-4 mb-1 sm:mb-2 text-cyan-300">
            {line.replace('### ', '')}
          </h3>
        )
        return
      }

      // Handle empty lines
      if (line.trim() === '') {
        elements.push(<br key={`br-${index}`} />)
        return
      }

      // Handle bold text and inline code
      const boldRegex = /\*\*([^*]+)\*\*/g
      const codeRegex = /`([^`]+)`/g
      const parts: (string | JSX.Element)[] = []
      let processedLine = line
      let partIndex = 0

      // First, replace bold text with placeholders
      const boldPlaceholders: { [key: string]: JSX.Element } = {}
      processedLine = processedLine.replace(boldRegex, (match, text) => {
             const placeholder = `__BOLD_${partIndex}__`
               boldPlaceholders[placeholder] = (
                 <strong key={`bold-${partIndex}`} className="font-semibold text-cyan-300 text-sm sm:text-base">
                   {text}
                 </strong>
               )
        partIndex++
        return placeholder
      })

      // Then, replace inline code with placeholders
      const codePlaceholders: { [key: string]: JSX.Element } = {}
      processedLine = processedLine.replace(codeRegex, (match, text) => {
             const placeholder = `__CODE_${partIndex}__`
               codePlaceholders[placeholder] = (
                 <code key={`inline-code-${partIndex}`} className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-1 sm:px-1.5 py-0.5 rounded text-xs sm:text-sm font-mono">
                   {text}
                 </code>
               )
        partIndex++
        return placeholder
      })

      // Split by placeholders and reconstruct
      const allPlaceholders = { ...boldPlaceholders, ...codePlaceholders }
      const placeholderRegex = /(__(?:BOLD|CODE)_\d+__)/g
      let lastIndex = 0
      let match

      while ((match = placeholderRegex.exec(processedLine)) !== null) {
        if (match.index > lastIndex) {
          const text = processedLine.substring(lastIndex, match.index)
          if (text) parts.push(text)
        }
        if (allPlaceholders[match[0]]) {
          parts.push(allPlaceholders[match[0]])
        }
        lastIndex = match.index + match[0].length
      }
      if (lastIndex < processedLine.length) {
        parts.push(processedLine.substring(lastIndex))
      }

             if (parts.length > 0) {
               elements.push(
                 <p key={`p-${index}`} className="mb-1 sm:mb-2 text-sm sm:text-base text-slate-200">
                   {parts}
                 </p>
               )
             } else {
               elements.push(
                 <p key={`p-${index}`} className="mb-1 sm:mb-2 text-sm sm:text-base text-slate-200">
                   {line}
                 </p>
               )
             }
    })

           // Handle any remaining code block
           if (inCodeBlock && codeBlockContent.length > 0) {
             elements.push(
               <pre key="code-final" className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-2 sm:p-4 rounded-lg overflow-x-auto my-2 sm:my-4 text-xs sm:text-sm font-mono cyber-glow">
                 <code>{codeBlockContent.join('\n')}</code>
               </pre>
             )
           }

           return elements.length > 0 ? elements : <p className="text-slate-200">{text}</p>
  }

  // Get unique source files (brief)
  const uniqueSources = message.sources
    ? Array.from(new Set(message.sources.map(s => s.source_file)))
        .map(filename => {
          const source = message.sources!.find(s => s.source_file === filename)
          return {
            filename: filename.replace('.pdf', '').replace(/_/g, ' '),
            original: filename,
            distance: source?.distance
          }
        })
    : []

  return (
    <article 
      className={`group flex items-start max-w-3xl w-full px-2 sm:px-4 ${isUser ? 'ml-auto' : 'mr-auto space-x-2 sm:space-x-3'} ${isUser && shouldAnimate ? 'animate-message-fly-in' : ''}`}
      role="article"
      aria-label={isUser ? "Your message" : "Assistant response"}
    >
      {/* Avatar for Assistant (left side) */}
      {!isUser && (
        <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-cyan-500 to-teal-500 cyber-glow" aria-hidden="true">
          <svg
            className="w-4 h-4 sm:w-5 sm:h-5 text-white"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
      )}

      {/* Message Content */}
      <div className={`flex-1 ${isUser ? 'flex flex-col items-end relative' : ''}`}>
        {/* Edit Button (User messages only) - Faded, visible on hover - positioned absolutely next to message */}
        {isUser && onEdit && !isEditing && (
          <button
            onClick={handleEdit}
            aria-label="Edit message"
            className="absolute opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded right-full mr-1 sm:mr-1.5 top-0 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            title="Edit"
          >
            <Edit2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
          </button>
        )}
        {isEditing && isUser ? (
          <div className="w-full max-w-3xl" role="dialog" aria-label="Edit message">
            <label htmlFor={`edit-message-${message.id}`} className="sr-only">
              Edit your message
            </label>
            <textarea
              id={`edit-message-${message.id}`}
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  handleCancelEdit()
                }
              }}
              className="w-full px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border border-cyan-500/30 rounded-xl sm:rounded-2xl glass-effect-light text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 resize-none"
              rows={Math.min(editContent.split('\n').length, 10)}
              aria-label="Edit message text"
            />
            <div className="flex items-center space-x-2 mt-2 justify-end" role="group" aria-label="Edit actions">
              <button
                onClick={handleSaveEdit}
                aria-label="Save changes"
                className="p-1.5 text-cyan-400 hover:bg-cyan-500/20 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                title="Save"
              >
                <Check className="w-4 h-4" aria-hidden="true" />
              </button>
              <button
                onClick={handleCancelEdit}
                aria-label="Cancel editing"
                className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-red-500/50"
                title="Cancel"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        ) : (
          <div
            className={`rounded-xl sm:rounded-2xl px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base ${
              isUser
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white cyber-glow'
                : 'glass-effect-light text-slate-200 border border-cyan-500/20'
            }`}
          >
            {!isUser && message.isLoading ? (
              <div className="flex items-center space-x-3 py-2" role="status" aria-live="polite" aria-label="Generating response">
                <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 text-cyan-400 animate-spin" aria-hidden="true" />
                <div className="flex flex-col">
                  <span className="text-cyan-300 font-medium">Re-Inventing Solutions 💡</span>
                  <span className="text-xs text-cyan-400/70 mt-0.5" aria-label={`Elapsed time: ${elapsedTime} seconds`}>{elapsedTime}s</span>
                </div>
              </div>
            ) : !isUser ? (
              <div className="prose prose-sm dark:prose-invert max-w-none" role="article">
                {renderMarkdown(message.content)}
              </div>
            ) : (
              <div className="whitespace-pre-wrap break-words">{message.content}</div>
            )}
          </div>
        )}

        {/* Footer Actions - Regenerate, Copy, Response Time, Sources */}
        {!isUser && !message.isLoading && (
          <div className="flex items-center space-x-2 sm:space-x-3 mt-2 flex-wrap">
            {/* Regenerate - Hidden for greeting messages */}
            {onRegenerate && !isGreeting && (
              <button
                onClick={() => onRegenerate(message.id)}
                aria-label="Regenerate response"
                className="p-1 sm:p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                title="Regenerate"
              >
                <RefreshCw className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
              </button>
            )}
            
            {/* Copy - Hidden for greeting messages */}
            {!isGreeting && (
              <button
                onClick={handleCopy}
                aria-label={isCopied ? "Copied to clipboard" : "Copy message"}
                aria-live="polite"
                className="p-1 sm:p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                title="Copy"
              >
                {isCopied ? (
                  <Check className="w-3 h-3 sm:w-4 sm:h-4 text-cyan-400" aria-hidden="true" />
                ) : (
                  <Copy className="w-3 h-3 sm:w-4 sm:h-4" aria-hidden="true" />
                )}
              </button>
            )}
            
            {/* Response Time */}
            {message.responseTime && (
              <span className="text-xs text-cyan-400/50 font-mono" aria-label={`Response time: ${message.responseTime} seconds`}>
                {message.responseTime}s
              </span>
            )}
            
            {/* Sources Dropdown */}
            {uniqueSources.length > 0 && (
              <div className="relative">
                <button
                  onClick={() => setSourcesOpen(!sourcesOpen)}
                  aria-expanded={sourcesOpen}
                  aria-controls={`sources-${message.id}`}
                  aria-label={`${sourcesOpen ? 'Hide' : 'Show'} ${uniqueSources.length} source${uniqueSources.length !== 1 ? 's' : ''}`}
                  className="flex items-center space-x-1 text-xs text-cyan-400/70 hover:text-cyan-300 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50 rounded"
                >
                  <FileText className="w-3 h-3" aria-hidden="true" />
                  <span>{uniqueSources.length} source{uniqueSources.length !== 1 ? 's' : ''}</span>
                  {sourcesOpen ? (
                    <ChevronUp className="w-3 h-3" aria-hidden="true" />
                  ) : (
                    <ChevronDown className="w-3 h-3" aria-hidden="true" />
                  )}
                </button>
                {sourcesOpen && (
                  <div 
                    id={`sources-${message.id}`}
                    className="absolute bottom-full left-0 mb-2 glass-effect-light border border-cyan-500/20 rounded-lg p-2 space-y-1 min-w-[200px] z-10"
                    role="list"
                    aria-label="Source documents"
                  >
                    {uniqueSources.map((source, index) => (
                      <div
                        key={index}
                        className="text-xs text-cyan-300/80 flex items-center space-x-1"
                        role="listitem"
                      >
                        <FileText className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
                        <span className="truncate">{source.filename}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </div>

      {/* Avatar for User (right side) */}
      {isUser && (
        <div className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center bg-gradient-to-br from-teal-500 to-cyan-500 cyber-glow ml-1 sm:ml-1.5" aria-hidden="true">
          <svg
            className="w-4 h-4 sm:w-5 sm:h-5 text-white"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      )}
    </div>
  )
}

export default MessageBubble
