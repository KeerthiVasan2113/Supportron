/**
 * Universal Timer Utility
 * 
 * Provides centralized timer functionality for the entire frontend application.
 * Similar to the backend logger pattern, this utility can be imported and used
 * anywhere in the application for consistent time tracking and formatting.
 * 
 * Features:
 * - Formats time in seconds, then converts to minutes when appropriate
 * - Provides both hook-based and utility-based APIs
 * - Consistent formatting across the application
 */

/**
 * Format elapsed time in a human-readable format.
 * 
 * @param seconds - Elapsed time in seconds
 * @param showDecimals - Whether to show decimal places for seconds (default: true)
 * @returns Formatted time string (e.g., "45s", "1m 30s", "2m 15.5s")
 * 
 * @example
 * ```typescript
 * formatElapsedTime(45) // "45s"
 * formatElapsedTime(90) // "1m 30s"
 * formatElapsedTime(135.5) // "2m 15.5s"
 * formatElapsedTime(60, false) // "1m 0s"
 * ```
 */
export const formatElapsedTime = (seconds: number, showDecimals: boolean = true): string => {
  if (seconds < 0) return '0s'
  
  const totalSeconds = Math.floor(seconds)
  const minutes = Math.floor(totalSeconds / 60)
  const remainingSeconds = totalSeconds % 60
  const decimalPart = showDecimals ? (seconds % 1).toFixed(1).substring(1) : ''
  
  if (minutes === 0) {
    // Show only seconds if less than 1 minute
    return `${seconds.toFixed(showDecimals ? 1 : 0)}s`
  } else {
    // Show minutes and seconds
    const secondsDisplay = remainingSeconds > 0 
      ? `${remainingSeconds}${decimalPart}s`
      : showDecimals && seconds % 1 !== 0
        ? `${decimalPart}s`
        : ''
    
    return secondsDisplay 
      ? `${minutes}m ${secondsDisplay}`
      : `${minutes}m`
  }
}

/**
 * Calculate elapsed time from a start timestamp.
 * 
 * @param startTime - Start timestamp in milliseconds (from Date.now())
 * @returns Elapsed time in seconds
 * 
 * @example
 * ```typescript
 * const start = Date.now()
 * // ... some time passes ...
 * const elapsed = calculateElapsedTime(start) // returns seconds
 * ```
 */
export const calculateElapsedTime = (startTime: number): number => {
  return (Date.now() - startTime) / 1000
}

/**
 * Timer class for programmatic timer management.
 * Similar to the logger pattern - can be instantiated and used anywhere.
 */
export class Timer {
  private startTime: number | null = null
  private isRunning: boolean = false

  /**
   * Start the timer.
   */
  start(): void {
    this.startTime = Date.now()
    this.isRunning = true
  }

  /**
   * Stop the timer.
   */
  stop(): void {
    this.isRunning = false
  }

  /**
   * Reset the timer to zero.
   */
  reset(): void {
    this.startTime = null
    this.isRunning = false
  }

  /**
   * Get the current elapsed time in seconds.
   * 
   * @returns Elapsed time in seconds, or 0 if timer hasn't started
   */
  getElapsedSeconds(): number {
    if (!this.startTime) return 0
    return calculateElapsedTime(this.startTime)
  }

  /**
   * Get the formatted elapsed time string.
   * 
   * @param showDecimals - Whether to show decimal places (default: true)
   * @returns Formatted time string
   */
  getFormattedTime(showDecimals: boolean = true): string {
    return formatElapsedTime(this.getElapsedSeconds(), showDecimals)
  }

  /**
   * Check if the timer is currently running.
   */
  get running(): boolean {
    return this.isRunning && this.startTime !== null
  }
}

/**
 * Create a new timer instance.
 * 
 * @returns A new Timer instance
 * 
 * @example
 * ```typescript
 * const timer = createTimer()
 * timer.start()
 * // ... do work ...
 * console.log(timer.getFormattedTime()) // "1m 30.5s"
 * timer.stop()
 * ```
 */
export const createTimer = (): Timer => {
  return new Timer()
}

