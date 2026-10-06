/**
 * Mock data used when the backend is unavailable.
 * Replace with real API calls once endpoints are live.
 */

export const mockDashboardSummary = {
  securityScore: 74,
  scoreLabel: 'Good',
  scoreAccent: 'success',

  recentScans: {
    total: 128,
    lastScan: '2 minutes ago',
    changeLabel: '+12 this week',
  },

  threatSummary: {
    high: 2,
    medium: 7,
    low: 14,
    safe: 105,
  },
}

export const mockRecentScans = [
  { id: 1, type: 'URL',      target: 'https://suspicious-site.net',  result: 'Malicious', severity: 'danger',  time: '2 min ago' },
  { id: 2, type: 'Password', target: 'P@ssw0rd123',                  result: 'Weak',      severity: 'warning', time: '15 min ago' },
  { id: 3, type: 'Email',    target: 'Phishing attempt #38',         result: 'Phishing',  severity: 'danger',  time: '1 hr ago' },
  { id: 4, type: 'URL',      target: 'https://github.com',           result: 'Safe',      severity: 'success', time: '2 hr ago' },
  { id: 5, type: 'Password', target: '••••••••••',                   result: 'Strong',    severity: 'success', time: '3 hr ago' },
]

export const mockQuickActions = [
  { id: 'url',       label: 'Check a URL',         iconName: 'link',  path: '/url',       description: 'Scan a link for phishing and threats' },
  { id: 'phishing',  label: 'Analyse an Email',    iconName: 'mail',  path: '/phishing',  description: 'Check an email for phishing indicators' },
  { id: 'password',  label: 'Test a Password',     iconName: 'lock',  path: '/password',  description: 'Measure how strong a password is' },
  { id: 'assistant', label: 'Ask the Assistant',   iconName: 'bot',   path: '/assistant', description: 'Get plain-English security guidance' },
]
