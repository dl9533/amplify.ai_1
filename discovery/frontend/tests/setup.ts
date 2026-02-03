import '@testing-library/jest-dom'
import { vi, beforeEach, afterEach } from 'vitest'

// Mock scrollIntoView for jsdom (not implemented)
Element.prototype.scrollIntoView = vi.fn()
import {
  mockChatApi,
  mockSessionsApi,
  mockActivitiesApi,
  mockAnalysisApi,
  mockRoleMappingsApi,
  mockRoadmapApi,
  mockOnetApi,
  mockUploadApi,
  mockHandoffApi,
  resetAllMocks,
} from './__mocks__/services'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock crypto.randomUUID
Object.defineProperty(window, 'crypto', {
  value: {
    randomUUID: () => 'test-uuid-' + Math.random().toString(36).substr(2, 9),
  },
})

// Mock fetch for auth
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/auth/login')) {
    return Promise.resolve({
      ok: false,
      status: 404,
    })
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
})

// Mock the services module
vi.mock('@/services', () => ({
  chatApi: mockChatApi,
  sessionsApi: mockSessionsApi,
  activitiesApi: mockActivitiesApi,
  analysisApi: mockAnalysisApi,
  roleMappingsApi: mockRoleMappingsApi,
  roadmapApi: mockRoadmapApi,
  onetApi: mockOnetApi,
  uploadApi: mockUploadApi,
  handoffApi: mockHandoffApi,
  ApiError: class ApiError extends Error {
    constructor(message: string, public status?: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
  getStoredToken: vi.fn().mockReturnValue('mock-token'),
}))

// Also mock the discoveryApi module directly for imports that use it
vi.mock('@/services/discoveryApi', () => ({
  chatApi: mockChatApi,
  sessionsApi: mockSessionsApi,
  activitiesApi: mockActivitiesApi,
  analysisApi: mockAnalysisApi,
  roleMappingsApi: mockRoleMappingsApi,
  roadmapApi: mockRoadmapApi,
  onetApi: mockOnetApi,
  uploadApi: mockUploadApi,
  handoffApi: mockHandoffApi,
  ApiError: class ApiError extends Error {
    constructor(message: string, public status?: number) {
      super(message)
      this.name = 'ApiError'
    }
  },
}))

// Set up default auth state for tests
beforeEach(() => {
  resetAllMocks()
  localStorageMock.clear()

  // Set up mock authenticated user by default
  const mockAuthData = {
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
      name: 'Test User',
      organization: 'TestOrg',
    },
    token: 'mock-token',
  }
  localStorageMock.setItem('discovery_auth', JSON.stringify(mockAuthData))
})

afterEach(() => {
  vi.clearAllMocks()
})
