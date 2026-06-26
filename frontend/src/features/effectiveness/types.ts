/**
 * Effectiveness feature - Types
 */
import type {
  EffectivenessResponse,
  KpiSnapshotSchema,
  WorkLogSchema,
  WorkLogCreateRequest,
  WorkLogListResponse,
} from '@/shared/api/generated/propertySaleScreeningAPI'

export type {
  EffectivenessResponse,
  KpiSnapshotSchema,
  WorkLogSchema,
  WorkLogCreateRequest,
  WorkLogListResponse,
}

export type TaskType = 'primary_screening' | 'deep_dive' | 'report' | 'other'

export interface PeriodRange {
  periodFrom?: string
  periodTo?: string
}

export interface WorkLogRange {
  from?: string
  to?: string
}
