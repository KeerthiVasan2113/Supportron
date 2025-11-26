/**
 * Universal Timer Hook
 * 
 * React hook for using the universal timer utility in components.
 * Provides automatic updates and cleanup.
 * 
 * @param isActive - Whether the timer should be running
 * @param updateInterval - How often to update the elapsed time in milliseconds (default: 100ms)
 * @returns Object with elapsed time in seconds and formatted time string
 * 
 * @example
 * ```typescript
 * const { elapsedSeconds, formattedTime } = useTimer(isLoading)
 * 
 * return <div>Elapsed: {formattedTime}</div>
 * ```
 */

import { useState, useEffect, useRef } from 'react'
import { formatElapsedTime, calculateElapsedTime } from '@/utils/timer'

interface UseTimerReturn {
  /** Elapsed time in seconds */
  elapsedSeconds: number
  /** Formatted time string (e.g., "45s", "1m 30s") */
  formattedTime: string
  /** Start the timer */
  start: () => void
  /** Stop the timer */
  stop: () => void
  /** Reset the timer to zero */
  reset: () => void
}

export const useTimer = (
  isActive: boolean = false,
  updateInterval: number = 100
): UseTimerReturn => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startTimeRef = useRef<number | null>(null)

  // Start timer when isActive becomes true
  useEffect(() => {
    if (isActive && !startTimeRef.current) {
      startTimeRef.current = Date.now()
    } else if (!isActive && startTimeRef.current) {
      // Keep the elapsed time when stopped, but don't update it
      startTimeRef.current = null
    }
  }, [isActive])

  // Update elapsed time at regular intervals
  useEffect(() => {
    if (!isActive || !startTimeRef.current) {
      return
    }

    const interval = setInterval(() => {
      if (startTimeRef.current) {
        const elapsed = calculateElapsedTime(startTimeRef.current)
        setElapsedSeconds(elapsed)
      }
    }, updateInterval)

    return () => clearInterval(interval)
  }, [isActive, updateInterval])

  // Reset elapsed time when timer stops
  useEffect(() => {
    if (!isActive && startTimeRef.current === null) {
      setElapsedSeconds(0)
    }
  }, [isActive])

  const start = () => {
    if (!startTimeRef.current) {
      startTimeRef.current = Date.now()
    }
  }

  const stop = () => {
    if (startTimeRef.current) {
      startTimeRef.current = null
    }
  }

  const reset = () => {
    startTimeRef.current = null
    setElapsedSeconds(0)
  }

  return {
    elapsedSeconds,
    formattedTime: formatElapsedTime(elapsedSeconds),
    start,
    stop,
    reset,
  }
}

