/**
 * Base API client for the Discovery module.
 * Provides fetch wrapper with authentication and error handling.
 */
import { getStoredToken } from '../stores/auth'

export { getStoredToken }

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * Custom error class for API errors with status code and response data.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Process API response, throwing ApiError for non-2xx status codes.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let data: unknown
    try {
      data = await response.json()
    } catch {
      data = {}
    }

    const message =
      (data && typeof data === 'object' && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : null) || `Request failed with status ${response.status}`

    throw new ApiError(message, response.status, data)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

/**
 * Make an authenticated API request.
 *
 * @param path - API endpoint path (will be appended to base URL)
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Parsed JSON response
 * @throws ApiError on non-2xx response
 */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  return handleResponse<T>(response)
}

/**
 * Convenience methods for common HTTP verbs.
 */
export const api = {
  get: <T>(path: string) => apiRequest<T>(path, { method: 'GET' }),

  post: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown) =>
    apiRequest<T>(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string) => apiRequest<T>(path, { method: 'DELETE' }),
}
