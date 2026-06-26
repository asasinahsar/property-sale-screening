/**
 * Dashboard feature - Business Logic Layer
 */
import { useQuery } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'

import { getDashboardKpi, getRecentEvents } from './api'
import type { DashboardKpiResponse, RecentEventSchema } from './api'

export const dashboardKeys = {
  kpi: ['dashboard', 'kpi'] as const,
  recentEvents: ['dashboard', 'recent-events'] as const,
}

/** ダッシュボード KPI を取得 */
export function useGetDashboardKpi(): UseQueryResult<DashboardKpiResponse, Error> {
  return useQuery({
    queryKey: dashboardKeys.kpi,
    queryFn: getDashboardKpi,
  })
}

/** 直近イベント（直近7日・最大10件）を取得 */
export function useRecentEvents(): UseQueryResult<RecentEventSchema[], Error> {
  return useQuery({
    queryKey: dashboardKeys.recentEvents,
    queryFn: getRecentEvents,
  })
}
