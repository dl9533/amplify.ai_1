import React from 'react'

export interface DiscoveryLayoutProps {
  children: React.ReactNode
  currentStep?: number
  totalSteps?: number
  sessionTitle?: string
}

export function DiscoveryLayout({
  children,
  currentStep = 1,
  totalSteps = 1,
  sessionTitle,
}: DiscoveryLayoutProps): React.ReactElement {
  return (
    <div className="grid grid-cols-[1fr_320px] min-h-screen bg-background">
      {/* Main Content Area */}
      <div className="flex flex-col">
        {/* Header with optional session title */}
        {sessionTitle && (
          <header className="border-b border-border px-6 py-4">
            <h1 className="text-xl font-semibold text-foreground">{sessionTitle}</h1>
          </header>
        )}

        {/* Main content */}
        <main className="flex-1 p-6 max-w-content mx-auto w-full">{children}</main>
      </div>

      {/* Sidebar */}
      <aside className="border-l border-border bg-background-subtle flex flex-col">
        {/* Step Indicator */}
        <nav
          role="navigation"
          aria-label="Discovery steps"
          className="border-b border-border px-4 py-4"
        >
          <div className="text-sm text-foreground-muted">
            <span className="font-medium text-foreground">Step {currentStep}</span>
            <span> of {totalSteps}</span>
          </div>
          <div className="mt-2">
            <div className="flex gap-1">
              {Array.from({ length: totalSteps }, (_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-colors duration-150 ${
                    i < currentStep ? 'bg-primary' : 'bg-background-accent'
                  }`}
                />
              ))}
            </div>
          </div>
        </nav>

        {/* Chat Panel */}
        <section
          role="complementary"
          aria-label="Discovery chat"
          className="flex-1 flex flex-col p-4"
        >
          <div className="text-sm font-medium text-foreground-muted mb-2">Chat</div>
          <div className="flex-1 bg-background-muted rounded-lg border border-border p-3">
            <p className="text-sm text-foreground-subtle">
              Ask questions or get help with your discovery session.
            </p>
          </div>
        </section>
      </aside>
    </div>
  )
}
