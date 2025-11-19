/**
 * API configuration and client utilities.
 * Centralized API endpoint management.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_VERSION = 'v1' // Use v1 API

/**
 * API endpoints configuration.
 */
export const API_ENDPOINTS = {
  // Health check endpoints
  health: `${API_BASE_URL}/health`,
  healthV1: `${API_BASE_URL}/api/${API_VERSION}/health`,
  
  // Chat endpoints
  chat: `${API_BASE_URL}/api/chat`, // Legacy endpoint (backward compatible)
  chatV1: `${API_BASE_URL}/api/${API_VERSION}/chat`, // New v1 endpoint
} as const

/**
 * Get the active chat endpoint.
 * Can be configured to use v1 or legacy endpoint.
 */
export const getChatEndpoint = (): string => {
  // Use v1 endpoint by default, fallback to legacy for compatibility
  return API_ENDPOINTS.chatV1
}

/**
 * Message in conversation history.
 */
export interface MessageHistory {
  role: 'user' | 'assistant'
  content: string
}

/**
 * Chat request payload.
 */
export interface ChatRequest {
  question: string
  show_sources?: boolean
  conversation_history?: MessageHistory[]
}

/**
 * Source document from RAG.
 */
export interface SourceDocument {
  source_file: string
  preview: string
  distance?: number
}

/**
 * Chat response from API.
 */
export interface ChatResponse {
  answer: string
  question: string
  sources?: SourceDocument[]
}

/**
 * Send a chat message to the API with conversation context.
 * 
 * @param question - User's question
 * @param showSources - Whether to include source documents
 * @param conversationHistory - Previous messages in the conversation for context
 * @returns Promise resolving to chat response
 * @throws Error if request fails
 */
export const sendChatMessage = async (
  question: string,
  showSources: boolean = true,
  conversationHistory?: MessageHistory[]
): Promise<ChatResponse> => {
  const endpoint = getChatEndpoint()
  
  // Format conversation history (exclude current question)
  const history: MessageHistory[] | undefined = conversationHistory 
    ? conversationHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    : undefined
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: question.trim(),
      show_sources: showSources,
      conversation_history: history,
    } as ChatRequest),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ 
      detail: 'Failed to get response' 
    }))
    throw new Error(errorData.detail || `Server error: ${response.status}`)
  }

  return response.json() as Promise<ChatResponse>
}

/**
 * Check API health status.
 * 
 * @returns Promise resolving to health status
 */
export const checkHealth = async (): Promise<any> => {
  const response = await fetch(API_ENDPOINTS.healthV1)
  
  if (!response.ok) {
    throw new Error('Health check failed')
  }
  
  return response.json()
}

