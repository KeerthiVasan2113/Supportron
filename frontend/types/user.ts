export interface User {
  id: string
  name: string
  email: string
  password: string
  role: 'admin' | 'user'
  createdAt: string
}

export interface ChatSession {
  id: string
  userId: string
  title: string
  createdAt: string
  updatedAt: string
  messages: Message[]
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

