import React from 'react'
import Image from 'next/image'
import { AvatarIcon } from './icons/AvatarIcon'
import iconImage from '../Assets/icon.png'

interface AvatarProps {
  type: 'assistant' | 'user'
  className?: string
}

export const Avatar: React.FC<AvatarProps> = ({ type, className = '' }) => {
  const baseClasses = 'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 border overflow-hidden'
  const classes = type === 'assistant'
    ? `${baseClasses} bg-telegram-blue/20 border-telegram-blue/30 ${className}`
    : `${baseClasses} bg-telegram-blue/30 border-telegram-blue/40 text-white ${className}`

  return (
    <div className={classes} role="img" aria-label={type === 'assistant' ? 'Supportron avatar' : 'User avatar'}>
      {type === 'assistant' ? (
        <Image
          src={iconImage}
          alt="Supportron"
          width={36}
          height={36}
          className="w-full h-full object-cover rounded-lg"
          aria-hidden="true"
        />
      ) : (
        <AvatarIcon aria-hidden={true} />
      )}
    </div>
  )
}
