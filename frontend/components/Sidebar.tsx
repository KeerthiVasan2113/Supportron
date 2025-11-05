'use client'

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface NavItem {
  id: string
  label: string
  path: string
  icon?: string
}

const navItems: NavItem[] = [
  { id: 'user', label: 'User Details & Activity', path: '/dashboard/user' },
  { id: 'policies', label: 'Client Policies', path: '/dashboard/policies' },
  { id: 'docs', label: 'Reference Docs', path: '/dashboard/docs' },
  { id: 'chat', label: 'Chat', path: '/dashboard/chat' },
]

export const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout, isAdmin } = useAuth()

  const handleNavigation = (path: string) => {
    router.push(path)
  }

  return (
    <aside
      className={`bg-tech-surface border-r border-tech-border transition-all duration-300 flex flex-col ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-4 border-b border-tech-border flex items-center justify-between">
        {!isCollapsed && (
          <h2 className="text-neon-cyan font-bold text-lg">SUPPORTRON</h2>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-tech-surface-hover rounded-lg transition-colors"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg
            className={`w-5 h-5 text-text-primary transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.path
          return (
            <button
              key={item.id}
              onClick={() => handleNavigation(item.path)}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all ${
                isActive
                  ? 'bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/50'
                  : 'text-text-secondary hover:bg-tech-surface-hover hover:text-text-primary'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xs">●</span>
                {!isCollapsed && <span className="text-sm font-medium">{item.label}</span>}
              </div>
            </button>
          )
        })}

        {isAdmin && (
          <button
            onClick={() => handleNavigation('/dashboard/admin')}
            className={`w-full text-left px-4 py-3 rounded-xl transition-all ${
              pathname === '/dashboard/admin'
                ? 'bg-accent/20 text-accent border border-accent/50'
                : 'text-text-secondary hover:bg-tech-surface-hover hover:text-text-primary'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-xs">⚙</span>
              {!isCollapsed && <span className="text-sm font-medium">Admin Panel</span>}
            </div>
          </button>
        )}
      </nav>

      <div className="p-4 border-t border-tech-border">
        {!isCollapsed && user && (
          <div className="mb-4 text-sm">
            <p className="text-text-primary font-medium">{user.name}</p>
            <p className="text-text-muted text-xs">{user.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full px-4 py-2 bg-red-500/20 text-red-400 rounded-xl hover:bg-red-500/30 transition-colors text-sm font-medium"
        >
          {!isCollapsed ? 'Logout' : '→'}
        </button>
      </div>
    </aside>
  )
}

