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
    <div className="grid grid-cols-[1fr_320px] min-h-screen">
      {/* Main Content Area */}
      <div className="flex flex-col">
        {/* Header with optional session title */}
        {sessionTitle && (
          <header className="border-b border-gray-200 px-6 py-4">
            <h1 className="text-xl font-semibold text-gray-900">{sessionTitle}</h1>
          </header>
        )}

        {/* Main content */}
        <main className="flex-1 p-6">{children}</main>
      </div>

      {/* Sidebar */}
      <aside className="border-l border-gray-200 bg-gray-50 flex flex-col">
        {/* Step Indicator */}
        <nav
          role="navigation"
          aria-label="Discovery steps"
          className="border-b border-gray-200 px-4 py-4"
        >
          <div className="text-sm text-gray-600">
            <span className="font-medium text-gray-900">Step {currentStep}</span>
            <span> of {totalSteps}</span>
          </div>
          <div className="mt-2">
            <div className="flex gap-1">
              {Array.from({ length: totalSteps }, (_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full ${
                    i < currentStep ? 'bg-blue-600' : 'bg-gray-300'
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
          <div className="text-sm font-medium text-gray-700 mb-2">Chat</div>
          <div className="flex-1 bg-white rounded-lg border border-gray-200 p-3">
            <p className="text-sm text-gray-500">
              Ask questions or get help with your discovery session.
            </p>
          </div>
        </section>
      </aside>
    </div>
  )
}
