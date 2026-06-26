/**
 * Companies feature - Data Access Layer
 *
 * Companies/Screenings API の fetch wrapper。
 * Slice 2 時点では orval 生成コードに該当エンドポイントが未追加のため、
 * 直接 fetch で実装する。
 */

import { useQuery, useMutation } from '@tanstack/react-query'
import type { UseQueryOptions } from '@tanstack/react-query'

import type {
  CompanyFilters,
  CompanyListResponse,
  CompanySearchParams,
  CompanySearchResponse,
  ScreeningRunResponse,
  TriggerScreeningResponse,
} from './types'

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const withCredentials: RequestInit = { credentials: 'include' }

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const companyKeys = {
  all: ['companies'] as const,
  list: (filters?: Partial<CompanyFilters>) =>
    [...companyKeys.all, 'list', filters] as const,
  search: (params?: CompanySearchParams) =>
    [...companyKeys.all, 'search', params] as const,
  screeningStatus: (runId: string) =>
    ['screenings', 'status', runId] as const,
}

// ---------------------------------------------------------------------------
// Search error（解釈失敗・LLM 失敗のコードを保持）
// ---------------------------------------------------------------------------

export class CompanySearchError extends Error {
  code?: string
  status: number

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'CompanySearchError'
    this.status = status
    this.code = code
  }
}

// ---------------------------------------------------------------------------
// Fetch functions
// ---------------------------------------------------------------------------

export async function fetchCompanies(
  filters: CompanyFilters,
): Promise<CompanyListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.pageSize))
  params.set('sort_by', filters.sortBy)
  if (filters.industry) params.set('industry', filters.industry)
  if (filters.minScore !== undefined)
    params.set('min_score', String(filters.minScore))
  if (filters.maxScore !== undefined)
    params.set('max_score', String(filters.maxScore))
  if (filters.hasEvent !== undefined)
    params.set('has_event', String(filters.hasEvent))

  const res = await fetch(
    `${baseURL}/api/v1/companies?${params.toString()}`,
    withCredentials,
  )
  if (!res.ok) throw new Error(`fetchCompanies failed: ${res.status}`)
  return res.json() as Promise<CompanyListResponse>
}

export async function searchCompanies(
  params: CompanySearchParams,
): Promise<CompanySearchResponse> {
  const search = new URLSearchParams()
  if (params.q) search.set('q', params.q)
  if (params.companyName) search.set('company_name', params.companyName)
  if (params.securitiesCode) search.set('securities_code', params.securitiesCode)
  search.set('sort_by', params.sortBy ?? 'total_score')
  search.set('page', String(params.page ?? 1))
  search.set('page_size', String(params.pageSize ?? 20))

  const res = await fetch(
    `${baseURL}/api/v1/companies?${search.toString()}`,
    withCredentials,
  )

  if (!res.ok) {
    let code: string | undefined
    let message = `searchCompanies failed: ${res.status}`
    try {
      const body = await res.json()
      const detail = body?.detail
      if (detail && typeof detail === 'object') {
        code = detail.code
        message = detail.message ?? message
      }
    } catch {
      // body 解析失敗は無視
    }
    throw new CompanySearchError(message, res.status, code)
  }

  return res.json() as Promise<CompanySearchResponse>
}

export async function triggerScreening(): Promise<TriggerScreeningResponse> {
  const res = await fetch(`${baseURL}/api/v1/screenings`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) throw new Error(`triggerScreening failed: ${res.status}`)
  return res.json() as Promise<TriggerScreeningResponse>
}

export async function fetchScreeningStatus(
  runId: string,
): Promise<ScreeningRunResponse> {
  const res = await fetch(
    `${baseURL}/api/v1/screenings/${runId}`,
    withCredentials,
  )
  if (!res.ok) throw new Error(`fetchScreeningStatus failed: ${res.status}`)
  return res.json() as Promise<ScreeningRunResponse>
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useCompanies(
  filters: CompanyFilters,
  options?: Omit<UseQueryOptions<CompanyListResponse, Error>, 'queryKey' | 'queryFn'>,
) {
  return useQuery<CompanyListResponse, Error>({
    queryKey: companyKeys.list(filters),
    queryFn: () => fetchCompanies(filters),
    ...options,
  })
}

export function useCompanySearch(
  params: CompanySearchParams | null,
  options?: Omit<
    UseQueryOptions<CompanySearchResponse, CompanySearchError>,
    'queryKey' | 'queryFn'
  >,
) {
  return useQuery<CompanySearchResponse, CompanySearchError>({
    queryKey: companyKeys.search(params ?? undefined),
    queryFn: () => searchCompanies(params as CompanySearchParams),
    enabled: params !== null,
    retry: false,
    ...options,
  })
}

export function useTriggerScreening() {
  return useMutation<TriggerScreeningResponse, Error, void>({
    mutationFn: () => triggerScreening(),
  })
}

export function useScreeningStatus(runId: string | null) {
  return useQuery<ScreeningRunResponse, Error>({
    queryKey: companyKeys.screeningStatus(runId ?? ''),
    queryFn: () => fetchScreeningStatus(runId!),
    enabled: runId !== null,
    refetchInterval: false, // ポーリング制御は hooks.ts で行う
  })
}
