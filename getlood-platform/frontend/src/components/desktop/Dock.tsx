import { useState, useRef } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { useDesktop } from '@/hooks/useDesktop'
import {
  MessageSquare,
  Terminal,
  FileText,
  Settings,
  Database,
  Box,
  Workflow,
  Plus
} from 'lucide-react'

interface AppDefinition {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}

const APPS: AppDefinition[] = [
  { id: 'chat', name: 'Chat', icon: MessageSquare, color: 'text-blue-400' },
  { id: 'terminal', name: 'Terminal', icon: Terminal, color: 'text-green-400' },
  { id: 'notes', name: 'Notes', icon: FileText, color: 'text-yellow-400' },
  { id: 'workflow', name: 'Workflow', icon: Workflow, color: 'text-purple-400' },
  { id: 'database', name: 'Database', icon: Database, color: 'text-cyan-400' },
  { id: 'agents', name: 'Agents', icon: Box, color: 'text-pink-400' },
  { id: 'settings', name: 'Settings', icon: Settings, color: 'text-gray-400' }
]

export function Dock() {
  const { createWindow, currentWindows } = useDesktop()
  const mouseX = useMotionValue(Infinity)

  // Check if app is running
  const isAppRunning = (appId: string) => {
    return currentWindows.some(w => w.appId === appId)
  }

  // Handle app launch
  const handleLaunch = (app: AppDefinition) => {
    // Check if app is already open, if so focus it
    const existingWindow = currentWindows.find(w => w.appId === app.id)

    if (!existingWindow) {
      // Create new window
      createWindow({
        appId: app.id,
        title: app.name
      })
    }
  }

  return (
    <motion.div
      onMouseMove={(e) => mouseX.set(e.pageX)}
      onMouseLeave={() => mouseX.set(Infinity)}
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50"
    >
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl px-3 py-2 shadow-2xl">
        <div className="flex items-end gap-2 h-16">
          {APPS.map((app) => (
            <DockIcon
              key={app.id}
              app={app}
              mouseX={mouseX}
              onClick={() => handleLaunch(app)}
              isRunning={isAppRunning(app.id)}
            />
          ))}

          {/* Separator */}
          <div className="w-px h-10 bg-slate-700 mx-1 self-center" />

          {/* Add App Button */}
          <DockIcon
            app={{ id: 'add', name: 'Add App', icon: Plus, color: 'text-gray-400' }}
            mouseX={mouseX}
            onClick={() => alert('Add app functionality coming soon!')}
            isRunning={false}
          />
        </div>
      </div>
    </motion.div>
  )
}

interface DockIconProps {
  app: AppDefinition
  mouseX: any
  onClick: () => void
  isRunning: boolean
}

function DockIcon({ app, mouseX, onClick, isRunning }: DockIconProps) {
  const ref = useRef<HTMLButtonElement>(null)
  const [isHovered, setIsHovered] = useState(false)

  const distance = useTransform(mouseX, (val) => {
    const bounds = ref.current?.getBoundingClientRect() ?? { x: 0, width: 0 }
    return val - bounds.x - bounds.width / 2
  })

  const widthSync = useTransform(distance, [-150, 0, 150], [48, 64, 48])
  const width = useSpring(widthSync, { mass: 0.1, stiffness: 150, damping: 12 })

  const Icon = app.icon

  return (
    <div className="flex flex-col items-center">
      <motion.button
        ref={ref}
        style={{ width }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
        className={`aspect-square rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center transition-colors relative group ${
          isRunning ? 'ring-2 ring-primary/50' : ''
        }`}
        whileHover={{ y: -8 }}
        whileTap={{ scale: 0.9 }}
      >
        <Icon className={`w-6 h-6 ${app.color}`} />

        {/* Running indicator */}
        {isRunning && (
          <div className="absolute -bottom-1 w-1 h-1 bg-primary rounded-full" />
        )}

        {/* Tooltip */}
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute -top-10 px-2 py-1 bg-slate-900 border border-slate-700 rounded-lg text-xs text-gray-200 whitespace-nowrap pointer-events-none"
          >
            {app.name}
          </motion.div>
        )}
      </motion.button>
    </div>
  )
}
