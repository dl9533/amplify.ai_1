/**
 * Mock implementations for discovery API services.
 * These mocks provide default responses for tests.
 */
import { vi } from 'vitest'

// Mock chat API responses
export const mockChatApi = {
  sendMessage: vi.fn().mockResolvedValue({
    response: 'Hello! How can I help you today?',
    quick_actions: [],
  }),
  getHistory: vi.fn().mockResolvedValue([]),
  executeAction: vi.fn().mockResolvedValue({ response: 'Action executed' }),
}

// Mock sessions API responses
export const mockSessionsApi = {
  list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, per_page: 20 }),
  get: vi.fn().mockResolvedValue({
    id: 'session-1',
    status: 'draft',
    current_step: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),
  create: vi.fn().mockResolvedValue({
    id: 'new-session',
    status: 'draft',
    current_step: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),
  delete: vi.fn().mockResolvedValue(undefined),
  updateStep: vi.fn().mockResolvedValue({
    id: 'session-1',
    status: 'in_progress',
    current_step: 2,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }),
}

// Mock activities API responses
export const mockActivitiesApi = {
  getBySession: vi.fn().mockResolvedValue([
    {
      gwa_code: 'GWA-001',
      gwa_title: 'Analyzing Data',
      ai_exposure_score: 0.72,
      dwas: [
        {
          id: 'dwa-001',
          code: 'DWA-001',
          title: 'Analyze business data',
          description: 'Analyze business data to identify trends',
          selected: false,
          gwa_code: 'GWA-001',
        },
        {
          id: 'dwa-002',
          code: 'DWA-002',
          title: 'Create data visualizations',
          description: 'Create charts and graphs',
          selected: false,
          gwa_code: 'GWA-001',
        },
      ],
    },
    {
      gwa_code: 'GWA-002',
      gwa_title: 'Communicating',
      ai_exposure_score: 0.45,
      dwas: [
        {
          id: 'dwa-003',
          code: 'DWA-003',
          title: 'Write reports',
          description: 'Write business reports',
          selected: false,
          gwa_code: 'GWA-002',
        },
      ],
    },
  ]),
  updateSelection: vi.fn().mockResolvedValue({
    id: 'dwa-001',
    selected: true,
  }),
  bulkSelect: vi.fn().mockResolvedValue({ updated_count: 2 }),
  getSelectionCount: vi.fn().mockResolvedValue({
    total: 3,
    selected: 0,
    unselected: 3,
    gwas_with_selections: 0,
  }),
}

// Mock analysis API responses
export const mockAnalysisApi = {
  trigger: vi.fn().mockResolvedValue({ status: 'completed' }),
  getByDimension: vi.fn().mockResolvedValue({
    dimension: 'ROLE',
    results: [
      {
        id: 'result-1',
        name: 'Software Engineer',
        ai_exposure_score: 0.85,
        impact_score: 0.72,
        complexity_score: 0.3,
        priority_score: 0.78,
        priority_tier: 'HIGH',
      },
      {
        id: 'result-2',
        name: 'Data Analyst',
        ai_exposure_score: 0.9,
        impact_score: 0.65,
        complexity_score: 0.25,
        priority_score: 0.75,
        priority_tier: 'HIGH',
      },
      {
        id: 'result-3',
        name: 'Customer Service Rep',
        ai_exposure_score: 0.6,
        impact_score: 0.45,
        complexity_score: 0.4,
        priority_score: 0.52,
        priority_tier: 'MEDIUM',
      },
    ],
  }),
  getAllDimensions: vi.fn().mockResolvedValue({
    ROLE: { count: 3, avg_exposure: 0.78 },
    DEPARTMENT: { count: 2, avg_exposure: 0.72 },
    GEOGRAPHY: { count: 2, avg_exposure: 0.7 },
  }),
}

// Mock role mappings API responses
export const mockRoleMappingsApi = {
  getBySession: vi.fn().mockResolvedValue([
    {
      id: 'mapping-1',
      source_role: 'Software Developer',
      onet_code: '15-1252.00',
      onet_title: 'Software Developers',
      confidence_score: 0.92,
      is_confirmed: false,
    },
    {
      id: 'mapping-2',
      source_role: 'Data Scientist',
      onet_code: '15-2051.00',
      onet_title: 'Data Scientists',
      confidence_score: 0.88,
      is_confirmed: true,
    },
  ]),
  update: vi.fn().mockResolvedValue({
    id: 'mapping-1',
    source_role: 'Software Developer',
    onet_code: '15-1252.00',
    onet_title: 'Software Developers',
    confidence_score: 0.92,
    is_confirmed: true,
  }),
  bulkConfirm: vi.fn().mockResolvedValue({ confirmed_count: 2 }),
}

// Mock roadmap API responses
export const mockRoadmapApi = {
  get: vi.fn().mockResolvedValue({
    items: [
      {
        id: 'roadmap-1',
        role_name: 'Software Engineer',
        priority_score: 0.85,
        priority_tier: 'HIGH',
        phase: 'NOW',
        estimated_effort: 'medium',
        order: 1,
      },
      {
        id: 'roadmap-2',
        role_name: 'Data Analyst',
        priority_score: 0.72,
        priority_tier: 'HIGH',
        phase: 'NEXT',
        estimated_effort: 'low',
        order: 2,
      },
    ],
  }),
  updatePhase: vi.fn().mockResolvedValue({
    id: 'roadmap-1',
    phase: 'NEXT',
  }),
  reorder: vi.fn().mockResolvedValue({ success: true }),
  bulkUpdate: vi.fn().mockResolvedValue({ updated_count: 2 }),
}

// Mock O*NET API responses
export const mockOnetApi = {
  search: vi.fn().mockResolvedValue([
    { code: '15-1252.00', title: 'Software Developers', score: 0.95 },
    { code: '15-1251.00', title: 'Computer Programmers', score: 0.85 },
  ]),
  getOccupation: vi.fn().mockResolvedValue({
    code: '15-1252.00',
    title: 'Software Developers',
    description: 'Develop, create, and modify computer applications software.',
  }),
}

// Mock upload API responses
export const mockUploadApi = {
  upload: vi.fn().mockResolvedValue({
    upload_id: 'upload-123',
    filename: 'workforce.csv',
    row_count: 150,
    detected_schema: ['Role', 'Department', 'Location', 'Headcount'],
    column_types: {
      Role: 'string',
      Department: 'string',
      Location: 'string',
      Headcount: 'number',
    },
  }),
  confirmMappings: vi.fn().mockResolvedValue({
    status: 'processed',
    roles_extracted: 25,
  }),
}

// Mock handoff API responses
export const mockHandoffApi = {
  submit: vi.fn().mockResolvedValue({
    intake_request_id: 'intake-123',
    status: 'submitted',
    candidates_count: 5,
  }),
  validate: vi.fn().mockResolvedValue({
    is_ready: true,
    warnings: [],
    errors: [],
  }),
  getStatus: vi.fn().mockResolvedValue({
    session_id: 'session-1',
    handed_off: false,
  }),
}

// Reset all mocks helper
export function resetAllMocks() {
  Object.values(mockChatApi).forEach((fn) => fn.mockClear())
  Object.values(mockSessionsApi).forEach((fn) => fn.mockClear())
  Object.values(mockActivitiesApi).forEach((fn) => fn.mockClear())
  Object.values(mockAnalysisApi).forEach((fn) => fn.mockClear())
  Object.values(mockRoleMappingsApi).forEach((fn) => fn.mockClear())
  Object.values(mockRoadmapApi).forEach((fn) => fn.mockClear())
  Object.values(mockOnetApi).forEach((fn) => fn.mockClear())
  Object.values(mockUploadApi).forEach((fn) => fn.mockClear())
  Object.values(mockHandoffApi).forEach((fn) => fn.mockClear())
}
