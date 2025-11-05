import { useMachine } from '@xstate/react'
import { desktopMachine, DesktopEvent } from '@/state/machines/desktopMachine'
import { useEffect } from 'react'

export function useDesktopMachine() {
  const [state, send] = useMachine(desktopMachine)

  // Helper functions
  const switchDesktop = (desktopId: number) => {
    send({ type: 'SWITCH_DESKTOP', desktopId })
  }

  const notifyWindowOpened = (windowId: string) => {
    send({ type: 'WINDOW_OPENED', windowId })
  }

  const notifyWindowClosed = (windowId: string) => {
    send({ type: 'WINDOW_CLOSED', windowId })
  }

  const enterFullscreen = (windowId: string) => {
    send({ type: 'ENTER_FULLSCREEN', windowId })
  }

  const exitFullscreen = () => {
    send({ type: 'EXIT_FULLSCREEN' })
  }

  const startScreenshare = () => {
    send({ type: 'START_SCREENSHARE' })
  }

  const stopScreenshare = () => {
    send({ type: 'STOP_SCREENSHARE' })
  }

  const lockDesktop = () => {
    send({ type: 'LOCK_DESKTOP' })
  }

  const unlockDesktop = () => {
    send({ type: 'UNLOCK_DESKTOP' })
  }

  const reportError = (error: string) => {
    send({ type: 'ERROR', error })
  }

  const clearError = () => {
    send({ type: 'CLEAR_ERROR' })
  }

  // Log state changes in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Desktop state:', state.value, state.context)
    }
  }, [state.value, state.context])

  return {
    // State
    state: state.value,
    context: state.context,
    currentDesktop: state.context.currentDesktop,
    activeWindows: state.context.activeWindows,
    lastAction: state.context.lastAction,
    error: state.context.error,

    // State checks
    isIdle: state.matches('idle'),
    isSwitching: state.matches('switching'),
    isFullscreen: state.matches('fullscreen'),
    isScreensharing: state.matches('screensharing'),
    isLocked: state.matches('locked'),
    hasError: state.matches('error'),

    // Actions
    switchDesktop,
    notifyWindowOpened,
    notifyWindowClosed,
    enterFullscreen,
    exitFullscreen,
    startScreenshare,
    stopScreenshare,
    lockDesktop,
    unlockDesktop,
    reportError,
    clearError,

    // Raw send function for custom events
    send
  }
}
