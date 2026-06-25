'use client'

import { Grid, Skeleton } from '@mui/material'
import { KpiCard } from './KpiCard'
import type { DashboardKpiResponse } from '../api'

export interface DashboardKpiSectionProps {
  data: DashboardKpiResponse | undefined
  isLoading: boolean
}

const KPI_COLORS = {
  total: 'primary.main',
  high: 'success.main',
  avg: 'warning.main',
  event: 'info.main',
} as const

export function DashboardKpiSection({ data, isLoading }: DashboardKpiSectionProps) {
  const kpis = [
    {
      title: '対象企業数',
      value: data?.total_companies ?? 0,
      color: KPI_COLORS.total,
    },
    {
      title: '高スコア企業数',
      value: data?.high_score_companies ?? 0,
      color: KPI_COLORS.high,
    },
    {
      title: '平均スコア',
      value: data?.avg_score != null ? data.avg_score.toFixed(1) : '0.0',
      color: KPI_COLORS.avg,
    },
    {
      title: 'イベント件数',
      value: data?.event_count ?? 0,
      color: KPI_COLORS.event,
    },
  ]

  return (
    <Grid container spacing={2} sx={{ mb: 4 }}>
      {kpis.map((kpi) => (
        <Grid item xs={12} sm={6} md={3} key={kpi.title}>
          {isLoading ? (
            <Skeleton variant="rounded" height={110} data-testid="kpi-skeleton" />
          ) : (
            <KpiCard title={kpi.title} value={kpi.value} color={kpi.color} />
          )}
        </Grid>
      ))}
    </Grid>
  )
}
