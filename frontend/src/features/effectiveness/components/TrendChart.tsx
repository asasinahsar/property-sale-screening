'use client'

import { useState } from 'react'
import {
  Box,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import type { KpiSnapshotSchema } from '../types'

export interface TrendChartProps {
  snapshots: KpiSnapshotSchema[]
}

type MetricKey =
  | 'workload_reduction_rate'
  | 'reproducibility_score'
  | 'universe_coverage'
  | 'traceability_rate'
  | 'avg_structure_score'

const METRIC_OPTIONS: { key: MetricKey; label: string; color: string }[] = [
  { key: 'workload_reduction_rate', label: '工数削減率', color: '#2563eb' },
  { key: 'reproducibility_score', label: '再現性スコア', color: '#7c3aed' },
  { key: 'universe_coverage', label: 'ユニバースカバレッジ', color: '#059669' },
  { key: 'traceability_rate', label: 'トレース可能率', color: '#d97706' },
  { key: 'avg_structure_score', label: '平均構造スコア', color: '#dc2626' },
]

const WIDTH = 640
const HEIGHT = 220
const PADDING = 36

export function TrendChart({ snapshots }: TrendChartProps) {
  const [metric, setMetric] = useState<MetricKey>('workload_reduction_rate')
  const meta = METRIC_OPTIONS.find((m) => m.key === metric)!

  const points = snapshots
    .map((s) => ({
      label: s.period_from,
      value: s[metric],
    }))
    .filter((p): p is { label: string; value: number } => p.value != null)

  const hasData = points.length > 0
  const values = points.map((p) => p.value)
  const maxV = hasData ? Math.max(...values, 0) : 100
  const minV = hasData ? Math.min(...values, 0) : 0
  const range = maxV - minV || 1

  const innerW = WIDTH - PADDING * 2
  const innerH = HEIGHT - PADDING * 2

  const coords = points.map((p, i) => {
    const x =
      points.length === 1
        ? PADDING + innerW / 2
        : PADDING + (i / (points.length - 1)) * innerW
    const y = PADDING + innerH - ((p.value - minV) / range) * innerH
    return { x, y, ...p }
  })

  const linePath = coords
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`)
    .join(' ')

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 1 }}
      >
        <Typography variant="subtitle2" color="text.secondary">
          KPI 推移
        </Typography>
        <TextField
          select
          size="small"
          value={metric}
          onChange={(e) => setMetric(e.target.value as MetricKey)}
          sx={{ minWidth: 200 }}
          inputProps={{ 'aria-label': '指標選択' }}
        >
          {METRIC_OPTIONS.map((opt) => (
            <MenuItem key={opt.key} value={opt.key}>
              {opt.label}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {!hasData ? (
        <Box
          sx={{
            height: HEIGHT,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            表示できるデータがありません
          </Typography>
        </Box>
      ) : (
        <Box sx={{ overflowX: 'auto' }}>
          <svg
            width="100%"
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            role="img"
            aria-label={`${meta.label}の推移チャート`}
          >
            {/* 軸 */}
            <line
              x1={PADDING}
              y1={PADDING}
              x2={PADDING}
              y2={HEIGHT - PADDING}
              stroke="#e5e7eb"
            />
            <line
              x1={PADDING}
              y1={HEIGHT - PADDING}
              x2={WIDTH - PADDING}
              y2={HEIGHT - PADDING}
              stroke="#e5e7eb"
            />
            {/* 折れ線 */}
            <path
              d={linePath}
              fill="none"
              stroke={meta.color}
              strokeWidth={2}
            />
            {/* データ点 */}
            {coords.map((c) => (
              <g key={`${c.label}-${c.x}`}>
                <circle cx={c.x} cy={c.y} r={3.5} fill={meta.color} />
                <text
                  x={c.x}
                  y={c.y - 8}
                  fontSize={10}
                  textAnchor="middle"
                  fill="#374151"
                >
                  {c.value.toFixed(1)}
                </text>
                <text
                  x={c.x}
                  y={HEIGHT - PADDING + 16}
                  fontSize={9}
                  textAnchor="middle"
                  fill="#9ca3af"
                >
                  {c.label}
                </text>
              </g>
            ))}
          </svg>
        </Box>
      )}
    </Paper>
  )
}
