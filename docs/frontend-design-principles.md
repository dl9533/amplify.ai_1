# Frontend Design Principles

> **For Claude:** Follow these principles when implementing any frontend/UI components. These are non-negotiable guidelines that ensure visual consistency and quality.

---

## Design Philosophy

**Clean. Minimal. Modern.**

We build interfaces that respect the user's attention. Every element earns its place. We draw inspiration from Linear, Vercel, and Stripe—tools built by developers, for developers.

---

## Core Principles

### 1. Intentional Minimalism

Minimalism is not about having less—it's about making room for what matters.

- **Remove, don't add**: Before adding any element, ask "Does this help the user accomplish their goal?"
- **Progressive disclosure**: Reveal information and options as users need them, not all at once
- **One primary action per view**: Every screen should have a clear purpose and primary action
- **Reduce cognitive load**: Fewer choices, clearer paths, faster decisions

```
❌ WRONG: Show all 15 filter options at once
✅ RIGHT: Show 3 common filters, "More filters" expands the rest
```

### 2. Visual Hierarchy

Structure guides the eye. Without hierarchy, interfaces feel chaotic.

- **Size communicates importance**: Primary actions are larger, secondary are smaller
- **Weight creates focus**: Bold for headlines and key data, regular for body text
- **Spacing groups related items**: Proximity implies relationship
- **Color draws attention sparingly**: Use accent colors only for actionable elements

```
Hierarchy Order:
1. Page title / Primary heading
2. Section headers
3. Key data / Metrics
4. Body content
5. Tertiary / Meta information
```

### 3. Purposeful White Space

Negative space is not empty—it's an active design element.

- **Generous padding**: Content needs room to breathe (min 16px padding on containers)
- **Consistent spacing scale**: Use 4px base unit (4, 8, 12, 16, 24, 32, 48, 64, 96)
- **Group with space**: Items with 8px gap are related; 24px+ gap indicates separation
- **Margins create rhythm**: Consistent vertical rhythm makes pages scannable

```css
/* Spacing scale (Tailwind) */
gap-1  = 4px   /* Tight grouping */
gap-2  = 8px   /* Related items */
gap-3  = 12px  /* Default spacing */
gap-4  = 16px  /* Section padding */
gap-6  = 24px  /* Section separation */
gap-8  = 32px  /* Major sections */
gap-12 = 48px  /* Page sections */
```

### 4. Restrained Color

Color is a scarce resource. Use it intentionally.

#### Dark Mode First (Default)

We use a Linear-style dark interface optimized for developer tools:

```css
/* Background layers (dark mode) */
--background:        #0a0a0a;  /* Page background */
--background-subtle: #111111;  /* Cards, panels */
--background-muted:  #1a1a1a;  /* Hover states, secondary surfaces */
--background-accent: #262626;  /* Active states, borders */

/* Text hierarchy */
--foreground:        #fafafa;  /* Primary text */
--foreground-muted:  #a1a1a1;  /* Secondary text */
--foreground-subtle: #737373;  /* Tertiary text, placeholders */

/* Accent colors (desaturated for dark mode) */
--primary:           #3b82f6;  /* Primary actions - blue */
--primary-foreground:#ffffff;
--destructive:       #ef4444;  /* Errors, delete actions - red */
--success:           #22c55e;  /* Success states - green */
--warning:           #f59e0b;  /* Warnings - amber */
```

#### Light Mode (Optional)

```css
--background:        #ffffff;
--background-subtle: #f9fafb;
--background-muted:  #f3f4f6;
--foreground:        #111827;
--foreground-muted:  #6b7280;
--foreground-subtle: #9ca3af;
```

#### Color Rules

1. **Never use pure black (#000000)** for backgrounds—use #0a0a0a or #111111
2. **Desaturate bright colors** in dark mode to prevent visual vibration
3. **Don't rely on color alone**—always pair with text labels or icons
4. **Accent colors are for actions only**—not decoration
5. **Status colors are semantic**—red=error, green=success, amber=warning, blue=info

### 5. Typography

Text is the primary interface element. Make it count.

#### Font Stack

```css
/* Primary: Inter or Geist Sans */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Monospace: For code, data, IDs */
--font-mono: 'Geist Mono', 'JetBrains Mono', 'Fira Code', monospace;
```

#### Type Scale

```css
/* Size scale */
text-xs   = 12px / 1.5  /* Labels, captions, timestamps */
text-sm   = 14px / 1.5  /* Body text, form inputs */
text-base = 16px / 1.5  /* Default body */
text-lg   = 18px / 1.5  /* Subheadings */
text-xl   = 20px / 1.4  /* Section headers */
text-2xl  = 24px / 1.3  /* Page titles */
text-3xl  = 30px / 1.2  /* Hero headings */
```

#### Typography Rules

1. **Maximum 2 font families**: Sans-serif for UI, monospace for code/data
2. **Maximum 3 font weights**: Regular (400), Medium (500), Semibold (600)
3. **Use tabular numbers** for data tables: `font-variant-numeric: tabular-nums`
4. **Line length**: 60-80 characters for body text (max-w-prose)
5. **No orphans/widows**: Break lines intentionally in headings

### 6. Accessibility First

Accessibility is not optional. It's a legal requirement and the right thing to do.

#### Contrast Requirements (WCAG 2.1)

| Element | Minimum Ratio | Target Ratio |
|---------|---------------|--------------|
| Body text | 4.5:1 | 7:1 (AAA) |
| Large text (18px+) | 3:1 | 4.5:1 |
| UI components | 3:1 | 4.5:1 |
| Focus indicators | 3:1 | — |

#### Accessibility Checklist

- [ ] All interactive elements are keyboard accessible
- [ ] Focus states are clearly visible (2px ring, offset)
- [ ] Color is never the only indicator of state
- [ ] Images have alt text; decorative images have `alt=""`
- [ ] Form inputs have visible labels (not just placeholders)
- [ ] Error messages are announced to screen readers
- [ ] Touch targets are minimum 44x44px on mobile
- [ ] Animations respect `prefers-reduced-motion`

```tsx
// Focus ring pattern
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background"
```

### 7. Keyboard-First Interaction

Power users live on the keyboard. Design for them.

#### Command Palette (Cmd+K)

Every application should have a command palette for:
- Navigation between pages
- Quick actions (create, search, filter)
- Settings access

```tsx
// Use cmdk library for command palette
import { Command } from 'cmdk'
```

#### Keyboard Shortcuts

- Document all shortcuts in a discoverable location
- Use standard conventions (Cmd+S save, Cmd+K command, Escape close)
- Show hints in UI: buttons can show "⌘K" next to label

#### Focus Management

- Trap focus in modals and dialogs
- Return focus to trigger element when closing
- Skip links for main content

### 8. Motion & Microinteractions

Animation should be functional, not decorative.

#### Principles

- **Purposeful**: Animation communicates state change or provides feedback
- **Fast**: Most transitions 150-200ms; never exceed 300ms for UI
- **Subtle**: Users should feel, not notice, animations
- **Respectful**: Honor `prefers-reduced-motion`

#### Timing Functions

```css
/* Recommended easings */
--ease-out: cubic-bezier(0.33, 1, 0.68, 1);      /* Elements entering */
--ease-in:  cubic-bezier(0.32, 0, 0.67, 0);      /* Elements exiting */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);   /* State changes */
```

#### Common Patterns

```css
/* Hover state */
transition: background-color 150ms var(--ease-out);

/* Modal enter */
animation: fadeIn 200ms var(--ease-out);

/* Button press */
transform: scale(0.98);
transition: transform 100ms var(--ease-out);
```

#### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Component Patterns

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main Content (fluid)         │
│  - Navigation           │  ┌─────────────────────────┐  │
│  - Workspace switcher   │  │ Page Header             │  │
│  - User menu            │  │ - Title                 │  │
│                         │  │ - Actions               │  │
│                         │  ├─────────────────────────┤  │
│                         │  │ Content Area            │  │
│                         │  │ (max-width: 1280px)     │  │
│                         │  │ (centered)              │  │
│                         │  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Cards

- Background: `--background-subtle`
- Border: 1px `--background-accent`
- Border radius: 8px (rounded-lg)
- Padding: 16px or 24px
- No shadows in dark mode (use borders)

### Buttons

| Variant | Use Case |
|---------|----------|
| Primary | Main CTA, one per view |
| Secondary | Alternative actions |
| Ghost | Tertiary actions, icon buttons |
| Destructive | Delete, remove, cancel subscription |

```tsx
// Button sizes
sm: h-8 px-3 text-sm
md: h-10 px-4 text-sm (default)
lg: h-12 px-6 text-base
```

### Forms

- Labels above inputs (not inline)
- Visible focus states
- Inline validation (show errors below field)
- Helper text in `--foreground-subtle`
- Required fields marked with `*`

### Tables

- Use tabular numbers for numeric columns
- Align numbers to the right
- Sticky headers for long lists
- Zebra striping optional (can use hover instead)
- Row actions in last column or on hover

### Empty States

Every list/table needs an empty state:
- Illustration (optional, subtle)
- Clear message explaining the state
- Primary action to resolve

---

## Tech Stack

### Required

- **React 18+** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** components (built on Radix primitives)
- **cmdk** for command palette
- **Lucide React** for icons

### Configuration

```ts
// tailwind.config.ts
export default {
  darkMode: 'class', // or 'media'
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
        mono: ['Geist Mono', ...defaultTheme.fontFamily.mono],
      },
      // Use CSS variables for colors (shadcn pattern)
    },
  },
}
```

### File Structure

```
src/
├── components/
│   ├── ui/           # shadcn/ui components (Button, Input, etc.)
│   ├── layout/       # Sidebar, Header, PageContainer
│   ├── features/     # Feature-specific components
│   └── shared/       # Shared components (DataTable, EmptyState)
├── styles/
│   └── globals.css   # CSS variables, base styles
└── lib/
    └── utils.ts      # cn() helper, other utilities
```

---

## Anti-Patterns (What NOT to Do)

### Visual

- ❌ Gradients on buttons or cards
- ❌ Drop shadows in dark mode
- ❌ Multiple accent colors competing for attention
- ❌ Decorative icons that don't add meaning
- ❌ Stock photos or generic illustrations
- ❌ Rounded corners > 12px (except full pills)

### Layout

- ❌ Content wider than 1280px
- ❌ Sidebar wider than 280px
- ❌ Cards without consistent padding
- ❌ Inconsistent spacing between sections

### Typography

- ❌ More than 2 font families
- ❌ Font weights lighter than 400
- ❌ ALL CAPS for body text (headers sparingly)
- ❌ Justified text alignment
- ❌ Line lengths > 80 characters

### Interaction

- ❌ Hover-only actions (must be accessible)
- ❌ Auto-playing animations
- ❌ Transitions longer than 300ms
- ❌ Modals without focus trap
- ❌ Toast notifications without dismiss option

---

## Quality Checklist

Before any UI component is considered complete:

### Visual

- [ ] Follows spacing scale (4px increments)
- [ ] Uses only defined colors from palette
- [ ] Typography matches type scale
- [ ] Dark mode is default and complete
- [ ] Light mode works if implemented

### Accessibility

- [ ] Keyboard navigable
- [ ] Focus states visible
- [ ] Contrast ratios pass WCAG AA
- [ ] Screen reader tested

### Responsiveness

- [ ] Works on mobile (320px+)
- [ ] Works on tablet (768px+)
- [ ] Works on desktop (1024px+)
- [ ] No horizontal scroll

### Polish

- [ ] Loading states defined
- [ ] Empty states defined
- [ ] Error states defined
- [ ] Hover/active states implemented
- [ ] Animations respect reduced motion

---

## References & Inspiration

### Design Systems

- [Vercel Geist](https://vercel.com/geist) - Color, typography, components
- [Linear UI](https://linear.app) - Dark mode excellence, keyboard-first
- [Stripe Dashboard](https://dashboard.stripe.com) - Data-heavy UI done right
- [shadcn/ui](https://ui.shadcn.com) - Component patterns, accessibility

### Resources

- [Vercel Web Interface Guidelines](https://vercel.com/design/guidelines)
- [Radix Primitives](https://radix-ui.com) - Accessible component primitives
- [Tailwind CSS](https://tailwindcss.com/docs) - Utility classes reference

---

*Last updated: 2025-01-30*
