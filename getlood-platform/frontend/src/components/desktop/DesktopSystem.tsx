import { useState } from 'react'
import { useAtom } from 'jotai'
import { currentDesktopAtom, windowsAtom } from '@/state/atoms/desktopAtoms'
import { Window } from './Window'
import { Dock } from './Dock'
import { TopBar } from './TopBar'
import { Taskbar } from './Taskbar'

export function DesktopSystem() {
  const [currentDesktop] = useAtom(currentDesktopAtom)
  const [windows] = useAtom(windowsAtom)

  const currentWindows = windows.filter(w =>
    w.desktopId === currentDesktop && w.isVisible && !w.isMinimized
  )

  return (
    <div className="relative h-screen w-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-20 left-20 w-96 h-96 bg-primary/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-secondary/30 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* TopBar */}
      <TopBar />

      {/* Desktop area */}
      <div className="relative h-[calc(100vh-64px-64px)] mt-16">
        {/* Windows */}
        {currentWindows
          .sort((a, b) => a.zIndex - b.zIndex)
          .map(window => (
            <Window key={window.id} window={window} />
          ))}
      </div>

      {/* Taskbar */}
      <Taskbar />

      {/* Dock */}
      <Dock />
    </div>
  )
}
