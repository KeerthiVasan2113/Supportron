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

// Code Block Component with Copy Functionality
interface CodeBlockProps {
  code: string
  language?: string
}

const CodeBlock = ({ code, language }: CodeBlockProps) => {
  const [isCopied, setIsCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (error) {
      console.error('Copy failed:', error)
    }
  }

  return (
    <div className="relative group my-4">
      <pre className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-4 pr-12 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow leading-relaxed">
        <code className="block whitespace-pre">{code}</code>
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 bg-slate-800/90 hover:bg-slate-700 border border-cyan-500/30 rounded text-cyan-300 hover:text-cyan-200 z-10 shadow-lg"
        aria-label="Copy code to clipboard"
        title={isCopied ? "Copied!" : "Copy code"}
      >
        {isCopied ? (
          <Check className="w-4 h-4 text-green-400" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
      </button>
    </div>
  )
}

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
    
    // Pre-process: Split text on list patterns even if they're in the same paragraph
    // This handles cases where list items are in continuous text without newlines
    // Only split if not already at the start of a line
    normalizedText = normalizedText.replace(/([^\n])(\d+[\.\)]|[-*•])\s+/g, '$1\n$2 ')
    
    // Split by lines for processing
    const lines = normalizedText.split('\n')
    const elements: JSX.Element[] = []

    let inBlock = false
    let blockLang = ''
    let blockLines: string[] = []
    let blockStartIndex = 0
    let regularTextBuffer: string[] = []

    // Helper to detect if a line is a heading (plain text headings)
    const isPlainTextHeading = (line: string): boolean => {
      const trimmed = line.trim()
      // Check for common heading patterns in plain text
      // - Ends with colon and is short
      // - All caps and short
      // - Starts with "Here are", "The following", etc.
      if (trimmed.endsWith(':') && trimmed.length < 80 && trimmed.split(' ').length <= 8) {
        return true
      }
      if (trimmed === trimmed.toUpperCase() && trimmed.length < 60 && trimmed.split(' ').length <= 6) {
        return true
      }
      if (/^(Here are|The following|Steps to|How to|Note:|Important:|Warning:)/i.test(trimmed)) {
        return true
      }
      return false
    }

    // Helper to flush regular text buffer
    const flushRegularText = () => {
      if (regularTextBuffer.length > 0) {
        const textContent = regularTextBuffer.join('\n')
        // Process inline markdown in the buffered text
        processRegularText(textContent, blockStartIndex)
        regularTextBuffer = []
      }
    }

      // Process regular text (non-code block content)
      const processRegularText = (text: string, index: number) => {
        if (!text.trim()) {
          elements.push(<div key={`sp-${index}`} className="h-3" />)
          return
        }

        // Check for markdown headings first
        if (text.startsWith('### ')) {
          elements.push(
            <h3 key={`h3-${index}`} className="text-base sm:text-lg font-semibold mt-6 mb-3 text-cyan-300 leading-tight">
              {text.substring(4).trim()}
            </h3>
          )
          return
        }

        if (text.startsWith('## ')) {
          elements.push(
            <h2
              key={`h2-${index}`}
              className="text-lg sm:text-xl font-bold mt-8 mb-4 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent leading-tight"
            >
              {text.substring(3).trim()}
            </h2>
          )
          return
        }

        // Check for plain text headings (lines ending with colon, short lines, etc.)
        if (isPlainTextHeading(text)) {
          const headingText = text.trim().replace(/:$/, '') // Remove trailing colon
          elements.push(
            <h3 key={`h3-plain-${index}`} className="text-base sm:text-lg font-semibold mt-6 mb-4 text-cyan-300 leading-tight">
              {headingText}
            </h3>
          )
          return
        }

        // Check for list items (numbered or bulleted) - improved regex
        // Matches: "1. text", "1) text", "- text", "* text", "• text"
        // Also handles cases like "1. Check Email Server Configuration:"
        // More flexible: allows for optional space after number
        const listMatch = text.match(/^(\d+[\.\)]|[-*•])\s+(.+)$/)
        if (listMatch) {
          let listContent = listMatch[2].trim()
          const isNumbered = /^\d+[\.\)]/.test(listMatch[1])
          const listMarker = listMatch[1].trim()
          
          // Remove trailing colon if present (common in list items)
          if (listContent.endsWith(':')) {
            listContent = listContent.slice(0, -1).trim()
          }
          
          elements.push(
            <div key={`li-${index}`} className="flex items-start mb-3 ml-1">
              <span className="text-cyan-400 mr-3 mt-1 flex-shrink-0 font-semibold min-w-[1.75rem] text-right">
                {isNumbered ? `${listMarker}` : '•'}
              </span>
              <span className="text-slate-200 text-sm sm:text-base leading-relaxed flex-1 mt-0.5">
                {listContent}
              </span>
            </div>
          )
          return
        }
        

      // Process inline markdown
      let processed = text
      let placeholderIndex = 0
      const placeholders: Record<string, JSX.Element> = {}

      // Process bold text - both markdown (**text**) and plain text patterns
      // Markdown bold
      const boldRegex = /\*\*([^*]+)\*\*/g
      processed = processed.replace(boldRegex, (match, content) => {
        const key = `__BOLD_${placeholderIndex}__`
        placeholders[key] = (
          <strong key={key} className="font-semibold text-cyan-300">
            {content}
          </strong>
        )
        placeholderIndex++
        return key
      })
      
      // Also detect important terms that should be highlighted (SPF, DKIM, DMARC, etc.)
      // This helps highlight technical terms even if not in markdown
      const importantTerms = ['SPF', 'DKIM', 'DMARC', 'SMTP', 'MX', 'DNS', 'IP', 'ISP', 'RBL', 'MXToolbox', 'Spamhaus']
      importantTerms.forEach(term => {
        const termRegex = new RegExp(`\\b(${term})\\b`, 'gi')
        let lastIndex = 0
        let match
        while ((match = termRegex.exec(processed)) !== null) {
          // Skip if already inside a placeholder
          const beforeMatch = processed.substring(0, match.index)
          if (!beforeMatch.includes('__') || !beforeMatch.match(/__[A-Z_]+\d+__$/)) {
            const key = `__TERM_${placeholderIndex}__`
            placeholders[key] = (
              <strong key={key} className="font-semibold text-cyan-300">
                {match[0]}
              </strong>
            )
            processed = processed.substring(0, match.index) + key + processed.substring(match.index + match[0].length)
            termRegex.lastIndex = match.index + key.length
            placeholderIndex++
          }
        }
      })

      // Process inline code (single backticks, not triple)
      const findInlineCode = (text: string): Array<{start: number, end: number, content: string}> => {
        const matches: Array<{start: number, end: number, content: string}> = []
        let i = 0
        while (i < text.length) {
          if (text[i] === '`') {
            // Check if it's triple backticks
            if (i + 2 < text.length && text[i + 1] === '`' && text[i + 2] === '`') {
              i += 3
              continue
            }
            // Found single backtick
            const start = i
            i++
            let content = ''
            while (i < text.length && text[i] !== '`') {
              content += text[i]
              i++
            }
            if (i < text.length && text[i] === '`') {
              if (i + 1 >= text.length || text[i + 1] !== '`') {
                matches.push({ start, end: i + 1, content })
              }
              i++
            } else {
              i = start + 1
            }
          } else {
            i++
          }
        }
        return matches
      }

      const inlineCodeMatches = findInlineCode(processed)
      for (let i = inlineCodeMatches.length - 1; i >= 0; i--) {
        const match = inlineCodeMatches[i]
        const key = `__CODE_${placeholderIndex}__`
        placeholders[key] = (
          <code
            key={key}
            className="bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.5 rounded text-xs sm:text-sm font-mono leading-normal"
          >
            {match.content}
          </code>
        )
        processed = processed.substring(0, match.start) + key + processed.substring(match.end)
        placeholderIndex++
      }

      const parts = processed.split(/(__BOLD_\d+__|__CODE_\d+__|__TERM_\d+__)/g)
      const html = parts.map((p, i) => placeholders[p] || p)

      elements.push(
        <p key={`p-${index}`} className="mb-4 text-sm sm:text-base text-slate-200 leading-7">
          {html}
        </p>
      )
    }

    lines.forEach((line, index) => {
      // Check for code block markers (``` or ```language) - check trimmed version
      const trimmedLine = line.trim()
      
      // Check if this line is a code block marker
      // Matches: ``` or ```language (where language is alphanumeric, dash, or underscore)
      const isCodeBlockMarker = trimmedLine === '```' || 
        (trimmedLine.startsWith('```') && /^```[a-zA-Z0-9_-]*$/.test(trimmedLine))
      
      if (isCodeBlockMarker) {
        if (inBlock) {
          // Closing code block - flush any pending regular text first
          flushRegularText()
          
          // Save accumulated code lines (trim empty lines from start/end but keep internal formatting)
          const trimmedBlockLines = blockLines
            .map((l, i) => {
              // Remove leading empty lines
              if (i === 0 && !l.trim()) return null
              // Remove trailing empty lines
              if (i === blockLines.length - 1 && !l.trim()) return null
              return l
            })
            .filter((l): l is string => l !== null)
          
          if (trimmedBlockLines.length > 0) {
            const codeContent = trimmedBlockLines.join('\n')
            const codeBlockId = `code-${blockStartIndex}-${Date.now()}`
            elements.push(
              <CodeBlock 
                key={codeBlockId}
                code={codeContent}
                language={blockLang}
              />
            )
          } else {
            // Empty code block
            elements.push(
              <pre
                key={`code-empty-${blockStartIndex}`}
                className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-4 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow my-4"
              >
                <code className="text-cyan-400/50 italic">(empty code block)</code>
              </pre>
            )
          }
          inBlock = false
          blockLines = []
          blockLang = ''
        } else {
          // Opening code block - flush any pending regular text first
          flushRegularText()
          
          // Extract language if present
          const langMatch = trimmedLine.match(/^```([a-zA-Z0-9_-]*)$/)
          blockLang = langMatch ? langMatch[1] : ''
          inBlock = true
          blockStartIndex = index
          blockLines = []
        }
        return // Skip processing the marker line itself
      }

      // If we're inside a code block, check if this line is explanatory text
      if (inBlock) {
        const trimmedLower = trimmedLine.toLowerCase()
        // Detect explanatory text patterns that should be outside code blocks
        const isExplanatoryText = (
          trimmedLine.startsWith('(Note:') ||
          trimmedLine.startsWith('(Note ') ||
          trimmedLine.startsWith('Note:') ||
          trimmedLine.match(/^\(Note[:\s]/i) ||
          trimmedLine.match(/^\(This\s+(example|command|method|approach)/i) ||
          (trimmedLine.startsWith('(') && trimmedLine.includes(')') && 
           trimmedLine.length < 200 &&
           !trimmedLine.includes('{') && !trimmedLine.includes('}') &&
           !trimmedLine.includes('=') && !trimmedLine.includes(';') &&
           (trimmedLower.includes('note') || trimmedLower.includes('example') || 
            trimmedLower.includes('for ') || trimmedLower.includes('when ') ||
            trimmedLower.includes('used') || trimmedLower.includes('machine') ||
            trimmedLower.includes('scenario') || trimmedLower.includes('domain-joined') ||
            trimmedLower.includes('standalone') || trimmedLower.includes('dual-boot')))
        )
        
        if (isExplanatoryText) {
          // Close code block, add explanatory text as regular text
          if (blockLines.length > 0) {
            const codeContent = blockLines.join('\n')
            const codeBlockId = `code-${blockStartIndex}-${Date.now()}`
            elements.push(
              <CodeBlock 
                key={codeBlockId}
                code={codeContent}
                language={blockLang}
              />
            )
            blockLines = []
            inBlock = false
            blockLang = ''
          }
          // Add explanatory text as regular text
          regularTextBuffer.push(line)
          return
        }
        
        // Regular code line - accumulate it
        blockLines.push(line)
        return
      }

      // Regular text - add to buffer
      regularTextBuffer.push(line)

    })

    // Flush any remaining regular text
    flushRegularText()

    // If code block left open at end (malformed markdown) - render it anyway
    if (inBlock) {
      if (blockLines.length > 0) {
        const codeContent = blockLines.join('\n')
        const codeBlockId = `code-final-${Date.now()}`
        elements.push(
          <CodeBlock 
            key={codeBlockId}
            code={codeContent}
            language={blockLang}
          />
        )
      } else {
        elements.push(
          <pre
            key="final-block-empty"
            className="bg-slate-900/80 border border-cyan-500/30 text-cyan-100 p-4 rounded-lg overflow-x-auto text-xs sm:text-sm font-mono cyber-glow my-4"
          >
            <code className="text-cyan-400/50 italic">(incomplete code block)</code>
          </pre>
        )
      }
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
          <div className="relative">
            {/* Edit (user message) - positioned relative to message bubble */}
            {isUser && onEdit && !isEditing && (
              <button
                onClick={handleEdit}
                className="absolute opacity-0 group-hover:opacity-100 transition p-1.5 text-cyan-400/70 hover:text-cyan-300 hover:bg-cyan-500/20 rounded -left-8 top-0 z-10"
                aria-label="Edit message"
                title="Edit message"
              >
                <Edit2 className="w-4 h-4" />
              </button>
            )}
            <div
              className={`rounded-2xl px-6 py-5 text-base max-w-full ${
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
              <div className="break-words overflow-wrap-anywhere message-content">
                {renderMarkdown(message.content)}
              </div>
            ) : (
              <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere leading-relaxed message-content">{message.content}</div>
            )}
            </div>
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