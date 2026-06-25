/**
 * Companies feature - Types
 */

export type SortBy = 'total_score' | 'structure_score' | 'event_score'

export type ConfidenceLevel = 'HIGH' | 'MID' | 'LOW'

export interface CompanyFilters {
  industry?: string
  minScore?: number
  maxScore?: number
  hasEvent?: boolean
  sortBy: SortBy
  page: number
  pageSize: number
}

export interface CompanyRankingItemSchema {
  id: string
  name: string
  securities_code: string
  industry: string
  total_score: number
  structure_score: number
  event_score: number
  unrealized_gain: number
  confidence: ConfidenceLevel
  has_event: boolean
  rank: number
}

export interface CompanyListResponse {
  items: CompanyRankingItemSchema[]
  total: number
  page: number
  page_size: number
}

export type ScreeningStatus = 'pending' | 'running' | 'success' | 'failed'

export interface ScreeningRunResponse {
  run_id: string
  status: ScreeningStatus
  progress: number
  created_at: string
  updated_at: string
}

export interface TriggerScreeningResponse {
  run_id: string
  status: ScreeningStatus
}
