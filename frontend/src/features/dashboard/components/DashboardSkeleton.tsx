'use client'

import {
  Box,
  Grid,
  Paper,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'

import { useGetDashboardKpi } from '../hooks'
import { KpiCard } from './KpiCard'

// i18n 未設定のため文字列定数として定義
const LABELS = {
  title: 'ダッシュボード',
  totalCompanies: '対象企業数',
  highScoreCompanies: '高スコア企業数',
  avgScore: '平均スコア',
  eventCount: 'イベント件数',
  filters: 'フィルタ',
  table: '企業一覧',
} as const

const KPI_COLORS = {
  total: 'primary.main',
  high: 'success.main',
  avg: 'warning.main',
  event: 'info.main',
} as const

export function DashboardSkeleton() {
  const { data, isLoading } = useGetDashboardKpi()

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        {LABELS.title}
      </Typography>

      {/* KPI カード枠 */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rounded" height={110} data-testid="kpi-skeleton" />
          ) : (
            <KpiCard
              title={LABELS.totalCompanies}
              value={data?.total_companies ?? 0}
              color={KPI_COLORS.total}
            />
          )}
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rounded" height={110} data-testid="kpi-skeleton" />
          ) : (
            <KpiCard
              title={LABELS.highScoreCompanies}
              value={data?.high_score_companies ?? 0}
              color={KPI_COLORS.high}
            />
          )}
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rounded" height={110} data-testid="kpi-skeleton" />
          ) : (
            <KpiCard
              title={LABELS.avgScore}
              value={data?.avg_score ?? 0}
              color={KPI_COLORS.avg}
            />
          )}
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          {isLoading ? (
            <Skeleton variant="rounded" height={110} data-testid="kpi-skeleton" />
          ) : (
            <KpiCard
              title={LABELS.eventCount}
              value={data?.event_count ?? 0}
              color={KPI_COLORS.event}
            />
          )}
        </Grid>
      </Grid>

      {/* フィルタ枠（Slice 2 以降で実装） */}
      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          {LABELS.filters}
        </Typography>
        <Stack direction="row" spacing={2}>
          <Skeleton variant="rounded" width={200} height={40} />
          <Skeleton variant="rounded" width={200} height={40} />
          <Skeleton variant="rounded" width={120} height={40} />
        </Stack>
      </Paper>

      {/* テーブル枠（Slice 2 以降で実装） */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          {LABELS.table}
        </Typography>
        <Stack spacing={1}>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} variant="rounded" height={48} />
          ))}
        </Stack>
      </Paper>
    </Box>
  )
}
