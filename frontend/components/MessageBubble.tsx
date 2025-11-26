'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { Message } from '@/types/chat'
import {
  FileText,
  ChevronDown,
  ChevronUp,
  Copy,
  RefreshCw,
  Edit2,
  Check,
  X,
  Loader2,
} from 'lucide-react'
import { formatElapsedTime, calculateElapsedTime } from '@/utils/timer'

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
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [shouldAnimate, setShouldAnimate] = useState(false)

  // Animation on NEW user messages only
  useEffect(() => {
    if (isUser && message.content) {
      setShouldAnimate(true)
      const timer = setTimeout(() => setShouldAnimate(false), 800)
      return () => clearTimeout(timer)
    }
  }, [isUser, message.id])

  // Loading timer logic using universal timer utility
  useEffect(() => {
    if (message.isLoading && message.loadingStartTime) {
      const i = setInterval(() => {
        const elapsed = calculateElapsedTime(message.loadingStartTime!)
        setElapsedSeconds(elapsed)
      }, 100)
      return () => clearInterval(i)
    } else if (!message.isLoading && message.responseTime) {
      // When loading completes, use the responseTime from the message
      setElapsedSeconds(message.responseTime)
    } else {
      setElapsedSeconds(0)
    }
  }, [message.isLoading, message.loadingStartTime, message.responseTime])
  
  // Format elapsed time using universal timer utility
  // Use responseTime if available and not loading, otherwise use live elapsedSeconds
  const timeToFormat = (!message.isLoading && message.responseTime) 
    ? message.responseTime 
    : elapsedSeconds
  const formattedTime = formatElapsedTime(timeToFormat)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (error) {
      console.error('Copy failed:', error)
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

  // --- Markdown Renderer (improved code block handling) ---
  const renderMarkdown = (text: string) => {
    // First, normalize the text to handle any malformed code blocks
    let normalizedText = text
    
    // Split by lines for processing
    const lines = normalizedText.split('\n')
    const elements: JSX.Element[] = []

    let inBlock = false
    let blockLang = ''
    let blockLines: string[] = []
    let blockStartIndex = 0

    lines.forEach((line, index) => {
      // Check for code block markers (``` or ```language) - check trimmed version
      const trimmedLine = line.trim()
      
      // Check if this line is a code block marker
      // Matches: ``` or ```language (where language is alphanumeric, dash, or underscore)
      const isCodeBlockMarker = trimmedLine === '```' || 
        (trimmedLine.startsWith('```') && /^```[a-zA-Z0-9_-]*$/.test(trimmedLine))
      
      if (isCodeBlockMarker) {
        if (inBlock) {
          // Closing code block - save accumulated lines
          if (blockLines.length > 0) {
            elements.push(
              <pre
                key={`code-${blockStartIndex}`}
                className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-3 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow my-2"
              >
                <code>{blockLines.join('\n')}</code>
              </pre>
            )
          } else {
            // Empty code block - still render it but with a note
            elements.push(
              <pre
                key={`code-empty-${blockStartIndex}`}
                className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-3 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow my-2"
              >
                <code className="text-cyan-400/50 italic">(empty code block)</code>
              </pre>
            )
          }
          inBlock = false
          blockLines = []
          blockLang = ''
        } else {
          // Opening code block - extract language if present
          const langMatch = trimmedLine.match(/^```([a-zA-Z0-9_-]*)$/)
          blockLang = langMatch ? langMatch[1] : ''
          inBlock = true
          blockStartIndex = index
          blockLines = []
        }
        return // Skip processing the marker line itself
      }

      // If we're inside a code block, accumulate lines (preserve original formatting)
      if (inBlock) {
        blockLines.push(line)
        return
      }

      // ### Heading
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${index}`} className="text-base sm:text-lg font-semibold mt-4 mb-2 text-cyan-300">
            {line.substring(4)}
          </h3>
        )
        return
      }

      // ## Heading
      if (line.startsWith('## ')) {
        elements.push(
          <h2
            key={`h2-${index}`}
            className="text-lg sm:text-xl font-bold mt-6 mb-3 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent"
          >
            {line.substring(3)}
          </h2>
        )
        return
      }

      // Blank line → spacing only
      if (line.trim() === '') {
        elements.push(<div key={`sp-${index}`} className="h-2" />)
        return
      }

      // Process inline markdown (only if not in code block)
      let html: (string | JSX.Element)[] = []

      const boldRegex = /\*\*([^*]+)\*\*/g
      
      // Helper function to find inline code (single backticks, not triple backticks)
      const findInlineCode = (text: string): Array<{start: number, end: number, content: string}> => {
        const matches: Array<{start: number, end: number, content: string}> = []
        let i = 0
        while (i < text.length) {
          if (text[i] === '`') {
            // Check if it's triple backticks (code block marker)
            if (i + 2 < text.length && text[i + 1] === '`' && text[i + 2] === '`') {
              // Skip triple backticks
              i += 3
              continue
            }
            // Found single backtick - find matching closing backtick
            const start = i
            i++
            let content = ''
            while (i < text.length && text[i] !== '`') {
              content += text[i]
              i++
            }
            if (i < text.length && text[i] === '`') {
              // Found closing backtick - check it's not part of triple
              if (i + 1 >= text.length || text[i + 1] !== '`') {
                matches.push({ start, end: i + 1, content })
              }
              i++
            } else {
              // No closing backtick found, treat as regular text
              i = start + 1
            }
          } else {
            i++
          }
        }
        return matches
      }

      let processed = line
      let placeholderIndex = 0
      const placeholders: Record<string, JSX.Element> = {}

      // Process bold text first
      processed = processed.replace(boldRegex, (match, content) => {
        // Skip if this is inside a code block context (shouldn't happen here, but safety check)
        if (match.includes('```')) {
          return match
        }
        const key = `__BOLD_${placeholderIndex}__`
        placeholders[key] = (
          <strong key={key} className="font-semibold text-cyan-300">
            {content}
          </strong>
        )
        placeholderIndex++
        return key
      })

      // Process inline code using our helper function
      const inlineCodeMatches = findInlineCode(processed)
      // Process matches in reverse order to maintain indices
      for (let i = inlineCodeMatches.length - 1; i >= 0; i--) {
        const match = inlineCodeMatches[i]
        const key = `__CODE_${placeholderIndex}__`
        placeholders[key] = (
          <code
            key={key}
            className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-1 py-0.5 rounded text-xs sm:text-sm font-mono"
          >
            {match.content}
          </code>
        )
        // Replace the matched text with placeholder
        processed = processed.substring(0, match.start) + key + processed.substring(match.end)
        placeholderIndex++
      }

      const parts = processed.split(/(__BOLD_\d+__|__CODE_\d+__)/g)

      html = parts.map((p, i) => placeholders[p] || p)

      elements.push(
        <p key={`p-${index}`} className="mb-2 text-sm sm:text-base text-slate-200">
          {html}
        </p>
      )
    })

    // If code block left open at end (malformed markdown)
    if (inBlock && blockLines.length > 0) {
      elements.push(
        <pre
          key="final-block"
          className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-3 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow my-2"
        >
          <code>{blockLines.join('\n')}</code>
        </pre>
      )
    }

    return elements
  }

  const uniqueSources = message.sources
    ? Array.from(
        new Map(
          message.sources.map((s) => [
            s.source_file,
            {
              filename: s.source_file.replace('.pdf', '').replace(/_/g, ' '),
              original: s.source_file,
            },
          ])
        ).values()
      )
    : []

  return (
    <article
      className={`group flex items-start w-full px-2 sm:px-3 ${
        isUser ? 'ml-auto justify-end' : 'mr-auto space-x-3'
      } ${isUser && shouldAnimate ? 'animate-message-fly-in' : ''}`}
    >
      {/* Assistant avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-cyan-500 to-teal-500 cyber-glow ring-2 ring-cyan-500/50">
          <Image
            src="/icons/AI.png"
            alt="AI Assistant"
            width={32}
            height={32}
            className="w-full h-full object-cover"
            aria-hidden="true"
          />
        </div>
      )}

      {/* Message container */}
      <div className={`flex-1 ${isUser ? 'flex flex-col items-end relative' : ''}`}>
        {/* Edit (user message) */}
        {isUser && onEdit && !isEditing && (
          <button
            onClick={handleEdit}
            className="absolute opacity-0 group-hover:opacity-100 transition p-1 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded right-full mr-1"
          >
            <Edit2 className="w-4 h-4" />
          </button>
        )}

        {/* Editing mode */}
        {isEditing && isUser ? (
          <div className="w-full max-w-3xl">
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              onKeyDown={(e) => e.key === 'Escape' && handleCancelEdit()}
              className="w-full px-4 py-3 text-base border border-cyan-500/30 rounded-2xl glass-effect-light text-slate-200 focus:ring-2 focus:ring-cyan-500/50"
              rows={Math.min(editContent.split('\n').length, 10)}
            />

            <div className="flex items-center space-x-2 mt-2 justify-end">
              <button onClick={handleSaveEdit} className="p-1.5 text-cyan-400 hover:bg-cyan-500/20 rounded">
                <Check className="w-4 h-4" />
              </button>

              <button onClick={handleCancelEdit} className="p-1.5 text-red-400 hover:bg-red-500/20 rounded">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div
            className={`rounded-2xl px-4 py-3 text-base max-w-full ${
              isUser
                ? 'bg-gradient-to-r from-teal-500 to-cyan-500 text-white cyber-glow'
                : 'glass-effect-light text-slate-200 border border-cyan-500/20'
            }`}
            style={{ maxWidth: 'min(100%, 48rem)' }}
          >
            {!isUser && message.isLoading ? (
              <div className="flex items-center space-x-3 py-2">
                <Loader2 className="w-5 h-5 text-cyan-400 animate-spin flex-shrink-0" />
                <span className="text-cyan-300 font-medium whitespace-nowrap">⚙ Re-Inventing Solution! 🛠️</span>
                <span className="text-xs text-cyan-400/70 whitespace-nowrap" aria-label={`Elapsed time: ${formattedTime}`}>{formattedTime}</span>
              </div>
            ) : !isUser ? (
              <div className="prose prose-sm dark:prose-invert max-w-none break-words overflow-wrap-anywhere">{renderMarkdown(message.content)}</div>
            ) : (
              <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere">{message.content}</div>
            )}
          </div>
        )}

        {/* Footer actions */}
        {!isUser && !message.isLoading && (
          <div className="flex items-center space-x-3 mt-2 flex-wrap">
            {onRegenerate && !isGreeting && (
              <button className="p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded" onClick={() => onRegenerate(message.id)}>
                <RefreshCw className="w-4 h-4" />
              </button>
            )}

            {!isGreeting && (
              <button className="p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded" onClick={handleCopy}>
                {isCopied ? <Check className="w-4 h-4 text-cyan-400" /> : <Copy className="w-4 h-4" />}
              </button>
            )}

            {message.responseTime && (
              <span className="text-xs text-cyan-400/50 font-mono" aria-label={`Response time: ${formattedTime}`}>
                {formattedTime}
              </span>
            )}

            {uniqueSources.length > 0 && (
              <div className="relative">
                <button
                  className="flex items-center space-x-1 text-xs text-cyan-400/70 hover:text-cyan-300 rounded"
                  onClick={() => setSourcesOpen(!sourcesOpen)}
                >
                  <FileText className="w-3 h-3" />
                  <span>{uniqueSources.length} source(s)</span>
                  {sourcesOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>

                {sourcesOpen && (
                  <div className="absolute bottom-full left-0 mb-2 glass-effect-light border border-cyan-500/20 rounded-lg p-2 min-w-[200px] z-10">
                    {uniqueSources.map((s, i) => (
                      <div key={i} className="text-xs text-cyan-300/80 flex items-center space-x-1">
                        <FileText className="w-3 h-3" />
                        <span className="truncate">{s.filename}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-teal-500 to-cyan-500 cyber-glow ml-1 ring-2 ring-teal-500/50">
          <Image
            src="/icons/User.png"
            alt="User"
            width={32}
            height={32}
            className="w-full h-full object-cover"
            aria-hidden="true"
          />
        </div>
      )}
    </article>
  )
}

export default MessageBubble