/**
 * Discovery module API functions.
 * Typed API functions for all Discovery endpoints.
 */
import { api, ApiError } from './api'

export { ApiError }

// ============ Common Types ============

export type SessionStatus = 'draft' | 'in_progress' | 'completed'
export type PriorityTier = 'HIGH' | 'MEDIUM' | 'LOW'
export type AnalysisDimension = 'ROLE' | 'DEPARTMENT' | 'GEOGRAPHY' | 'TASK' | 'LOB'
export type RoadmapPhase = 'NOW' | 'NEXT' | 'LATER'
export type EstimatedEffort = 'low' | 'medium' | 'high'

// ============ Upload API ============

export interface UploadResponse {
  upload_id: string
  filename: string
  row_count: number
  detected_schema: string[]
  column_types: Record<string, string>
}

export interface ColumnMapping {
  source_column: string
  target_field: string
}

export interface ConfirmUploadResponse {
  status: string
  roles_extracted: number
}

export const uploadApi = {
  /**
   * Upload a workforce data file.
   */
  upload: async (
    sessionId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100)
          onProgress(progress)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch {
            reject(new Error('Invalid response from server'))
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText)
            reject(new Error(errorData.detail || 'Upload failed'))
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`))
          }
        }
      })

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'))
      })

      const baseUrl = import.meta.env.VITE_API_URL || ''
      xhr.open('POST', `${baseUrl}/discovery/sessions/${sessionId}/upload`)
      xhr.send(formData)
    })
  },

  /**
   * Confirm column mappings and process the upload.
   */
  confirmMappings: (
    sessionId: string,
    uploadId: string,
    mappings: ColumnMapping[]
  ): Promise<ConfirmUploadResponse> =>
    api.post(`/discovery/sessions/${sessionId}/upload/${uploadId}/confirm`, { mappings }),
}

// ============ Sessions API ============

export interface SessionResponse {
  id: string
  status: SessionStatus
  current_step: number
  created_at: string
  updated_at: string
}

export interface SessionListResponse {
  items: SessionResponse[]
  total: number
  page: number
  per_page: number
}

export const sessionsApi = {
  /**
   * List discovery sessions with pagination.
   */
  list: (page = 1, perPage = 20): Promise<SessionListResponse> =>
    api.get(`/discovery/sessions?page=${page}&per_page=${perPage}`),

  /**
   * Get a single discovery session by ID.
   */
  get: (sessionId: string): Promise<SessionResponse> =>
    api.get(`/discovery/sessions/${sessionId}`),

  /**
   * Create a new discovery session.
   */
  create: (organizationId: string): Promise<SessionResponse> =>
    api.post('/discovery/sessions', { organization_id: organizationId }),

  /**
   * Delete a discovery session.
   */
  delete: (sessionId: string): Promise<void> =>
    api.delete(`/discovery/sessions/${sessionId}`),

  /**
   * Update the current step of a session.
   */
  updateStep: (sessionId: string, step: number): Promise<SessionResponse> =>
    api.patch(`/discovery/sessions/${sessionId}/step`, { step }),
}

// ============ Chat API ============

export interface ChatMessage {
  message: string
}

export interface QuickAction {
  label: string
  action: string
}

export interface ChatResponse {
  response: string
  quick_actions: QuickAction[]
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export const chatApi = {
  /**
   * Send a message to the discovery orchestrator.
   */
  sendMessage: (sessionId: string, message: string): Promise<ChatResponse> =>
    api.post(`/discovery/sessions/${sessionId}/chat`, { message }),

  /**
   * Get chat history for a session.
   */
  getHistory: (sessionId: string): Promise<ChatHistoryItem[]> =>
    api.get(`/discovery/sessions/${sessionId}/chat`),

  /**
   * Execute a quick action.
   */
  executeAction: (
    sessionId: string,
    action: string,
    params?: Record<string, unknown>
  ): Promise<{ response: string; data?: Record<string, unknown> }> =>
    api.post(`/discovery/sessions/${sessionId}/chat/action`, { action, params }),
}

// ============ Role Mappings API ============

export type ConfidenceTier = 'HIGH' | 'MEDIUM' | 'LOW'

export interface RoleMappingResponse {
  id: string
  source_role: string
  onet_code: string | null
  onet_title: string | null
  confidence_score: number
  confidence_tier?: ConfidenceTier
  reasoning?: string
  is_confirmed: boolean
  row_count?: number
}

export interface RoleMappingUpdate {
  onet_code?: string
  onet_title?: string
  is_confirmed?: boolean
}

export interface BulkConfirmResponse {
  confirmed_count: number
}

export interface BulkRemapRequest {
  threshold?: number
  mapping_ids?: string[]
}

export interface RoleMappingWithReasoning {
  id: string
  source_role: string
  onet_code: string | null
  onet_title: string | null
  confidence_score: number
  confidence_tier: ConfidenceTier
  reasoning: string | null
  is_confirmed: boolean
}

export interface BulkRemapResponse {
  remapped_count: number
  mappings: RoleMappingWithReasoning[]
}

// Grouped role mappings types
export interface GroupedMappingSummary {
  total_roles: number
  confirmed_count: number
  pending_count: number
  low_confidence_count: number
  total_employees: number
}

export interface RoleMappingCompact {
  id: string
  source_role: string
  onet_code: string | null
  onet_title: string | null
  confidence_score: number
  is_confirmed: boolean
  employee_count: number
}

export interface LobGroup {
  lob: string
  summary: GroupedMappingSummary
  mappings: RoleMappingCompact[]
}

export interface GroupedRoleMappingsResponse {
  session_id: string
  overall_summary: GroupedMappingSummary
  lob_groups: LobGroup[]
  ungrouped_mappings: RoleMappingCompact[]
}

export interface BulkConfirmRequest {
  threshold?: number
  lob?: string
  mapping_ids?: string[]
}

// LOB mapping lookup types
export interface LobNaicsLookupResponse {
  lob: string
  naics_codes: string[]
  confidence: number
  source: 'curated' | 'fuzzy' | 'llm' | 'none'
}

export const roleMappingsApi = {
  /**
   * Get all role mappings for a session.
   */
  getBySession: (sessionId: string): Promise<RoleMappingResponse[]> =>
    api.get(`/discovery/sessions/${sessionId}/role-mappings`),

  /**
   * Update a role mapping.
   */
  update: (mappingId: string, data: RoleMappingUpdate): Promise<RoleMappingResponse> =>
    api.put(`/discovery/role-mappings/${mappingId}`, data),

  /**
   * Bulk confirm mappings above a confidence threshold.
   * Optionally filter by LOB or specific mapping IDs.
   * @param threshold - Confidence threshold (0-1), defaults to 0.85
   * @param lob - Optional LOB filter
   * @param mappingIds - Optional specific mapping IDs
   */
  bulkConfirm: (
    sessionId: string,
    threshold?: number,
    lob?: string,
    mappingIds?: string[]
  ): Promise<BulkConfirmResponse> =>
    api.post(`/discovery/sessions/${sessionId}/role-mappings/confirm`, {
      threshold: threshold ?? 0.85,
      lob,
      mapping_ids: mappingIds,
    }),

  /**
   * Get role mappings grouped by LOB.
   */
  getGroupedBySession: (sessionId: string): Promise<GroupedRoleMappingsResponse> =>
    api.get(`/discovery/sessions/${sessionId}/role-mappings/grouped`),

  /**
   * Bulk remap low-confidence roles using LLM.
   * @param threshold - Maximum confidence threshold (roles at or below will be re-mapped)
   * @param mappingIds - Optional specific mapping IDs to re-map
   */
  bulkRemap: (
    sessionId: string,
    threshold?: number,
    mappingIds?: string[]
  ): Promise<BulkRemapResponse> =>
    api.post(`/discovery/sessions/${sessionId}/role-mappings/remap`, {
      threshold: threshold ?? 0.6,
      mapping_ids: mappingIds,
    }),
}

// ============ O*NET API ============

export interface OnetSearchResult {
  code: string
  title: string
  score: number
}

export interface OnetOccupation {
  code: string
  title: string
  description?: string
  gwas?: string[]
}

export const onetApi = {
  /**
   * Search O*NET occupations.
   */
  search: async (query: string): Promise<OnetSearchResult[]> => {
    const response = await api.get<{ results: OnetSearchResult[] }>(
      `/api/v1/discovery/onet/search?query=${encodeURIComponent(query)}`
    )
    return response.results
  },

  /**
   * Get occupation details by O*NET code.
   */
  getOccupation: (code: string): Promise<OnetOccupation> =>
    api.get(`/api/v1/discovery/onet/${encodeURIComponent(code)}`),
}

// ============ LOB Mapping API ============

export const lobMappingApi = {
  /**
   * Lookup NAICS codes for a Line of Business.
   */
  lookup: (lob: string): Promise<LobNaicsLookupResponse> =>
    api.get(`/discovery/lob/lookup?lob=${encodeURIComponent(lob)}`),
}

// ============ Activities API ============

export interface DWAResponse {
  id: string
  code: string
  title: string
  description?: string
  selected: boolean
  gwa_code: string
}

export interface GWAGroupResponse {
  gwa_code: string
  gwa_title: string
  dwas: DWAResponse[]
  ai_exposure_score?: number
}

export interface SelectionCountResponse {
  total: number
  selected: number
  unselected: number
  gwas_with_selections: number
}

export interface BulkSelectionResponse {
  updated_count: number
}

export const activitiesApi = {
  /**
   * Get activities grouped by GWA for a session.
   */
  getBySession: (sessionId: string, includeUnselected = true): Promise<GWAGroupResponse[]> =>
    api.get(
      `/discovery/sessions/${sessionId}/activities?include_unselected=${includeUnselected}`
    ),

  /**
   * Update selection status of a single activity.
   */
  updateSelection: (activityId: string, selected: boolean): Promise<DWAResponse> =>
    api.put(`/discovery/activities/${activityId}`, { selected }),

  /**
   * Bulk select/deselect activities.
   */
  bulkSelect: (
    sessionId: string,
    activityIds: string[],
    selected: boolean
  ): Promise<BulkSelectionResponse> =>
    api.post(`/discovery/sessions/${sessionId}/activities/select`, {
      activity_ids: activityIds,
      selected,
    }),

  /**
   * Get selection count statistics.
   */
  getSelectionCount: (sessionId: string): Promise<SelectionCountResponse> =>
    api.get(`/discovery/sessions/${sessionId}/activities/count`),
}

// ============ Analysis API ============

export interface AnalysisResult {
  id: string
  name: string
  ai_exposure_score: number
  impact_score: number
  complexity_score: number
  priority_score: number
  priority_tier: PriorityTier
}

export interface DimensionAnalysisResponse {
  dimension: AnalysisDimension
  results: AnalysisResult[]
}

export interface DimensionSummary {
  count: number
  avg_exposure: number
}

export type AllDimensionsResponse = Record<string, DimensionSummary>

export interface TriggerAnalysisResponse {
  status: string
}

export const analysisApi = {
  /**
   * Trigger scoring analysis for a session.
   */
  trigger: (sessionId: string): Promise<TriggerAnalysisResponse> =>
    api.post(`/discovery/sessions/${sessionId}/analyze`),

  /**
   * Get analysis results for a specific dimension.
   */
  getByDimension: (
    sessionId: string,
    dimension: AnalysisDimension,
    priorityTier?: PriorityTier
  ): Promise<DimensionAnalysisResponse> => {
    let url = `/discovery/sessions/${sessionId}/analysis/${dimension}`
    if (priorityTier) {
      url += `?priority_tier=${priorityTier}`
    }
    return api.get(url)
  },

  /**
   * Get summary of all dimensions.
   */
  getAllDimensions: (sessionId: string): Promise<AllDimensionsResponse> =>
    api.get(`/discovery/sessions/${sessionId}/analysis`),
}

// ============ Roadmap API ============

export interface RoadmapItem {
  id: string
  role_name: string
  priority_score: number
  priority_tier: string
  phase: RoadmapPhase
  estimated_effort: EstimatedEffort
  order?: number
}

export interface RoadmapItemsResponse {
  items: RoadmapItem[]
}

export interface BulkPhaseUpdate {
  item_id: string
  phase: RoadmapPhase
}

export interface BulkUpdateResponse {
  updated_count: number
}

export const roadmapApi = {
  /**
   * Get roadmap items for a session.
   */
  get: (sessionId: string, phase?: RoadmapPhase): Promise<RoadmapItemsResponse> => {
    let url = `/discovery/sessions/${sessionId}/roadmap`
    if (phase) {
      url += `?phase=${phase}`
    }
    return api.get(url)
  },

  /**
   * Update a roadmap item's phase.
   */
  updatePhase: (itemId: string, phase: RoadmapPhase): Promise<RoadmapItem> =>
    api.put(`/discovery/roadmap/${itemId}`, { phase }),

  /**
   * Reorder roadmap items.
   */
  reorder: (sessionId: string, itemIds: string[]): Promise<{ success: boolean }> =>
    api.post(`/discovery/sessions/${sessionId}/roadmap/reorder`, { item_ids: itemIds }),

  /**
   * Bulk update phases for multiple items.
   */
  bulkUpdate: (sessionId: string, updates: BulkPhaseUpdate[]): Promise<BulkUpdateResponse> =>
    api.post(`/discovery/sessions/${sessionId}/roadmap/bulk-update`, { updates }),
}

// ============ Handoff API ============

export interface HandoffRequest {
  candidate_ids?: string[]
  notes?: string
}

export interface HandoffResponse {
  intake_request_id: string
  status: string
  candidates_count: number
}

export interface ValidationResult {
  is_ready: boolean
  warnings: string[]
  errors: string[]
}

export interface HandoffStatus {
  session_id: string
  handed_off: boolean
  intake_request_id?: string
  handed_off_at?: string
}

// ============ Admin API ============

export interface OnetSyncRequest {
  version?: string // e.g., "30_1" for v30.1
}

export interface OnetSyncResponse {
  version: string
  occupation_count: number
  alternate_title_count: number
  task_count: number
  status: string
}

export interface OnetSyncStatus {
  synced: boolean
  version: string | null
  synced_at: string | null
  occupation_count: number
}

export const adminApi = {
  /**
   * Trigger O*NET database sync.
   */
  syncOnet: (version?: string): Promise<OnetSyncResponse> =>
    api.post('/discovery/admin/onet/sync', { version: version || '30_1' }),

  /**
   * Get O*NET sync status.
   */
  getOnetStatus: (): Promise<OnetSyncStatus> =>
    api.get('/discovery/admin/onet/status'),
}

// ============ Handoff API ============

export const handoffApi = {
  /**
   * Submit candidates to intake system.
   */
  submit: (
    sessionId: string,
    candidateIds?: string[],
    notes?: string
  ): Promise<HandoffResponse> =>
    api.post(`/discovery/sessions/${sessionId}/handoff`, {
      candidate_ids: candidateIds,
      notes,
    }),

  /**
   * Validate handoff readiness.
   */
  validate: (sessionId: string): Promise<ValidationResult> =>
    api.post(`/discovery/sessions/${sessionId}/handoff/validate`),

  /**
   * Get current handoff status.
   */
  getStatus: (sessionId: string): Promise<HandoffStatus> =>
    api.get(`/discovery/sessions/${sessionId}/handoff`),
}
