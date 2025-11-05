'use client'

import ChatInterface from '@/components/ChatInterface'
import { StatusIndicator } from '@/components/StatusIndicator'

export default function Home() {
  return (
    <main 
      className="flex min-h-screen w-full flex-col items-center justify-center p-1.5 xs:p-2 sm:p-3 md:p-4 lg:p-6 xl:p-8 pt-safe-top pb-safe-bottom px-safe-left px-safe-right"
      role="main"
      aria-label="Supportron IT Tech Support Chatbot"
    >
      <div className="w-full max-w-6xl 3xl:max-w-7xl 4xl:max-w-8xl flex flex-col h-[calc(100dvh-0.75rem)] xs:h-[calc(100dvh-1rem)] sm:h-[calc(100dvh-1.5rem)] md:h-[calc(100dvh-2rem)] lg:h-[calc(100dvh-2.5rem)] xl:h-[calc(100dvh-3rem)]">
        <header 
          className="mb-2 xs:mb-3 sm:mb-4 md:mb-5 lg:mb-6 text-center flex-shrink-0"
          role="banner"
          aria-label="Application header"
        >
          <h1 className="text-xl xs:text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold mb-0.5 xs:mb-1 sm:mb-1.5 md:mb-2 text-text-primary tracking-tight leading-tight bg-gradient-to-r from-telegram-blue to-accent bg-clip-text text-transparent">
            Supportron
          </h1>
          <p className="text-text-secondary text-xs xs:text-sm sm:text-base md:text-lg lg:text-xl font-medium px-1 xs:px-2 sm:px-3 md:px-4">
            Advanced IT Tech Support AI Assistant
          </p>
          <div className="mt-1.5 xs:mt-2 sm:mt-3 md:mt-4 flex items-center justify-center">
            <StatusIndicator />
          </div>
        </header>
        <section 
          className="flex-1 min-h-0 w-full"
          aria-label="Chat interface"
        >
          <ChatInterface />
        </section>
      </div>
    </main>
  )
}

