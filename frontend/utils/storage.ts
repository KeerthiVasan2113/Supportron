/**
 * LocalStorage utility functions with error handling and type safety.
 */

const STORAGE_KEYS = {
  CHATS: 'supportron_chats',
  LAST_CHAT_ID: 'supportron_last_chat_id',
  START_NEW_CHAT: 'startNewChat',
} as const

export const StorageKeys = STORAGE_KEYS

/**
 * Safely get item from localStorage.
 */
export const getStorageItem = <T>(key: string, defaultValue: T): T => {
  if (typeof window === 'undefined') {
    return defaultValue
  }
  
  try {
    const item = localStorage.getItem(key)
    if (item === null) {
      return defaultValue
    }
    return JSON.parse(item) as T
  } catch (error) {
    console.error(`Error reading from localStorage (${key}):`, error)
    return defaultValue
  }
}

/**
 * Safely set item in localStorage.
 */
export const setStorageItem = <T>(key: string, value: T): boolean => {
  if (typeof window === 'undefined') {
    return false
  }
  
  try {
    localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch (error) {
    console.error(`Error writing to localStorage (${key}):`, error)
    if (error instanceof Error && error.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded. Consider clearing old data.')
    }
    return false
  }
}

/**
 * Safely remove item from localStorage.
 */
export const removeStorageItem = (key: string): boolean => {
  if (typeof window === 'undefined') {
    return false
  }
  
  try {
    localStorage.removeItem(key)
    return true
  } catch (error) {
    console.error(`Error removing from localStorage (${key}):`, error)
    return false
  }
}

/**
 * Safely get item from sessionStorage.
 */
export const getSessionItem = (key: string): string | null => {
  if (typeof window === 'undefined') {
    return null
  }
  
  try {
    return sessionStorage.getItem(key)
  } catch (error) {
    console.error(`Error reading from sessionStorage (${key}):`, error)
    return null
  }
}

/**
 * Safely set item in sessionStorage.
 */
export const setSessionItem = (key: string, value: string): boolean => {
  if (typeof window === 'undefined') {
    return false
  }
  
  try {
    sessionStorage.setItem(key, value)
    return true
  } catch (error) {
    console.error(`Error writing to sessionStorage (${key}):`, error)
    return false
  }
}

/**
 * Safely remove item from sessionStorage.
 */
export const removeSessionItem = (key: string): boolean => {
  if (typeof window === 'undefined') {
    return false
  }
  
  try {
    sessionStorage.removeItem(key)
    return true
  } catch (error) {
    console.error(`Error removing from sessionStorage (${key}):`, error)
    return false
  }
}

