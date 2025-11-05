import { setup, assign } from 'xstate'

export interface DesktopContext {
  currentDesktop: number
  activeWindows: string[]
  lastAction: string | null
  error: string | null
}

export type DesktopEvent =
  | { type: 'SWITCH_DESKTOP'; desktopId: number }
  | { type: 'WINDOW_OPENED'; windowId: string }
  | { type: 'WINDOW_CLOSED'; windowId: string }
  | { type: 'ENTER_FULLSCREEN'; windowId: string }
  | { type: 'EXIT_FULLSCREEN' }
  | { type: 'START_SCREENSHARE' }
  | { type: 'STOP_SCREENSHARE' }
  | { type: 'LOCK_DESKTOP' }
  | { type: 'UNLOCK_DESKTOP' }
  | { type: 'ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }

export const desktopMachine = setup({
  types: {
    context: {} as DesktopContext,
    events: {} as DesktopEvent
  },
  guards: {
    isValidDesktop: ({ context, event }) => {
      if (event.type !== 'SWITCH_DESKTOP') return false
      return event.desktopId >= 1 && event.desktopId <= 4
    },
    hasActiveWindows: ({ context }) => {
      return context.activeWindows.length > 0
    }
  },
  actions: {
    switchDesktop: assign({
      currentDesktop: ({ context, event }) => {
        if (event.type === 'SWITCH_DESKTOP') {
          return event.desktopId
        }
        return context.currentDesktop
      },
      lastAction: 'SWITCH_DESKTOP'
    }),
    openWindow: assign({
      activeWindows: ({ context, event }) => {
        if (event.type === 'WINDOW_OPENED') {
          return [...context.activeWindows, event.windowId]
        }
        return context.activeWindows
      },
      lastAction: 'WINDOW_OPENED'
    }),
    closeWindow: assign({
      activeWindows: ({ context, event }) => {
        if (event.type === 'WINDOW_CLOSED') {
          return context.activeWindows.filter(id => id !== event.windowId)
        }
        return context.activeWindows
      },
      lastAction: 'WINDOW_CLOSED'
    }),
    setError: assign({
      error: ({ event }) => {
        if (event.type === 'ERROR') {
          return event.error
        }
        return null
      }
    }),
    clearError: assign({
      error: null
    })
  }
}).createMachine({
  id: 'desktop',
  initial: 'idle',
  context: {
    currentDesktop: 1,
    activeWindows: [],
    lastAction: null,
    error: null
  },
  states: {
    idle: {
      on: {
        SWITCH_DESKTOP: {
          target: 'switching',
          guard: 'isValidDesktop'
        },
        WINDOW_OPENED: {
          actions: 'openWindow'
        },
        WINDOW_CLOSED: {
          actions: 'closeWindow'
        },
        ENTER_FULLSCREEN: {
          target: 'fullscreen'
        },
        START_SCREENSHARE: {
          target: 'screensharing'
        },
        LOCK_DESKTOP: {
          target: 'locked'
        },
        ERROR: {
          target: 'error',
          actions: 'setError'
        }
      }
    },
    switching: {
      entry: 'switchDesktop',
      after: {
        300: 'idle'
      }
    },
    fullscreen: {
      on: {
        EXIT_FULLSCREEN: {
          target: 'idle'
        },
        WINDOW_CLOSED: {
          target: 'idle',
          actions: 'closeWindow'
        }
      }
    },
    screensharing: {
      on: {
        STOP_SCREENSHARE: {
          target: 'idle'
        },
        SWITCH_DESKTOP: {
          target: 'switching',
          guard: 'isValidDesktop'
        },
        WINDOW_OPENED: {
          actions: 'openWindow'
        },
        WINDOW_CLOSED: {
          actions: 'closeWindow'
        }
      }
    },
    locked: {
      on: {
        UNLOCK_DESKTOP: {
          target: 'idle'
        }
      }
    },
    error: {
      on: {
        CLEAR_ERROR: {
          target: 'idle',
          actions: 'clearError'
        }
      }
    }
  }
})
