import { useEffect, useCallback, useRef } from 'react'
import { useAtom } from 'jotai'
import { windowsAtom, currentDesktopAtom, focusedWindowAtom, WindowData } from '@/state/atoms/desktopAtoms'
import { useAuth } from './useAuth'

interface CreateWindowOptions {
  appId: string
  title: string
  x?: number
  y?: number
  width?: number
  height?: number
  desktopId?: number
}

export function useDesktop() {
  const { token, user } = useAuth()
  const [windows, setWindows] = useAtom(windowsAtom)
  const [currentDesktop, setCurrentDesktop] = useAtom(currentDesktopAtom)
  const [focusedWindow, setFocusedWindow] = useAtom(focusedWindowAtom)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Get max z-index
  const getMaxZIndex = useCallback((): number => {
    if (windows.length === 0) return 1
    return Math.max(...windows.map(w => w.zIndex))
  }, [windows])

  // Generate random position with offset
  const getRandomPosition = useCallback((): { x: number; y: number } => {
    const offset = windows.filter(w => w.desktopId === currentDesktop).length * 30
    return {
      x: 100 + offset,
      y: 100 + offset
    }
  }, [windows, currentDesktop])

  // Send message to WebSocket
  const sendWsMessage = useCallback((type: string, data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }))
    }
  }, [])

  // Create window
  const createWindow = useCallback(
    (options: CreateWindowOptions): string => {
      const position = getRandomPosition()
      const windowId = `window_${Date.now()}_${Math.random().toString(36).substring(7)}`

      const newWindow: WindowData = {
        id: windowId,
        appId: options.appId,
        title: options.title,
        x: options.x ?? position.x,
        y: options.y ?? position.y,
        width: options.width ?? 800,
        height: options.height ?? 600,
        zIndex: getMaxZIndex() + 1,
        isMinimized: false,
        isMaximized: false,
        isFocused: true,
        isVisible: true,
        desktopId: options.desktopId ?? currentDesktop
      }

      setWindows(prev => [...prev, newWindow])
      setFocusedWindow(windowId)

      // Notify other clients
      sendWsMessage('WINDOW_OPENED', {
        window_id: windowId,
        app_id: options.appId,
        desktop_id: newWindow.desktopId,
        x: newWindow.x,
        y: newWindow.y,
        width: newWindow.width,
        height: newWindow.height
      })

      return windowId
    },
    [currentDesktop, getMaxZIndex, getRandomPosition, setWindows, setFocusedWindow, sendWsMessage]
  )

  // Close window
  const closeWindow = useCallback(
    (windowId: string) => {
      setWindows(prev => prev.filter(w => w.id !== windowId))

      if (focusedWindow === windowId) {
        setFocusedWindow(null)
      }

      // Notify other clients
      sendWsMessage('WINDOW_CLOSED', { window_id: windowId })
    },
    [focusedWindow, setWindows, setFocusedWindow, sendWsMessage]
  )

  // Focus window
  const focusWindow = useCallback(
    (windowId: string) => {
      const maxZ = getMaxZIndex()

      setWindows(prev =>
        prev.map(w =>
          w.id === windowId
            ? { ...w, zIndex: maxZ + 1, isFocused: true, isMinimized: false }
            : { ...w, isFocused: false }
        )
      )
      setFocusedWindow(windowId)

      // Notify other clients
      sendWsMessage('WINDOW_FOCUSED', { window_id: windowId })
    },
    [getMaxZIndex, setWindows, setFocusedWindow, sendWsMessage]
  )

  // Move window
  const moveWindow = useCallback(
    (windowId: string, x: number, y: number) => {
      setWindows(prev =>
        prev.map(w => (w.id === windowId ? { ...w, x, y } : w))
      )

      // Notify other clients (debounced in production)
      sendWsMessage('WINDOW_MOVED', { window_id: windowId, x, y })
    },
    [setWindows, sendWsMessage]
  )

  // Resize window
  const resizeWindow = useCallback(
    (windowId: string, width: number, height: number) => {
      setWindows(prev =>
        prev.map(w => (w.id === windowId ? { ...w, width, height } : w))
      )

      // Notify other clients (debounced in production)
      sendWsMessage('WINDOW_RESIZED', { window_id: windowId, width, height })
    },
    [setWindows, sendWsMessage]
  )

  // Minimize window
  const minimizeWindow = useCallback(
    (windowId: string) => {
      setWindows(prev =>
        prev.map(w => (w.id === windowId ? { ...w, isMinimized: true, isFocused: false } : w))
      )

      if (focusedWindow === windowId) {
        setFocusedWindow(null)
      }

      sendWsMessage('WINDOW_MINIMIZED', { window_id: windowId })
    },
    [focusedWindow, setWindows, setFocusedWindow, sendWsMessage]
  )

  // Maximize window
  const maximizeWindow = useCallback(
    (windowId: string) => {
      setWindows(prev =>
        prev.map(w =>
          w.id === windowId
            ? { ...w, isMaximized: !w.isMaximized, isFocused: true }
            : { ...w, isFocused: false }
        )
      )
      setFocusedWindow(windowId)

      sendWsMessage('WINDOW_MAXIMIZED', { window_id: windowId })
    },
    [setWindows, setFocusedWindow, sendWsMessage]
  )

  // Restore window from minimized
  const restoreWindow = useCallback(
    (windowId: string) => {
      const maxZ = getMaxZIndex()

      setWindows(prev =>
        prev.map(w =>
          w.id === windowId
            ? { ...w, isMinimized: false, isFocused: true, zIndex: maxZ + 1 }
            : { ...w, isFocused: false }
        )
      )
      setFocusedWindow(windowId)

      sendWsMessage('WINDOW_RESTORED', { window_id: windowId })
    },
    [getMaxZIndex, setWindows, setFocusedWindow, sendWsMessage]
  )

  // Switch desktop
  const switchDesktop = useCallback(
    (desktopId: number) => {
      setCurrentDesktop(desktopId)
      setFocusedWindow(null)

      sendWsMessage('DESKTOP_SWITCHED', { desktop_id: desktopId })
    },
    [setCurrentDesktop, setFocusedWindow, sendWsMessage]
  )

  // Get windows for current desktop
  const currentWindows = windows.filter(w => w.desktopId === currentDesktop)
  const visibleWindows = currentWindows.filter(w => w.isVisible && !w.isMinimized)
  const minimizedWindows = currentWindows.filter(w => w.isMinimized)

  // Handle WebSocket messages
  const handleWsMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'WINDOW_OPENED':
            // Another client opened a window
            if (!windows.find(w => w.id === data.window_id)) {
              const newWindow: WindowData = {
                id: data.window_id,
                appId: data.app_id,
                title: data.title || 'Untitled',
                x: data.x,
                y: data.y,
                width: data.width,
                height: data.height,
                zIndex: getMaxZIndex() + 1,
                isMinimized: false,
                isMaximized: false,
                isFocused: false,
                isVisible: true,
                desktopId: data.desktop_id
              }
              setWindows(prev => [...prev, newWindow])
            }
            break

          case 'WINDOW_CLOSED':
            setWindows(prev => prev.filter(w => w.id !== data.window_id))
            break

          case 'WINDOW_MOVED':
            setWindows(prev =>
              prev.map(w =>
                w.id === data.window_id ? { ...w, x: data.x, y: data.y } : w
              )
            )
            break

          case 'WINDOW_RESIZED':
            setWindows(prev =>
              prev.map(w =>
                w.id === data.window_id
                  ? { ...w, width: data.width, height: data.height }
                  : w
              )
            )
            break

          case 'WINDOW_FOCUSED':
            setWindows(prev =>
              prev.map(w =>
                w.id === data.window_id
                  ? { ...w, isFocused: true, zIndex: getMaxZIndex() + 1 }
                  : { ...w, isFocused: false }
              )
            )
            break

          case 'WINDOW_MINIMIZED':
            setWindows(prev =>
              prev.map(w =>
                w.id === data.window_id ? { ...w, isMinimized: true } : w
              )
            )
            break

          case 'WINDOW_RESTORED':
            setWindows(prev =>
              prev.map(w =>
                w.id === data.window_id
                  ? { ...w, isMinimized: false, zIndex: getMaxZIndex() + 1 }
                  : w
              )
            )
            break

          case 'DESKTOP_SWITCHED':
            // Another user switched desktops (if shared desktop mode)
            break

          case 'PONG':
            // Heartbeat response
            break

          default:
            console.warn('Unknown WebSocket message type:', data.type)
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    },
    [windows, getMaxZIndex, setWindows]
  )

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!token || !user) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/api/v1/ws/desktop/${currentDesktop}?token=${token}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')

        // Send heartbeat every 30 seconds
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING' }))
          }
        }, 30000)
      }

      ws.onmessage = handleWsMessage

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')

        // Clear heartbeat interval
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }

        // Attempt reconnection after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connectWebSocket()
        }, 5000)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }, [token, user, currentDesktop, handleWsMessage])

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket()

    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }

      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current)
        heartbeatIntervalRef.current = null
      }
    }
  }, [connectWebSocket])

  // Reconnect WebSocket when desktop changes
  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close()
      connectWebSocket()
    }
  }, [currentDesktop])

  return {
    windows,
    currentWindows,
    visibleWindows,
    minimizedWindows,
    currentDesktop,
    focusedWindow,
    createWindow,
    closeWindow,
    focusWindow,
    moveWindow,
    resizeWindow,
    minimizeWindow,
    maximizeWindow,
    restoreWindow,
    switchDesktop
  }
}
