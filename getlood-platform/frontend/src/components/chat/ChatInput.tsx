import { useState, useRef, useCallback, KeyboardEvent } from 'react'
import { Send, StopCircle } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  onCancel?: () => void
  isLoading?: boolean
  isStreaming?: boolean
  placeholder?: string
  disabled?: boolean
}

export function ChatInput({
  onSend,
  onCancel,
  isLoading = false,
  isStreaming = false,
  placeholder = 'Type your message...',
  disabled = false
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.style.height = 'auto'
    const newHeight = Math.min(textarea.scrollHeight, 200) // Max 200px
    textarea.style.height = `${newHeight}px`
  }, [])

  // Handle input change
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value)
      adjustHeight()
    },
    [adjustHeight]
  )

  // Handle send
  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isLoading || disabled) return

    onSend(trimmed)
    setInput('')

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [input, isLoading, disabled, onSend])

  // Handle key down
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter to send (Shift+Enter for new line)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  // Handle cancel
  const handleCancel = useCallback(() => {
    onCancel?.()
  }, [onCancel])

  const showCancelButton = isLoading || isStreaming

  return (
    <div className="flex items-end gap-2 p-4 border-t border-slate-700 bg-slate-900/50 backdrop-blur">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled || isLoading}
        rows={1}
        className="flex-1 resize-none bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        style={{ minHeight: '40px', maxHeight: '200px' }}
      />

      {showCancelButton ? (
        <button
          onClick={handleCancel}
          className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
          title="Cancel"
        >
          <StopCircle className="w-5 h-5" />
          <span>Stop</span>
        </button>
      ) : (
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading || disabled}
          className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/80 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Send (Enter)"
        >
          <Send className="w-5 h-5" />
          <span>Send</span>
        </button>
      )}
    </div>
  )
}
