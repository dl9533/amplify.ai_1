import { ButtonHTMLAttributes, forwardRef } from 'react'
import { IconSpinner } from './Icons'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      iconPosition = 'left',
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseClass = `btn-${variant} btn-${size}`
    const isDisabled = disabled || loading

    return (
      <button
        ref={ref}
        className={`${baseClass} ${className}`}
        disabled={isDisabled}
        {...props}
      >
        {loading ? (
          <IconSpinner size={size === 'xs' || size === 'sm' ? 14 : 18} />
        ) : icon && iconPosition === 'left' ? (
          icon
        ) : null}
        {children}
        {!loading && icon && iconPosition === 'right' ? icon : null}
      </button>
    )
  }
)

Button.displayName = 'Button'

// Icon-only button variant
interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  label: string // Required for accessibility
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      variant = 'ghost',
      size = 'md',
      loading = false,
      label,
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: 'w-8 h-8',
      md: 'w-9 h-9',
      lg: 'w-10 h-10',
    }

    return (
      <button
        ref={ref}
        className={`btn-${variant} ${sizeClasses[size]} p-0 flex items-center justify-center rounded-md ${className}`}
        disabled={disabled || loading}
        aria-label={label}
        title={label}
        {...props}
      >
        {loading ? <IconSpinner size={18} /> : children}
      </button>
    )
  }
)

IconButton.displayName = 'IconButton'
