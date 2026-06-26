/**
 * Effectiveness feature - Data Access Layer
 *
 * 効果検証 KPI / 工数ログ API の fetch wrapper（Cookie 認証）。
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query'

import type {
  EffectivenessResponse,
  WorkLogListResponse,
  WorkLogSchema,
  WorkLogCreateRequest,
  PeriodRange,
  WorkLogRange,
} from './types'

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const withCredentials: RequestInit = { credentials: 'include' }

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const effectivenessKeys = {
  all: ['effectiveness'] as const,
  effectiveness: (range?: PeriodRange) =>
    [...effectivenessKeys.all, 'kpi', range] as const,
  workLogs: (range?: WorkLogRange) =>
    [...effectivenessKeys.all, 'work-logs', range] as const,
}

// ---------------------------------------------------------------------------
// Fetch functions
// ---------------------------------------------------------------------------

export async function fetchEffectiveness(
  range?: PeriodRange,
): Promise<EffectivenessResponse> {
  const params = new URLSearchParams()
  if (range?.periodFrom) params.set('period_from', range.periodFrom)
  if (range?.periodTo) params.set('period_to', range.periodTo)
  const qs = params.toString()
  const res = await fetch(
    `${baseURL}/api/v1/kpi/effectiveness${qs ? `?${qs}` : ''}`,
    withCredentials,
  )
  if (!res.ok) throw new Error(`fetchEffectiveness failed: ${res.status}`)
  return res.json() as Promise<EffectivenessResponse>
}

export async function fetchWorkLogs(
  range?: WorkLogRange,
): Promise<WorkLogListResponse> {
  const params = new URLSearchParams()
  if (range?.from) params.set('from', range.from)
  if (range?.to) params.set('to', range.to)
  const qs = params.toString()
  const res = await fetch(
    `${baseURL}/api/v1/kpi/work-logs${qs ? `?${qs}` : ''}`,
    withCredentials,
  )
  if (!res.ok) throw new Error(`fetchWorkLogs failed: ${res.status}`)
  return res.json() as Promise<WorkLogListResponse>
}

export async function postWorkLog(
  body: WorkLogCreateRequest,
): Promise<WorkLogSchema> {
  const res = await fetch(`${baseURL}/api/v1/kpi/work-logs`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`postWorkLog failed: ${res.status}`)
  return res.json() as Promise<WorkLogSchema>
}

// ---------------------------------------------------------------------------
// Query / Mutation hooks (Data Access)
// ---------------------------------------------------------------------------

export function useEffectivenessQuery(
  range?: PeriodRange,
): UseQueryResult<EffectivenessResponse, Error> {
  return useQuery<EffectivenessResponse, Error>({
    queryKey: effectivenessKeys.effectiveness(range),
    queryFn: () => fetchEffectiveness(range),
  })
}

export function useWorkLogsQuery(
  range?: WorkLogRange,
): UseQueryResult<WorkLogListResponse, Error> {
  return useQuery<WorkLogListResponse, Error>({
    queryKey: effectivenessKeys.workLogs(range),
    queryFn: () => fetchWorkLogs(range),
  })
}

export function useAddWorkLogMutation(): UseMutationResult<
  WorkLogSchema,
  Error,
  WorkLogCreateRequest
> {
  const queryClient = useQueryClient()
  return useMutation<WorkLogSchema, Error, WorkLogCreateRequest>({
    mutationFn: (body) => postWorkLog(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: effectivenessKeys.all })
    },
  })
}
