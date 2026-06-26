/**
 * Longlist feature - Types
 *
 * orval 生成スキーマを re-export し、feature 内で利用する型を集約する。
 */
export type {
  LonglistItemSchema,
  LonglistListResponse,
  LonglistCreateRequest,
  LonglistUpdateRequest,
  LonglistApprovalRequest,
  LonglistExportResponse,
} from '@/shared/api/generated/propertySaleScreeningAPI'

export type LonglistStatus = 'candidate' | 'approved' | 'rejected'
export type ApprovalAction = 'approve' | 'reject'
