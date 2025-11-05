import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { useDesktop } from '@/hooks/useDesktop'
import {
  Menu,
  Search,
  Bell,
  User,
  Settings,
  LogOut,
  Grid3x3,
  Clock
} from 'lucide-react'

export function TopBar() {
  const { user, logout } = useAuth()
  const { currentDesktop, switchDesktop } = useDesktop()
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showDesktopMenu, setShowDesktopMenu] = useState(false)

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  // Format time
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    })
  }

  // Format date
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  }

  // Handle desktop switch
  const handleDesktopSwitch = (desktopId: number) => {
    switchDesktop(desktopId)
    setShowDesktopMenu(false)
  }

  // Handle logout
  const handleLogout = () => {
    if (confirm('Are you sure you want to log out?')) {
      logout()
    }
  }

  return (
    <div className="fixed top-0 left-0 right-0 h-16 bg-slate-900/90 backdrop-blur-xl border-b border-slate-700/50 z-40">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left Section - Logo & Menu */}
        <div className="flex items-center gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              GETLOOD
            </span>
          </div>

          {/* Main Menu */}
          <button
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Menu"
          >
            <Menu className="w-5 h-5 text-gray-400" />
          </button>

          {/* Search */}
          <button
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Search"
          >
            <Search className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Center Section - Desktop Switcher */}
        <div className="relative">
          <button
            onClick={() => setShowDesktopMenu(!showDesktopMenu)}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Grid3x3 className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300">Desktop {currentDesktop}</span>
          </button>

          <AnimatePresence>
            {showDesktopMenu && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden"
              >
                <div className="p-2 space-y-1 min-w-[150px]">
                  {[1, 2, 3, 4].map((desktop) => (
                    <button
                      key={desktop}
                      onClick={() => handleDesktopSwitch(desktop)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        currentDesktop === desktop
                          ? 'bg-primary text-white'
                          : 'text-gray-300 hover:bg-slate-700'
                      }`}
                    >
                      Desktop {desktop}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Section - Time, Notifications, User */}
        <div className="flex items-center gap-2">
          {/* Time & Date */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-lg">
            <Clock className="w-4 h-4 text-gray-400" />
            <div className="text-sm">
              <div className="text-gray-300 font-medium">{formatTime(currentTime)}</div>
              <div className="text-gray-500 text-xs">{formatDate(currentTime)}</div>
            </div>
          </div>

          {/* Notifications */}
          <button
            className="relative p-2 hover:bg-slate-800 rounded-lg transition-colors"
            title="Notifications"
          >
            <Bell className="w-5 h-5 text-gray-400" />
            <div className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-1.5 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <div className="w-6 h-6 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-300">{user?.display_name || 'User'}</span>
            </button>

            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute top-full mt-2 right-0 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden"
                >
                  <div className="p-2 space-y-1 min-w-[200px]">
                    {/* User Info */}
                    <div className="px-3 py-2 border-b border-slate-700">
                      <div className="text-sm font-medium text-gray-200">
                        {user?.display_name}
                      </div>
                      <div className="text-xs text-gray-500">{user?.email}</div>
                      <div className="mt-1 inline-block px-2 py-0.5 bg-primary/20 text-primary text-xs rounded">
                        {user?.tier?.toUpperCase() || 'FREE'}
                      </div>
                    </div>

                    {/* Menu Items */}
                    <button
                      onClick={() => setShowUserMenu(false)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>

                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
