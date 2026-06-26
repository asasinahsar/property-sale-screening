/**
 * CompanyDetail feature - Types
 *
 * バックエンドの Pydantic スキーマ（CompanyDetailSchema / ReportGenerateResponse /
 * FileStatusResponse）に対応する TypeScript 型定義。
 */

export type DocumentType =
  | 'yuho'
  | 'mid_term_plan'
  | 'timely_disclosure'
  | 'large_shareholding'

export type SignalType =
  | 'activist_proposal'
  | 'capital_efficiency_target'
  | 'sale_suggestion'
  | 'other'

export type SignalStance = 'support' | 'counter'

export type ConfidenceLevel = 'high' | 'mid' | 'low'

export type FileStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface DocumentSummary {
  document_id: string
  document_type: DocumentType
  disclosed_at: string // ISO date
  source_url: string
}

export interface QualitativeSignalDetail {
  signal_id: string
  signal_type: SignalType
  stance: SignalStance
  strength: number | null
  quote_text: string
  source_page: number
  document: DocumentSummary
}

export interface FinancialDataDetail {
  as_of_date: string
  revenue: number | null
  pbr: number | null
  adjusted_pbr: number | null
  equity_ratio: number | null
  re_market_value: number | null
  re_book_value: number | null
  unrealized_gain: number | null
  unrealized_gain_ratio: number | null
  roic: number | null
  wacc: number | null
  stock_price: number | null
  roic_wacc_gap: number | null
}

export interface ScoreBreakdownDetail {
  structure_score: number
  event_score: number
  total_score: number
  event_boost: number | null
  confidence: ConfidenceLevel
  ai_judgment: string | null
  judgment_refs: Record<string, unknown> | null
  score_breakdown: Record<string, unknown> | null
}

export interface CompanyDetail {
  company_id: string
  securities_code: string
  name: string
  industry: string
  market_cap: number | null
  scoring: ScoreBreakdownDetail | null
  financial: FinancialDataDetail | null
  signals_support: QualitativeSignalDetail[]
  signals_counter: QualitativeSignalDetail[]
}

export interface ReportGenerateRequest {
  format: 'pdf'
}

export interface ReportGenerateResponse {
  file_id: string
  status: FileStatus
  download_url: string | null
  created_at: string
}

export interface FileStatusResponse {
  file_id: string
  status: FileStatus
  download_url: string | null
  format: string
  created_at: string
}
