'use client'

import { useState } from 'react'
import { Alert, Box, Paper, Stack, Typography } from '@mui/material'

import { useGetDashboardKpi } from '../hooks'
import { DashboardKpiSection } from './DashboardKpiSection'
import { ScreeningButton } from './ScreeningButton'
import { CompanyRankingTable } from './CompanyRankingTable'

import { useCompanies, useScreeningPipeline } from '@/features/companies'
import type { CompanyFilters } from '@/features/companies'

const DEFAULT_FILTERS: CompanyFilters = {
  sortBy: 'total_score',
  page: 1,
  pageSize: 20,
}

export function DashboardContent() {
  const [filters] = useState<CompanyFilters>(DEFAULT_FILTERS)

  const { data: kpiData, isLoading: kpiLoading } = useGetDashboardKpi()
  const { data: companiesData, isLoading: companiesLoading } = useCompanies(filters)
  const { triggerScreening, isRunning, progress, error: screeningError } = useScreeningPipeline()

  return (
    <Box sx={{ p: 4 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 3 }}
      >
        <Typography variant="h4" fontWeight="bold">
          ダッシュボード
        </Typography>
        <ScreeningButton
          onTrigger={triggerScreening}
          isRunning={isRunning}
          progress={progress}
        />
      </Stack>

      {screeningError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {screeningError}
        </Alert>
      )}

      <DashboardKpiSection data={kpiData} isLoading={kpiLoading} />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          企業ランキング
        </Typography>
        <CompanyRankingTable
          items={companiesData?.items ?? []}
          isLoading={companiesLoading}
        />
      </Paper>
    </Box>
  )
}
