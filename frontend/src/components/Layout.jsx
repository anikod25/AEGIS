import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import './Layout.css'

const PAGE_TITLES = {
  '/':          'Dashboard',
  '/url':       'URL Analysis',
  '/phishing':  'Phishing Email Analysis',
  '/password':  'Password Analysis',
  '/assistant': 'AI Assistant',
  '/history':   'Scan History',
  '/reports':   'Reports',
  '/profile':   'Profile',
}

export default function Layout() {
  const { pathname } = useLocation()
  const title = PAGE_TITLES[pathname] ?? 'AEGIS'
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="layout">
      <button
        className="mobile-menu-btn"
        aria-label="Toggle navigation"
        onClick={() => setSidebarOpen(o => !o)}
      >
        ≡
      </button>

      {/* Overlay — closes sidebar when tapped on mobile */}
      <div
        className={sidebarOpen ? 'sidebar-overlay sidebar-overlay--visible' : 'sidebar-overlay'}
        onClick={() => setSidebarOpen(false)}
      />

      <div
        className={sidebarOpen ? 'layout-sidebar sidebar--open' : 'layout-sidebar'}
        onClick={() => setSidebarOpen(false)}
      >
        <Sidebar />
      </div>

      <div className="layout-main">
        <Header title={title} />
        <main className="layout-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
