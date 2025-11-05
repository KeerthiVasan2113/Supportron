import React from 'react'

interface StatusIndicatorProps {
  status?: 'online' | 'offline' | 'away'
  label?: string
  className?: string
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  status = 'online', 
  label = 'Online & Ready',
  className = '' 
}) => {
  const statusColors = {
    online: 'bg-neon-green',
    offline: 'bg-gray-500',
    away: 'bg-yellow-500'
  }

  return (
    <div className={`flex items-center gap-2 ${className}`} role="status" aria-live="polite">
      <div 
        className={`w-2 h-2 rounded-full ${statusColors[status]} animate-pulse relative`}
        aria-hidden="true"
      >
        {status === 'online' && (
          <span className="absolute inset-0 rounded-full bg-neon-green animate-ping opacity-75"></span>
        )}
      </div>
      <span className="text-sm text-text-secondary font-medium">
        <span className="text-neon-cyan">[</span> {label} <span className="text-neon-cyan">]</span>
      </span>
    </div>
  )
}

