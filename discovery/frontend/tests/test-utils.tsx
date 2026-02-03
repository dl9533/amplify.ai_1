/**
 * Test utilities for rendering components with required providers.
 */
import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '@/stores/auth'

interface WrapperOptions {
  route?: string
  routePath?: string
}

interface AllTheProvidersProps {
  children: ReactNode
}

// Default wrapper with all providers
function AllTheProviders({ children }: AllTheProvidersProps): JSX.Element {
  return <AuthProvider>{children}</AuthProvider>
}

// Wrapper with router
function createRouterWrapper(route: string, routePath: string) {
  return function RouterWrapper({ children }: AllTheProvidersProps): JSX.Element {
    return (
      <AuthProvider>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            <Route path={routePath} element={children} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    )
  }
}

// Custom render function
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & WrapperOptions
) {
  const { route, routePath, ...renderOptions } = options || {}

  const Wrapper =
    route && routePath
      ? createRouterWrapper(route, routePath)
      : AllTheProviders

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Render with router helper
export function renderWithRouter(
  ui: ReactElement,
  { route, routePath }: { route: string; routePath: string }
) {
  return customRender(ui, { route, routePath })
}

// Export everything from testing-library
export * from '@testing-library/react'
export { customRender as render }
