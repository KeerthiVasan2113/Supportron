export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  message: string
  is_it_related: boolean
}

