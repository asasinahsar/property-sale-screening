/**
 * Dashboard feature - Data Access Layer
 *
 * orval 生成の fetch 関数を wrap し、Cookie 認証を付与する。
 */
import {
  getDashboardKpiApiV1DashboardKpiGet,
  getRecentEventsApiV1EventsRecentGet,
} from '@/shared/api/generated/propertySaleScreeningAPI'
import type {
  DashboardKpiResponse,
  RecentEventSchema,
} from '@/shared/api/generated/propertySaleScreeningAPI'

const withCredentials: RequestInit = { credentials: 'include' }

export async function getDashboardKpi(): Promise<DashboardKpiResponse> {
  const res = await getDashboardKpiApiV1DashboardKpiGet(withCredentials)
  if (res.status >= 400) {
    throw new Error(String(res.status))
  }
  return res.data as DashboardKpiResponse
}

/** 直近イベント（直近7日・最大10件）を取得 */
export async function getRecentEvents(): Promise<RecentEventSchema[]> {
  const res = await getRecentEventsApiV1EventsRecentGet(withCredentials)
  if (res.status >= 400) {
    throw new Error(String(res.status))
  }
  return res.data as RecentEventSchema[]
}

export type { DashboardKpiResponse, RecentEventSchema }
