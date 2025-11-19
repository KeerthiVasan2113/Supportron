export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: SourceDocument[]
  responseTime?: number
  isLoading?: boolean
  loadingStartTime?: number
}

export interface SourceDocument {
  source_file: string
  preview: string
  distance?: number
}

export interface ChatResponse {
  answer: string
  question: string
  sources?: SourceDocument[]
}

