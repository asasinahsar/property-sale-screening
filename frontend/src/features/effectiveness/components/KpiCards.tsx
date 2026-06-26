'use client'

import { Box, Card, CardContent, Skeleton, Typography } from '@mui/material'

import type { KpiSnapshotSchema } from '../types'

export interface KpiCardsProps {
  snapshot: KpiSnapshotSchema | null | undefined
  isLoading?: boolean
}

interface KpiItem {
  title: string
  value: string
  color: string
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${Number(value).toFixed(1)}%`
}

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return Number(value).toFixed(1)
}

export function KpiCards({ snapshot, isLoading }: KpiCardsProps) {
  const items: KpiItem[] = [
    {
      title: '工数削減率',
      value: formatPercent(snapshot?.workload_reduction_rate),
      color: '#2563eb',
    },
    {
      title: '再現性スコア',
      value: formatScore(snapshot?.reproducibility_score),
      color: '#7c3aed',
    },
    {
      title: 'ユニバースカバレッジ',
      value: formatPercent(snapshot?.universe_coverage),
      color: '#059669',
    },
    {
      title: 'トレース可能率',
      value: formatPercent(snapshot?.traceability_rate),
      color: '#d97706',
    },
    {
      title: '平均構造スコア',
      value: formatScore(snapshot?.avg_structure_score),
      color: '#dc2626',
    },
  ]

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          md: 'repeat(5, 1fr)',
        },
        gap: 2,
        mb: 3,
      }}
    >
      {items.map((item) => (
        <Card key={item.title} variant="outlined" sx={{ height: '100%' }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {item.title}
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'baseline',
                borderLeft: 4,
                borderColor: item.color,
                pl: 1.5,
              }}
            >
              {isLoading ? (
                <Skeleton width={80} height={48} />
              ) : (
                <Typography
                  variant="h4"
                  fontWeight="bold"
                  sx={{ color: item.color }}
                >
                  {item.value}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      ))}
    </Box>
  )
}
