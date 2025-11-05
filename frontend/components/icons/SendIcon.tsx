import React from 'react'

interface SendIconProps {
  className?: string
  'aria-hidden'?: boolean
}

export const SendIcon: React.FC<SendIconProps> = ({ className = 'w-5 h-5', 'aria-hidden': ariaHidden = true }) => (
  <svg
    className={className}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    aria-hidden={ariaHidden}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
    />
  </svg>
)

