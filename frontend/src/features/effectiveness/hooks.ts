/**
 * Effectiveness feature - Business Logic Layer
 */

'use client'

import { useCallback } from 'react'

import {
  useEffectivenessQuery,
  useWorkLogsQuery,
  useAddWorkLogMutation,
} from './api'
import type {
  EffectivenessResponse,
  WorkLogListResponse,
  WorkLogCreateRequest,
  PeriodRange,
  WorkLogRange,
} from './types'

export interface UseEffectivenessResult {
  data: EffectivenessResponse | undefined
  isLoading: boolean
  error: Error | null
}

/** 効果検証 KPI（最新スナップショット + 推移）を取得 */
export function useEffectiveness(range?: PeriodRange): UseEffectivenessResult {
  const { data, isLoading, error } = useEffectivenessQuery(range)
  return { data, isLoading, error }
}

export interface UseWorkLogsResult {
  data: WorkLogListResponse | undefined
  isLoading: boolean
  error: Error | null
}

/** 工数ログ一覧を取得 */
export function useWorkLogs(range?: WorkLogRange): UseWorkLogsResult {
  const { data, isLoading, error } = useWorkLogsQuery(range)
  return { data, isLoading, error }
}

export interface UseAddWorkLogResult {
  addWorkLog: (body: WorkLogCreateRequest) => Promise<void>
  isPending: boolean
  error: Error | null
}

/** 工数ログを記録 */
export function useAddWorkLog(): UseAddWorkLogResult {
  const mutation = useAddWorkLogMutation()

  const addWorkLog = useCallback(
    async (body: WorkLogCreateRequest) => {
      await mutation.mutateAsync(body)
    },
    [mutation],
  )

  return {
    addWorkLog,
    isPending: mutation.isPending,
    error: mutation.error,
  }
}
