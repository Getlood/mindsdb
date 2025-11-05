import { atom } from 'jotai'

export interface WindowData {
  id: string
  appId: string
  title: string
  x: number
  y: number
  width: number
  height: number
  zIndex: number
  isMinimized: boolean
  isMaximized: boolean
  isFocused: boolean
  isVisible: boolean
  desktopId: number
}

export const windowsAtom = atom<WindowData[]>([])
export const currentDesktopAtom = atom<number>(1)
export const focusedWindowAtom = atom<string | null>(null)
