import React from 'react'
import Image from 'next/image'
import { SpinnerIcon } from './icons/SpinnerIcon'
import iconImage from '../Assets/icon.png'

export const LoadingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start w-full mb-1 sm:mb-1.5 md:mb-2" role="status" aria-live="polite" aria-label="Supportron is thinking">
      <div className="max-w-[92%] xs:max-w-[88%] sm:max-w-[82%] md:max-w-[78%] lg:max-w-[72%] xl:max-w-[68%] 2xl:max-w-[65%] 3xl:max-w-[60%] bg-tech-surface rounded-2xl p-2.5 xs:p-3 sm:p-3.5 md:p-4 lg:p-4 shadow-md tech-border relative" style={{ borderRadius: '12px 12px 12px 4px' }}>
        <div className="flex items-center gap-1.5 xs:gap-2 sm:gap-2.5 md:gap-3">
          <div className="w-8 h-8 xs:w-9 xs:h-9 rounded-lg bg-tech-surface border border-neon-cyan/40 flex-shrink-0 overflow-hidden relative">
            <Image
              src={iconImage}
              alt="Supportron"
              width={36}
              height={36}
              className="w-full h-full object-cover rounded-lg opacity-70"
              aria-hidden="true"
            />
            <div className="absolute inset-0 flex items-center justify-center bg-tech-surface/80 backdrop-blur-sm">
              <SpinnerIcon className="w-3 h-3 xs:w-4 xs:h-4 text-neon-cyan animate-spin neon-glow" aria-hidden={true} />
            </div>
          </div>
          <span className="text-xs xs:text-sm sm:text-sm md:text-base text-text-secondary">
            <span className="sr-only">Supportron is thinking</span>
            <span aria-hidden="true" className="inline-flex items-center gap-1">
              <span className="text-neon-cyan">[</span>
              <span className="animate-pulse">PROCESSING</span>
              <span className="text-neon-cyan">]</span>
            </span>
          </span>
        </div>
      </div>
    </div>
  )
}

