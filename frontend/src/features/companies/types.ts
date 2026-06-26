/**
 * Companies feature - Types
 */

export type SortBy = 'total_score' | 'structure_score' | 'event_score'

export type ConfidenceLevel = 'high' | 'mid' | 'low'

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
  company_id: string
  name: string
  securities_code: string
  industry: string
  market_cap: number | null
  total_score: number
  structure_score: number
  event_score: number
  event_boost: number | null
  unrealized_gain: number | null
  confidence: ConfidenceLevel
  has_event: boolean
}

export interface CompanyListResponse {
  items: CompanyRankingItemSchema[]
  total: number
  page: number
  page_size: number
}

export interface SearchConditionSchema {
  unrealized_gain_min: number | null
  unrealized_gain_max: number | null
  region: string | null
  industry: string | null
  pbr_max: number | null
  pbr_min: number | null
  structure_score_min: number | null
  company_name: string | null
  securities_code: string | null
}

export interface CompanySearchResponse {
  items: CompanyRankingItemSchema[]
  total: number
  page: number
  page_size: number
  search_summary: string | null
  extracted_filters: SearchConditionSchema | null
}

/** SearchBox からの検索条件（companies API への検索パラメータ） */
export interface CompanySearchParams {
  q?: string
  companyName?: string
  securitiesCode?: string
  sortBy?: SortBy
  page?: number
  pageSize?: number
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
