import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../stores/auth'
import {
  IconTarget,
  IconLogout,
  IconUser,
  IconSettings,
} from '../ui/Icons'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-base flex flex-col">
      {/* Header */}
      <header className="h-14 border-b border-border bg-elevated/50 backdrop-blur-sm sticky top-0 z-sticky">
        <div className="h-full max-w-[1600px] mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <Link to="/discovery" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-accent flex items-center justify-center">
              <IconTarget size={18} className="text-white" />
            </div>
            <span className="font-display font-semibold text-default tracking-tight">
              Discovery
            </span>
          </Link>

          {/* User menu */}
          <div className="flex items-center gap-4">
            <Link
              to="/admin"
              className="btn-ghost btn-sm text-muted hover:text-default"
              title="Admin settings"
            >
              <IconSettings size={18} />
              <span className="hidden sm:inline">Admin</span>
            </Link>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-7 h-7 rounded-full bg-bg-muted flex items-center justify-center">
                <IconUser size={14} className="text-muted" />
              </div>
              <span className="text-muted hidden sm:block">
                {user?.email || 'Guest'}
              </span>
            </div>
            <button
              onClick={logout}
              className="btn-ghost btn-sm text-muted hover:text-default"
              title="Sign out"
            >
              <IconLogout size={18} />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}

// Page container with max width and padding
interface PageContainerProps {
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
}

export function PageContainer({ children, size = 'lg' }: PageContainerProps) {
  const maxWidths = {
    sm: 'max-w-2xl',
    md: 'max-w-4xl',
    lg: 'max-w-6xl',
    xl: 'max-w-7xl',
    full: 'max-w-[1600px]',
  }

  return (
    <div className={`${maxWidths[size]} mx-auto px-6 py-8`}>
      {children}
    </div>
  )
}

// Page header with title and actions
interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
  breadcrumb?: ReactNode
}

export function PageHeader({ title, description, actions, breadcrumb }: PageHeaderProps) {
  return (
    <div className="mb-8">
      {breadcrumb && <div className="mb-3">{breadcrumb}</div>}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-default tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-muted">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3">{actions}</div>}
      </div>
    </div>
  )
}

// Breadcrumb component
interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1.5 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-1.5">
            {index > 0 && (
              <span className="text-faint">/</span>
            )}
            {item.href ? (
              <Link to={item.href} className="text-muted hover:text-default transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className="text-default font-medium">{item.label}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
