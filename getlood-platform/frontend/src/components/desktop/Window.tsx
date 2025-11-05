import { useRef, useCallback, useEffect } from 'react'
import { motion } from 'framer-motion'
import { WindowData } from '@/state/atoms/desktopAtoms'
import { useDesktop } from '@/hooks/useDesktop'
import { Minimize2, Maximize2, X, Minus } from 'lucide-react'

interface WindowProps {
  window: WindowData
}

type ResizeHandle = 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw'

export function Window({ window }: WindowProps) {
  const {
    focusWindow,
    closeWindow,
    minimizeWindow,
    maximizeWindow,
    moveWindow,
    resizeWindow
  } = useDesktop()

  const windowRef = useRef<HTMLDivElement>(null)
  const dragStateRef = useRef({
    isDragging: false,
    startX: 0,
    startY: 0,
    windowX: 0,
    windowY: 0
  })

  const resizeStateRef = useRef({
    isResizing: false,
    handle: null as ResizeHandle | null,
    startX: 0,
    startY: 0,
    startWidth: 0,
    startHeight: 0,
    startWindowX: 0,
    startWindowY: 0
  })

  const rafRef = useRef<number | null>(null)

  // Handle window focus
  const handleFocus = useCallback(() => {
    if (!window.isFocused) {
      focusWindow(window.id)
    }
  }, [window.id, window.isFocused, focusWindow])

  // Handle drag start
  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      // Only drag from title bar
      const target = e.target as HTMLElement
      if (!target.closest('.window-title-bar')) return

      e.preventDefault()
      handleFocus()

      dragStateRef.current = {
        isDragging: true,
        startX: e.clientX,
        startY: e.clientY,
        windowX: window.x,
        windowY: window.y
      }

      document.body.style.cursor = 'move'
      document.body.style.userSelect = 'none'
    },
    [window.x, window.y, handleFocus]
  )

  // Handle resize start
  const handleResizeStart = useCallback(
    (e: React.MouseEvent, handle: ResizeHandle) => {
      e.preventDefault()
      e.stopPropagation()
      handleFocus()

      resizeStateRef.current = {
        isResizing: true,
        handle,
        startX: e.clientX,
        startY: e.clientY,
        startWidth: window.width,
        startHeight: window.height,
        startWindowX: window.x,
        startWindowY: window.y
      }

      document.body.style.userSelect = 'none'
    },
    [window.width, window.height, window.x, window.y, handleFocus]
  )

  // RAF-optimized mouse move handler
  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (rafRef.current !== null) return

      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null

        // Handle dragging
        if (dragStateRef.current.isDragging) {
          const deltaX = e.clientX - dragStateRef.current.startX
          const deltaY = e.clientY - dragStateRef.current.startY

          const newX = Math.max(0, dragStateRef.current.windowX + deltaX)
          const newY = Math.max(0, dragStateRef.current.windowY + deltaY)

          moveWindow(window.id, newX, newY)
        }

        // Handle resizing
        if (resizeStateRef.current.isResizing) {
          const { handle, startX, startY, startWidth, startHeight, startWindowX, startWindowY } =
            resizeStateRef.current

          const deltaX = e.clientX - startX
          const deltaY = e.clientY - startY

          let newWidth = startWidth
          let newHeight = startHeight
          let newX = startWindowX
          let newY = startWindowY

          // Calculate new dimensions based on resize handle
          if (handle?.includes('e')) {
            newWidth = Math.max(400, startWidth + deltaX)
          }
          if (handle?.includes('w')) {
            newWidth = Math.max(400, startWidth - deltaX)
            newX = startWindowX + (startWidth - newWidth)
          }
          if (handle?.includes('s')) {
            newHeight = Math.max(300, startHeight + deltaY)
          }
          if (handle?.includes('n')) {
            newHeight = Math.max(300, startHeight - deltaY)
            newY = startWindowY + (startHeight - newHeight)
          }

          // Update position if needed (for n, w, nw, ne, sw handles)
          if (newX !== startWindowX || newY !== startWindowY) {
            moveWindow(window.id, newX, newY)
          }

          resizeWindow(window.id, newWidth, newHeight)
        }
      })
    },
    [window.id, moveWindow, resizeWindow]
  )

  // Handle mouse up
  const handleMouseUp = useCallback(() => {
    if (dragStateRef.current.isDragging) {
      dragStateRef.current.isDragging = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    if (resizeStateRef.current.isResizing) {
      resizeStateRef.current.isResizing = false
      document.body.style.userSelect = ''
    }

    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }, [])

  // Add/remove event listeners
  useEffect(() => {
    const handleMove = (e: MouseEvent) => handleMouseMove(e)
    const handleUp = () => handleMouseUp()

    if (dragStateRef.current.isDragging || resizeStateRef.current.isResizing) {
      document.addEventListener('mousemove', handleMove)
      document.addEventListener('mouseup', handleUp)

      return () => {
        document.removeEventListener('mousemove', handleMove)
        document.removeEventListener('mouseup', handleUp)
      }
    }
  }, [handleMouseMove, handleMouseUp])

  // Get cursor style for resize handles
  const getResizeCursor = (handle: ResizeHandle): string => {
    const cursors: Record<ResizeHandle, string> = {
      n: 'ns-resize',
      s: 'ns-resize',
      e: 'ew-resize',
      w: 'ew-resize',
      ne: 'nesw-resize',
      nw: 'nwse-resize',
      se: 'nwse-resize',
      sw: 'nesw-resize'
    }
    return cursors[handle]
  }

  // Render window content based on appId
  const renderContent = () => {
    // Placeholder - will be replaced with actual app components
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <p className="text-lg font-medium">{window.appId}</p>
          <p className="text-sm mt-2">Content goes here</p>
        </div>
      </div>
    )
  }

  if (!window.isVisible) return null

  return (
    <motion.div
      ref={windowRef}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={`absolute bg-slate-800 rounded-lg shadow-2xl overflow-hidden ${
        window.isFocused ? 'ring-2 ring-primary/50' : ''
      }`}
      style={{
        left: window.isMaximized ? 0 : window.x,
        top: window.isMaximized ? 0 : window.y,
        width: window.isMaximized ? '100vw' : window.width,
        height: window.isMaximized ? 'calc(100vh - 128px)' : window.height,
        zIndex: window.zIndex
      }}
      onMouseDown={handleFocus}
    >
      {/* Title Bar */}
      <div
        className="window-title-bar flex items-center justify-between px-4 py-2 bg-slate-900/90 backdrop-blur border-b border-slate-700 cursor-move"
        onMouseDown={handleDragStart}
      >
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gradient-to-br from-primary to-secondary" />
          <span className="text-sm font-medium text-gray-200">{window.title}</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              minimizeWindow(window.id)
            }}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors"
            title="Minimize"
          >
            <Minus className="w-4 h-4 text-gray-400" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation()
              maximizeWindow(window.id)
            }}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors"
            title="Maximize"
          >
            {window.isMaximized ? (
              <Minimize2 className="w-4 h-4 text-gray-400" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-400" />
            )}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation()
              closeWindow(window.id)
            }}
            className="p-1.5 hover:bg-red-500/20 hover:text-red-400 rounded transition-colors"
            title="Close"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Window Content */}
      <div className="h-[calc(100%-40px)] overflow-auto bg-slate-800">
        {renderContent()}
      </div>

      {/* Resize Handles - only visible when not maximized */}
      {!window.isMaximized && (
        <>
          {/* Corners */}
          <div
            className="absolute top-0 left-0 w-3 h-3 cursor-nwse-resize"
            style={{ cursor: getResizeCursor('nw') }}
            onMouseDown={(e) => handleResizeStart(e, 'nw')}
          />
          <div
            className="absolute top-0 right-0 w-3 h-3 cursor-nesw-resize"
            style={{ cursor: getResizeCursor('ne') }}
            onMouseDown={(e) => handleResizeStart(e, 'ne')}
          />
          <div
            className="absolute bottom-0 left-0 w-3 h-3 cursor-nesw-resize"
            style={{ cursor: getResizeCursor('sw') }}
            onMouseDown={(e) => handleResizeStart(e, 'sw')}
          />
          <div
            className="absolute bottom-0 right-0 w-3 h-3 cursor-nwse-resize"
            style={{ cursor: getResizeCursor('se') }}
            onMouseDown={(e) => handleResizeStart(e, 'se')}
          />

          {/* Edges */}
          <div
            className="absolute top-0 left-3 right-3 h-1 cursor-ns-resize"
            style={{ cursor: getResizeCursor('n') }}
            onMouseDown={(e) => handleResizeStart(e, 'n')}
          />
          <div
            className="absolute bottom-0 left-3 right-3 h-1 cursor-ns-resize"
            style={{ cursor: getResizeCursor('s') }}
            onMouseDown={(e) => handleResizeStart(e, 's')}
          />
          <div
            className="absolute top-3 bottom-3 left-0 w-1 cursor-ew-resize"
            style={{ cursor: getResizeCursor('w') }}
            onMouseDown={(e) => handleResizeStart(e, 'w')}
          />
          <div
            className="absolute top-3 bottom-3 right-0 w-1 cursor-ew-resize"
            style={{ cursor: getResizeCursor('e') }}
            onMouseDown={(e) => handleResizeStart(e, 'e')}
          />
        </>
      )}
    </motion.div>
  )
}
