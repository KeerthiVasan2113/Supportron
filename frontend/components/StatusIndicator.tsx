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
    online: 'bg-success',
    offline: 'bg-gray-500',
    away: 'bg-yellow-500'
  }

  return (
    <div className={`flex items-center gap-2 ${className}`} role="status" aria-live="polite">
      <div 
        className={`w-2 h-2 rounded-full ${statusColors[status]} animate-pulse`}
        aria-hidden="true"
      />
      <span className="text-sm text-text-muted font-medium">
        {label}
      </span>
    </div>
  )
}

