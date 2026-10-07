import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './ProfilePage.css'

function initials(name) {
  return (name ?? 'U')
    .split(' ')
    .map(p => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'long', day: 'numeric',
  })
}

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const name  = user?.name  ?? 'Unknown'
  const email = user?.email ?? '—'
  const role  = user?.role  ?? 'user'
  const since = formatDate(user?.created_at)

  function handleSignOut() {
    logout()
    navigate('/login')
  }

  return (
    <div className="prof-page">
      {/* Avatar + identity */}
      <div className="prof-identity">
        <div className="prof-avatar" aria-hidden="true">{initials(name)}</div>
        <div className="prof-identity-info">
          <h1 className="prof-name">{name}</h1>
          <span className={`prof-role-badge prof-role-badge--${role}`}>
            {role === 'admin' ? 'Administrator' : 'User'}
          </span>
        </div>
      </div>

      {/* Account section */}
      <section className="prof-section">
        <h2 className="prof-section-title">Account</h2>
        <div className="prof-fields">
          <div className="prof-field">
            <span className="prof-field-label">Full name</span>
            <span className="prof-field-value">{name}</span>
          </div>
          <div className="prof-field">
            <span className="prof-field-label">Email address</span>
            <span className="prof-field-value">{email}</span>
          </div>
          <div className="prof-field">
            <span className="prof-field-label">Member since</span>
            <span className="prof-field-value">{since}</span>
          </div>
          <div className="prof-field">
            <span className="prof-field-label">Role</span>
            <span className="prof-field-value">{role === 'admin' ? 'Administrator' : 'Standard user'}</span>
          </div>
        </div>
        <p className="prof-note">
          To update your account details, contact your administrator.
        </p>
      </section>

      {/* Session section */}
      <section className="prof-section">
        <h2 className="prof-section-title">Session</h2>
        <p className="prof-session-desc">
          Signing out will clear your session. You will need to log in again to access AEGIS.
        </p>
        <button className="prof-signout-btn" onClick={handleSignOut}>
          Sign out
        </button>
      </section>
    </div>
  )
}
