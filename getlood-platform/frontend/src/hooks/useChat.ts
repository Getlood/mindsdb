import { useState, useCallback, useRef } from 'react'
import axios from 'axios'
import { useAuth } from './useAuth'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    model?: string
    agent?: string
    universe?: string
    execution_time_ms?: number
  }
}

export interface ChatSession {
  id: string
  title: string
  created_at: Date
  updated_at: Date
  messages: Message[]
}

interface ChatState {
  sessions: ChatSession[]
  currentSessionId: string | null
  isLoading: boolean
  isStreaming: boolean
  error: string | null
}

interface SendMessageOptions {
  sessionId?: string
  stream?: boolean
  model?: string
  temperature?: number
  max_tokens?: number
}

export function useChat() {
  const { token } = useAuth()
  const [state, setState] = useState<ChatState>({
    sessions: [],
    currentSessionId: null,
    isLoading: false,
    isStreaming: false,
    error: null
  })

  const abortControllerRef = useRef<AbortController | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  // Create a new chat session
  const createSession = useCallback(async (title?: string): Promise<string> => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`
    const newSession: ChatSession = {
      id: sessionId,
      title: title || 'New Conversation',
      created_at: new Date(),
      updated_at: new Date(),
      messages: []
    }

    setState(prev => ({
      ...prev,
      sessions: [...prev.sessions, newSession],
      currentSessionId: sessionId
    }))

    return sessionId
  }, [])

  // Get current session
  const getCurrentSession = useCallback((): ChatSession | null => {
    if (!state.currentSessionId) return null
    return state.sessions.find(s => s.id === state.currentSessionId) || null
  }, [state.currentSessionId, state.sessions])

  // Add message to session
  const addMessage = useCallback((sessionId: string, message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(7)}`,
      timestamp: new Date()
    }

    setState(prev => ({
      ...prev,
      sessions: prev.sessions.map(session =>
        session.id === sessionId
          ? {
              ...session,
              messages: [...session.messages, newMessage],
              updated_at: new Date()
            }
          : session
      )
    }))

    return newMessage
  }, [])

  // Update partial message (for streaming)
  const updateMessage = useCallback((sessionId: string, messageId: string, content: string, metadata?: any) => {
    setState(prev => ({
      ...prev,
      sessions: prev.sessions.map(session =>
        session.id === sessionId
          ? {
              ...session,
              messages: session.messages.map(msg =>
                msg.id === messageId
                  ? { ...msg, content, metadata: { ...msg.metadata, ...metadata } }
                  : msg
              ),
              updated_at: new Date()
            }
          : session
      )
    }))
  }, [])

  // Send message with non-streaming
  const sendMessageSync = async (
    message: string,
    sessionId: string,
    options: SendMessageOptions
  ): Promise<Message> => {
    try {
      const response = await axios.post(
        '/api/v1/chat/completions',
        {
          message,
          session_id: sessionId,
          model: options.model,
          temperature: options.temperature,
          max_tokens: options.max_tokens,
          stream: false
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          signal: abortControllerRef.current?.signal
        }
      )

      const assistantMessage = addMessage(sessionId, {
        role: 'assistant',
        content: response.data.content,
        metadata: response.data.metadata
      })

      return assistantMessage
    } catch (error: any) {
      if (axios.isCancel(error)) {
        throw new Error('Request cancelled')
      }
      throw new Error(error.response?.data?.detail || 'Failed to send message')
    }
  }

  // Send message with streaming (SSE)
  const sendMessageStream = async (
    message: string,
    sessionId: string,
    options: SendMessageOptions
  ): Promise<Message> => {
    return new Promise((resolve, reject) => {
      // Create placeholder message for streaming content
      const assistantMessage = addMessage(sessionId, {
        role: 'assistant',
        content: '',
        metadata: {}
      })

      // Build URL with query parameters
      const params = new URLSearchParams({
        session_id: sessionId,
        message: message,
        stream: 'true'
      })

      if (options.model) params.append('model', options.model)
      if (options.temperature !== undefined) params.append('temperature', options.temperature.toString())
      if (options.max_tokens !== undefined) params.append('max_tokens', options.max_tokens.toString())

      const url = `/api/v1/chat/completions?${params.toString()}`

      // Create EventSource for SSE
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      let accumulatedContent = ''
      let metadata: any = {}

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          switch (data.type) {
            case 'start':
              setState(prev => ({ ...prev, isStreaming: true }))
              break

            case 'content':
              accumulatedContent += data.content
              updateMessage(sessionId, assistantMessage.id, accumulatedContent)
              break

            case 'metadata':
              metadata = { ...metadata, ...data.metadata }
              break

            case 'done':
              updateMessage(sessionId, assistantMessage.id, accumulatedContent, {
                ...metadata,
                execution_time_ms: data.execution_time_ms
              })
              setState(prev => ({ ...prev, isStreaming: false }))
              eventSource.close()
              eventSourceRef.current = null
              resolve({ ...assistantMessage, content: accumulatedContent, metadata })
              break

            case 'error':
              throw new Error(data.error)
          }
        } catch (error: any) {
          console.error('SSE parsing error:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        setState(prev => ({ ...prev, isStreaming: false, error: 'Connection error' }))
        eventSource.close()
        eventSourceRef.current = null
        reject(new Error('SSE connection failed'))
      }
    })
  }

  // Send message (main function)
  const sendMessage = useCallback(
    async (message: string, options: SendMessageOptions = {}): Promise<boolean> => {
      setState(prev => ({ ...prev, isLoading: true, error: null }))

      try {
        // Get or create session
        let sessionId = options.sessionId || state.currentSessionId
        if (!sessionId) {
          sessionId = await createSession()
        }

        // Add user message
        addMessage(sessionId, {
          role: 'user',
          content: message
        })

        // Create abort controller
        abortControllerRef.current = new AbortController()

        // Send message based on stream option
        if (options.stream !== false) {
          await sendMessageStream(message, sessionId, options)
        } else {
          await sendMessageSync(message, sessionId, options)
        }

        setState(prev => ({ ...prev, isLoading: false }))
        return true
      } catch (error: any) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Failed to send message'
        }))
        return false
      } finally {
        abortControllerRef.current = null
      }
    },
    [state.currentSessionId, createSession, addMessage]
  )

  // Cancel ongoing request
  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }

    setState(prev => ({ ...prev, isLoading: false, isStreaming: false }))
  }, [])

  // Load conversations from server
  const loadConversations = useCallback(async () => {
    if (!token) return

    try {
      const response = await axios.get('/api/v1/chat/conversations', {
        headers: { Authorization: `Bearer ${token}` }
      })

      const sessions: ChatSession[] = response.data.map((conv: any) => ({
        id: conv.id,
        title: conv.title,
        created_at: new Date(conv.created_at),
        updated_at: new Date(conv.updated_at),
        messages: []
      }))

      setState(prev => ({ ...prev, sessions }))
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }, [token])

  // Load messages for a session
  const loadMessages = useCallback(
    async (sessionId: string) => {
      if (!token) return

      try {
        const response = await axios.get(`/api/v1/chat/conversations/${sessionId}/messages`, {
          headers: { Authorization: `Bearer ${token}` }
        })

        const messages: Message[] = response.data.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp),
          metadata: msg.metadata
        }))

        setState(prev => ({
          ...prev,
          sessions: prev.sessions.map(session =>
            session.id === sessionId ? { ...session, messages } : session
          )
        }))
      } catch (error) {
        console.error('Failed to load messages:', error)
      }
    },
    [token]
  )

  // Switch to a different session
  const switchSession = useCallback((sessionId: string) => {
    setState(prev => ({ ...prev, currentSessionId: sessionId }))
  }, [])

  // Delete a session
  const deleteSession = useCallback((sessionId: string) => {
    setState(prev => ({
      ...prev,
      sessions: prev.sessions.filter(s => s.id !== sessionId),
      currentSessionId: prev.currentSessionId === sessionId ? null : prev.currentSessionId
    }))
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  return {
    sessions: state.sessions,
    currentSession: getCurrentSession(),
    isLoading: state.isLoading,
    isStreaming: state.isStreaming,
    error: state.error,
    sendMessage,
    cancelRequest,
    createSession,
    switchSession,
    deleteSession,
    loadConversations,
    loadMessages,
    clearError
  }
}
