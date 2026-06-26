'use client'

import { useCallback, useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material'

import { useGetDashboardKpi } from '../hooks'
import { DashboardKpiSection } from './DashboardKpiSection'
import { ScreeningButton } from './ScreeningButton'
import { CompanyRankingTable } from './CompanyRankingTable'
import { SearchBox } from './SearchBox'
import { CompanySearchResults } from './CompanySearchResults'

import {
  useCompanies,
  useCompanySearch,
  useScreeningPipeline,
} from '@/features/companies'
import type {
  ClassifiedQuery,
  CompanyFilters,
  CompanySearchParams,
} from '@/features/companies'

const DEFAULT_FILTERS: CompanyFilters = {
  sortBy: 'total_score',
  page: 1,
  pageSize: 20,
}

/** URL の ?q= から初期検索文字列を読み取る（クライアントのみ） */
function readInitialQuery(): string {
  if (typeof window === 'undefined') return ''
  return new URLSearchParams(window.location.search).get('q') ?? ''
}

function toSearchParams(query: ClassifiedQuery): CompanySearchParams {
  switch (query.kind) {
    case 'securities_code':
      return { securitiesCode: query.value }
    case 'company_name':
      return { companyName: query.value }
    case 'nl':
      return { q: query.value }
  }
}

export function DashboardContent() {
  const router = useRouter()
  const pathname = usePathname()

  const [filters] = useState<CompanyFilters>(DEFAULT_FILTERS)
  const [initialQuery] = useState<string>(readInitialQuery)
  const [searchParams, setSearchParams] = useState<CompanySearchParams | null>(
    initialQuery ? { q: initialQuery } : null,
  )

  const { data: kpiData, isLoading: kpiLoading } = useGetDashboardKpi()
  const { data: companiesData, isLoading: companiesLoading } = useCompanies(
    filters,
    { enabled: searchParams === null },
  )
  const {
    data: searchData,
    isLoading: searchLoading,
    error: searchError,
  } = useCompanySearch(searchParams)
  const {
    triggerScreening,
    isRunning,
    progress,
    error: screeningError,
  } = useScreeningPipeline()

  const syncUrl = useCallback(
    (rawValue: string | null) => {
      const params = new URLSearchParams(window.location.search)
      if (rawValue) {
        params.set('q', rawValue)
      } else {
        params.delete('q')
      }
      const qs = params.toString()
      router.push(qs ? `${pathname}?${qs}` : pathname)
    },
    [router, pathname],
  )

  const handleSearch = useCallback(
    (query: ClassifiedQuery) => {
      setSearchParams(toSearchParams(query))
      syncUrl(query.value)
    },
    [syncUrl],
  )

  const handleClear = useCallback(() => {
    setSearchParams(null)
    syncUrl(null)
  }, [syncUrl])

  const isSearching = searchParams !== null

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
        <Stack direction="row" spacing={2} alignItems="center">
          <Button component={Link} href="/effectiveness" variant="outlined">
            効果検証
          </Button>
          <ScreeningButton
            onTrigger={triggerScreening}
            isRunning={isRunning}
            progress={progress}
          />
        </Stack>
      </Stack>

      {screeningError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {screeningError}
        </Alert>
      )}

      <DashboardKpiSection data={kpiData} isLoading={kpiLoading} />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          企業検索・ランキング
        </Typography>

        <SearchBox
          onSearch={handleSearch}
          onClear={handleClear}
          initialValue={initialQuery}
        />

        {isSearching ? (
          <CompanySearchResults
            data={searchData}
            isLoading={searchLoading}
            error={searchError}
          />
        ) : (
          <CompanyRankingTable
            items={companiesData?.items ?? []}
            isLoading={companiesLoading}
          />
        )}
      </Paper>
    </Box>
  )
}
