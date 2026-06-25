/**
 * Dashboard feature - Business Logic Layer
 */
import { useQuery } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'

import { getDashboardKpi } from './api'
import type { DashboardKpiResponse } from './api'

export const dashboardKeys = {
  kpi: ['dashboard', 'kpi'] as const,
}

/** ダッシュボード KPI を取得 */
export function useGetDashboardKpi(): UseQueryResult<DashboardKpiResponse, Error> {
  return useQuery({
    queryKey: dashboardKeys.kpi,
    queryFn: getDashboardKpi,
  })
}
