import { useEffect, useCallback } from 'react'
import { useChat } from '@/hooks/useChat'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { MessageSquare, Plus, Trash2 } from 'lucide-react'

interface ChatInterfaceProps {
  className?: string
}

export function ChatInterface({ className = '' }: ChatInterfaceProps) {
  const {
    currentSession,
    sessions,
    isLoading,
    isStreaming,
    error,
    sendMessage,
    cancelRequest,
    createSession,
    switchSession,
    deleteSession,
    loadConversations,
    clearError
  } = useChat()

  // Load conversations on mount
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  // Create initial session if none exists
  useEffect(() => {
    if (sessions.length === 0) {
      createSession('New Conversation')
    }
  }, [sessions.length, createSession])

  // Handle send message
  const handleSend = useCallback(
    async (message: string) => {
      const success = await sendMessage(message, { stream: true })
      if (!success && error) {
        console.error('Failed to send message:', error)
      }
    },
    [sendMessage, error]
  )

  // Handle cancel
  const handleCancel = useCallback(() => {
    cancelRequest()
  }, [cancelRequest])

  // Handle create new session
  const handleNewSession = useCallback(() => {
    createSession(`Conversation ${sessions.length + 1}`)
  }, [createSession, sessions.length])

  // Handle delete session
  const handleDeleteSession = useCallback(
    (sessionId: string) => {
      if (confirm('Are you sure you want to delete this conversation?')) {
        deleteSession(sessionId)
      }
    },
    [deleteSession]
  )

  return (
    <div className={`flex flex-col h-full bg-slate-900 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-900/90 backdrop-blur">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-200">
            {currentSession?.title || 'Chat'}
          </h2>
        </div>

        <button
          onClick={handleNewSession}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary hover:bg-primary/80 text-white text-sm rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New
        </button>
      </div>

      {/* Sidebar - Session List (collapsible on small screens) */}
      {sessions.length > 1 && (
        <div className="border-b border-slate-700 bg-slate-900/50 px-4 py-2 overflow-x-auto">
          <div className="flex gap-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => switchSession(session.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors whitespace-nowrap ${
                  currentSession?.id === session.id
                    ? 'bg-primary text-white'
                    : 'bg-slate-800 text-gray-400 hover:bg-slate-700'
                }`}
              >
                <span>{session.title}</span>
                {sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteSession(session.id)
                    }}
                    className="hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-red-500/20 border-b border-red-500/50 text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-300 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        {currentSession ? (
          <MessageList
            messages={currentSession.messages}
            isLoading={isLoading && !isStreaming}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg mb-2">No conversation selected</p>
              <p className="text-sm">Create a new conversation to get started</p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      {currentSession && (
        <ChatInput
          onSend={handleSend}
          onCancel={handleCancel}
          isLoading={isLoading}
          isStreaming={isStreaming}
          disabled={!currentSession}
        />
      )}
    </div>
  )
}
