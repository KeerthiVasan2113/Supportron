import React from 'react'
import { Message } from '@/types/chat'
import { Avatar } from './Avatar'

interface MessageBubbleProps {
  message: Message
  'aria-label'?: string
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, 'aria-label': ariaLabel }) => {
  const isUser = message.role === 'user'
  const senderName = isUser ? 'You' : 'Supportron'

  return (
    <div
      className={`flex w-full mb-1 sm:mb-1.5 md:mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}
      role="article"
      aria-label={ariaLabel || `Message from ${senderName}`}
    >
      <div
        className={`max-w-[92%] xs:max-w-[88%] sm:max-w-[82%] md:max-w-[78%] lg:max-w-[72%] xl:max-w-[68%] 2xl:max-w-[65%] 3xl:max-w-[60%] rounded-2xl p-3 xs:p-3.5 sm:p-4 md:p-4 lg:p-4 ${
          isUser
            ? 'bg-telegram-blue text-white shadow-lg'
            : 'bg-telegram-surface text-text-primary shadow-md'
        }`}
        style={{
          borderRadius: isUser ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
        }}
      >
        {isUser ? (
          <div className="flex items-start gap-1.5 xs:gap-2 sm:gap-2.5 md:gap-3 flex-row-reverse">
            <Avatar type={message.role} className="hidden xs:flex flex-shrink-0" />
            <div className="flex-1 min-w-0 text-right">
              <p className="text-[10px] xs:text-xs sm:text-xs md:text-sm font-semibold mb-1 xs:mb-1.5 sm:mb-2 text-white/90 uppercase tracking-wide">
                {senderName}
              </p>
              <p className="text-xs xs:text-sm sm:text-sm md:text-base lg:text-base leading-relaxed whitespace-pre-wrap text-white break-words hyphens-auto">
                {message.content}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-start gap-1.5 xs:gap-2 sm:gap-2.5 md:gap-3 flex-row">
            <Avatar type={message.role} className="hidden xs:flex flex-shrink-0" />
            <div className="flex-1 min-w-0 text-left">
              <p className="text-[10px] xs:text-xs sm:text-xs md:text-sm font-semibold mb-1 xs:mb-1.5 sm:mb-2 text-text-secondary uppercase tracking-wide">
                {senderName}
              </p>
              <p className="text-xs xs:text-sm sm:text-sm md:text-base lg:text-base leading-relaxed whitespace-pre-wrap text-text-primary break-words hyphens-auto">
                {message.content}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

