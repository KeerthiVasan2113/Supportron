import React from 'react'
import Image from 'next/image'
import { AvatarIcon } from './icons/AvatarIcon'
import iconImage from '../Assets/icon.png'

interface AvatarProps {
  type: 'assistant' | 'user'
  className?: string
}

export const Avatar: React.FC<AvatarProps> = ({ type, className = '' }) => {
  const baseClasses = 'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border overflow-hidden relative'
  const classes = type === 'assistant'
    ? `${baseClasses} bg-tech-surface border-neon-cyan/40 ${className}`
    : `${baseClasses} bg-gradient-to-br from-neon-cyan/30 to-cyber-blue/30 border-neon-cyan/50 text-white ${className}`

  return (
    <div className={classes} role="img" aria-label={type === 'assistant' ? 'Supportron avatar' : 'User avatar'}>
      {type === 'assistant' && (
        <div className="absolute inset-0 bg-neon-cyan/10 rounded-lg animate-pulse"></div>
      )}
      {type === 'assistant' ? (
        <Image
          src={iconImage}
          alt="Supportron"
          width={36}
          height={36}
          className="w-full h-full object-cover rounded-lg relative z-10"
          aria-hidden="true"
        />
      ) : (
        <div className="relative z-10">
          <AvatarIcon aria-hidden={true} />
        </div>
      )}
    </div>
  )
}
