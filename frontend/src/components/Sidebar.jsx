import { NavLink } from 'react-router-dom'
import Icon from '../components/Icon'
import './Sidebar.css'

const NAV_ITEMS = [
  { path: '/',          label: 'Dashboard',         iconName: 'grid' },
  { path: '/url',       label: 'URL Analysis',       iconName: 'link' },
  { path: '/phishing',  label: 'Phishing Email',     iconName: 'mail' },
  { path: '/password',  label: 'Password Analysis',  iconName: 'lock' },
  { path: '/assistant', label: 'AI Assistant',        iconName: 'bot' },
  { path: '/history',   label: 'Scan History',       iconName: 'clock' },
  { path: '/reports',   label: 'Reports',            iconName: 'chart' },
  { path: '/profile',   label: 'Profile',            iconName: 'user' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-icon"><Icon name="shield" size={20} /></span>
        <span className="brand-name">AEGIS</span>
      </div>

      <nav className="sidebar-nav">
        <ul>
          {NAV_ITEMS.map(({ path, label, iconName }) => (
            <li key={path}>
              <NavLink
                to={path}
                end={path === '/'}
                className={({ isActive }) =>
                  `nav-item${isActive ? ' nav-item--active' : ''}`
                }
              >
                <span className="nav-icon"><Icon name={iconName} size={16} /></span>
                <span className="nav-label">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-version">v0.1.0</span>
      </div>
    </aside>
  )
}
