import { motion } from 'framer-motion'
import { useDesktop } from '@/hooks/useDesktop'
import {
  MessageSquare,
  Terminal,
  FileText,
  Settings,
  Database,
  Box,
  Workflow,
  X,
  Minimize2
} from 'lucide-react'

// Map appId to icon
const APP_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  chat: MessageSquare,
  terminal: Terminal,
  notes: FileText,
  workflow: Workflow,
  database: Database,
  agents: Box,
  settings: Settings
}

export function Taskbar() {
  const {
    currentWindows,
    minimizedWindows,
    focusedWindow,
    focusWindow,
    restoreWindow,
    closeWindow
  } = useDesktop()

  // Get icon for app
  const getIcon = (appId: string) => {
    const Icon = APP_ICONS[appId] || Box
    return Icon
  }

  // Handle window click
  const handleWindowClick = (windowId: string, isMinimized: boolean) => {
    if (isMinimized) {
      restoreWindow(windowId)
    } else {
      focusWindow(windowId)
    }
  }

  // No windows open
  if (currentWindows.length === 0) {
    return (
      <div className="fixed bottom-24 left-0 right-0 flex justify-center z-30">
        <div className="bg-slate-900/50 backdrop-blur border border-slate-700/50 rounded-lg px-4 py-2 text-gray-500 text-sm">
          No windows open
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-24 left-0 right-0 flex justify-center z-30">
      <div className="max-w-4xl w-full px-4">
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-lg shadow-xl overflow-hidden">
          <div className="flex items-center gap-1 p-2 overflow-x-auto">
            {currentWindows.map((window) => {
              const Icon = getIcon(window.appId)
              const isFocused = focusedWindow === window.id
              const isMinimized = window.isMinimized

              return (
                <motion.button
                  key={window.id}
                  onClick={() => handleWindowClick(window.id, isMinimized)}
                  className={`relative flex items-center gap-2 px-3 py-2 rounded-lg transition-all min-w-[150px] group ${
                    isFocused && !isMinimized
                      ? 'bg-primary text-white'
                      : isMinimized
                      ? 'bg-slate-800/50 text-gray-500'
                      : 'bg-slate-800 text-gray-300 hover:bg-slate-700'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {/* Icon */}
                  <Icon className="w-4 h-4 flex-shrink-0" />

                  {/* Title */}
                  <span className="text-sm truncate flex-1">{window.title}</span>

                  {/* Minimized indicator */}
                  {isMinimized && (
                    <Minimize2 className="w-3 h-3 flex-shrink-0 opacity-50" />
                  )}

                  {/* Close button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      closeWindow(window.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 hover:bg-red-500/20 rounded"
                  >
                    <X className="w-3 h-3" />
                  </button>

                  {/* Focus indicator */}
                  {isFocused && !isMinimized && (
                    <motion.div
                      layoutId="taskbar-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-white rounded-full"
                    />
                  )}
                </motion.button>
              )
            })}
          </div>

          {/* Minimized windows count */}
          {minimizedWindows.length > 0 && (
            <div className="px-4 py-1 border-t border-slate-700/50 bg-slate-900/50">
              <div className="text-xs text-gray-500">
                {minimizedWindows.length} window{minimizedWindows.length !== 1 ? 's' : ''} minimized
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
