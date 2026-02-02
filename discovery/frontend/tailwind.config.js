/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Background layers
        bg: {
          base: 'hsl(var(--bg-base) / <alpha-value>)',
          elevated: 'hsl(var(--bg-elevated) / <alpha-value>)',
          surface: 'hsl(var(--bg-surface) / <alpha-value>)',
          muted: 'hsl(var(--bg-muted) / <alpha-value>)',
          subtle: 'hsl(var(--bg-subtle) / <alpha-value>)',
        },
        // Foreground
        fg: {
          default: 'hsl(var(--fg-default) / <alpha-value>)',
          muted: 'hsl(var(--fg-muted) / <alpha-value>)',
          subtle: 'hsl(var(--fg-subtle) / <alpha-value>)',
          faint: 'hsl(var(--fg-faint) / <alpha-value>)',
        },
        // Accent
        accent: {
          DEFAULT: 'hsl(var(--accent) / <alpha-value>)',
          muted: 'hsl(var(--accent-muted) / <alpha-value>)',
          subtle: 'hsl(var(--accent-subtle) / <alpha-value>)',
        },
        // Semantic
        success: {
          DEFAULT: 'hsl(var(--success) / <alpha-value>)',
          muted: 'hsl(var(--success-muted) / <alpha-value>)',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning) / <alpha-value>)',
          muted: 'hsl(var(--warning-muted) / <alpha-value>)',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive) / <alpha-value>)',
          muted: 'hsl(var(--destructive-muted) / <alpha-value>)',
        },
        // Borders
        border: {
          DEFAULT: 'hsl(var(--border-default) / <alpha-value>)',
          muted: 'hsl(var(--border-muted) / <alpha-value>)',
          accent: 'hsl(var(--border-accent) / <alpha-value>)',
        },
        // Priority tiers
        tier: {
          high: 'hsl(var(--tier-high) / <alpha-value>)',
          medium: 'hsl(var(--tier-medium) / <alpha-value>)',
          low: 'hsl(var(--tier-low) / <alpha-value>)',
        },
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        glow: 'var(--shadow-glow)',
      },
      transitionDuration: {
        fast: '120ms',
        base: '200ms',
        slow: '350ms',
      },
      zIndex: {
        base: '1',
        dropdown: '100',
        sticky: '200',
        modal: '300',
        toast: '400',
      },
      animation: {
        'fade-in': 'fade-in 200ms ease-out forwards',
        'slide-up': 'slide-up 350ms ease-out forwards',
        'slide-down': 'slide-down 350ms ease-out forwards',
        'scale-in': 'scale-in 350ms ease-out forwards',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-down': {
          from: { opacity: '0', transform: 'translateY(-8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
