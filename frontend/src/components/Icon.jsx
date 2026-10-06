/**
 * Icon — thin inline SVG icon wrapper.
 *
 * Props:
 *   name      {string}  icon identifier (see ICONS map below)
 *   size      {number}  width/height in px (default 16)
 *   className {string}  optional extra CSS class
 */

const ICONS = {
  grid: (
    <>
      <path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z" />
    </>
  ),
  link: (
    <>
      <path d="M6.5 9.5a3.5 3.5 0 0 0 4.95 0l1.5-1.5a3.5 3.5 0 0 0-4.95-4.95l-.75.75" />
      <path d="M9.5 6.5a3.5 3.5 0 0 0-4.95 0L3.05 8a3.5 3.5 0 0 0 4.95 4.95l.75-.75" />
    </>
  ),
  mail: (
    <>
      <rect x="2" y="4" width="12" height="9" rx="1" />
      <path d="M2 4l6 5 6-5" />
    </>
  ),
  lock: (
    <>
      <rect x="4" y="8" width="8" height="6" rx="1" />
      <path d="M4 8V6a4 4 0 0 1 8 0v2" />
    </>
  ),
  bot: (
    <>
      <rect x="3" y="5" width="10" height="8" rx="2" />
      <path d="M7 9h.01M9 9h.01" />
      <path d="M6 13v1M10 13v1" />
      <path d="M8 5V3" />
    </>
  ),
  clock: (
    <>
      <circle cx="8" cy="8" r="6" />
      <path d="M8 5v3l2 2" />
    </>
  ),
  chart: (
    <>
      <path d="M2 14V8h3v6H2zM7 14V5h3v9H7zM12 14V2h2v12h-2z" />
    </>
  ),
  user: (
    <>
      <circle cx="8" cy="5" r="3" />
      <path d="M2 14c0-3.314 2.686-5 6-5s6 1.686 6 5" />
    </>
  ),
  shield: (
    <>
      <path d="M8 2L3 4.5v4C3 11.5 5.5 14 8 15c2.5-1 5-3.5 5-6.5v-4L8 2z" />
    </>
  ),
  scan: (
    <>
      <circle cx="8" cy="8" r="6" />
      <circle cx="8" cy="8" r="2" />
      <path d="M8 2v2M8 12v2M2 8h2M12 8h2" />
    </>
  ),
  alert: (
    <>
      <path d="M8 2L2 13h12L8 2z" />
      <path d="M8 7v3" />
      <circle cx="8" cy="12" r=".5" fill="currentColor" />
    </>
  ),
  info: (
    <>
      <circle cx="8" cy="8" r="6" />
      <path d="M8 7v4" />
      <circle cx="8" cy="5.5" r=".5" fill="currentColor" />
    </>
  ),
  check: (
    <>
      <path d="M3 8l4 4 6-7" />
    </>
  ),
  search: (
    <>
      <circle cx="7" cy="7" r="4" />
      <path d="M10.5 10.5L14 14" />
    </>
  ),
  refresh: (
    <>
      <path d="M13 8A5 5 0 1 1 8 3" />
      <path d="M13 3v5h-5" />
    </>
  ),
  power: (
    <>
      <path d="M6 3.5a5 5 0 1 0 4 0" />
      <path d="M8 2v5" />
    </>
  ),
  'chevron-down': (
    <>
      <path d="M4 6l4 4 4-4" />
    </>
  ),
  external: (
    <>
      <path d="M9 3h4v4" />
      <path d="M9 7L13 3" />
      <path d="M7 5H4a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V10" />
    </>
  ),
}

export default function Icon({ name, size = 16, className }) {
  const paths = ICONS[name]
  if (!paths) return null

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      {paths}
    </svg>
  )
}
