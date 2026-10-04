/**
 * Drawn icon set for Campus Customs.
 *
 * One consistent construction: 24×24 box, 1.6 stroke, round caps and joins,
 * no fills. Authored rather than pulled from a library so the few shapes the
 * site needs share the press-room character, and so nothing ships as an emoji
 * standing in for an icon.
 */

type IconName =
  | 'chat'
  | 'close'
  | 'menu'
  | 'search'
  | 'arrow-right'
  | 'check'
  | 'registration'
  | 'squeegee'
  | 'bag'

interface IconProps {
  name: IconName
  size?: number
  className?: string
  strokeWidth?: number
}

const PATHS: Record<IconName, React.ReactNode> = {
  // A printed speech mark — square like a stamped block, not a bubble.
  chat: (
    <>
      <path d="M4 5h16v11H9l-5 4V5Z" />
      <path d="M8.5 10.5h7" />
      <path d="M8.5 7.5h4" />
    </>
  ),
  close: (
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>
  ),
  menu: (
    <>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16l4 4" />
    </>
  ),
  'arrow-right': (
    <>
      <path d="M4 12h15" />
      <path d="M13 6l6 6-6 6" />
    </>
  ),
  check: <path d="M5 12.5l4.5 4.5L19 7" />,
  // The printer's registration cross, used to align colour plates.
  registration: (
    <>
      <circle cx="12" cy="12" r="6" />
      <path d="M12 1.5v7" />
      <path d="M12 15.5v7" />
      <path d="M1.5 12h7" />
      <path d="M15.5 12h7" />
    </>
  ),
  // A paper shop bag with folded handles.
  bag: (
    <>
      <path d="M5 8h14l-1 12H6L5 8Z" />
      <path d="M9 8V6a3 3 0 0 1 6 0v2" />
    </>
  ),
  // A squeegee pulling ink across a screen.
  squeegee: (
    <>
      <path d="M3 17h18" />
      <path d="M7 4h7l3 9H9.5L7 4Z" />
    </>
  ),
}

export default function Icon({
  name,
  size = 20,
  className,
  strokeWidth = 1.6,
}: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name]}
    </svg>
  )
}
