'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import {
  Alert,
  Box,
  Button,
  Stack,
  Typography,
} from '@mui/material'

import { useEffectiveness, useWorkLogs } from '../hooks'
import type { PeriodRange, WorkLogRange } from '../types'
import { KpiCards } from './KpiCards'
import { TrendChart } from './TrendChart'
import { PeriodFilter } from './PeriodFilter'
import { WorkLogForm } from './WorkLogForm'

export function EffectivenessPage() {
  const [period, setPeriod] = useState<PeriodRange>({})

  const { data, isLoading, error } = useEffectiveness(period)

  const workLogRange: WorkLogRange = useMemo(
    () => ({ from: period.periodFrom, to: period.periodTo }),
    [period],
  )
  const { data: workLogs } = useWorkLogs(workLogRange)

  const latest = data?.latest ?? null
  const snapshots = data?.snapshots ?? []

  return (
    <Box sx={{ p: 4 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" fontWeight="bold">
          効果検証ダッシュボード
        </Typography>
        <Button component={Link} href="/dashboard" variant="outlined">
          ダッシュボードへ
        </Button>
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          KPI の取得に失敗しました
        </Alert>
      )}

      <PeriodFilter
        value={period}
        onChange={setPeriod}
        onReset={() => setPeriod({})}
      />

      <KpiCards snapshot={latest} isLoading={isLoading} />

      <Box sx={{ mb: 3 }}>
        <TrendChart snapshots={snapshots} />
      </Box>

      <WorkLogForm />

      {workLogs && (
        <Typography variant="body2" color="text.secondary">
          期間内の合計工数: {workLogs.total_min} 分（
          {workLogs.items?.length ?? 0} 件）
        </Typography>
      )}
    </Box>
  )
}
