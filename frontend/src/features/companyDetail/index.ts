/**
 * CompanyDetail Feature - Public API
 *
 * このファイル経由でのみ feature 外からアクセスすること。
 */

// Components
export { CompanyDetailPage } from './components/CompanyDetailPage'

// Hooks
export { useCompanyDetail, useGenerateReport, useFileStatus } from './hooks'

// Types
export type {
  CompanyDetail,
  ScoreBreakdownDetail,
  QualitativeSignalDetail,
  FinancialDataDetail,
  ReportGenerateResponse,
  FileStatusResponse,
} from './types'
