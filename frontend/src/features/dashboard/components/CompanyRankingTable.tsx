'use client'

import {
  Box,
  Chip,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import type { CompanyRankingItemSchema, ConfidenceLevel } from '@/features/companies'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CompanyRankingTableProps {
  items: CompanyRankingItemSchema[]
  isLoading: boolean
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const CONFIDENCE_COLORS: Record<
  ConfidenceLevel,
  'success' | 'warning' | 'error'
> = {
  high: 'success',
  mid: 'warning',
  low: 'error',
}

function fmt(value: number, digits = 1): string {
  return value.toFixed(digits)
}

// ---------------------------------------------------------------------------
// Column headers
// ---------------------------------------------------------------------------

const COLUMNS = [
  '#',
  '企業名（証券コード）',
  '業種',
  '総合スコア',
  '構造スコア',
  'イベントスコア',
  '含み益',
  '確信度',
  'イベント',
] as const

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function CompanyRankingTable({
  items,
  isLoading,
}: CompanyRankingTableProps) {
  if (isLoading) {
    return (
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              {COLUMNS.map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                {COLUMNS.map((col) => (
                  <TableCell key={col}>
                    <Skeleton variant="text" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            {COLUMNS.map((col) => (
              <TableCell
                key={col}
                align={
                  ['総合スコア', '構造スコア', 'イベントスコア', '含み益'].includes(
                    col,
                  )
                    ? 'right'
                    : 'left'
                }
              >
                {col}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item, index) => (
            <TableRow key={item.company_id} hover>
              <TableCell>{index + 1}</TableCell>
              <TableCell>
                {item.name}
                <Box
                  component="span"
                  sx={{ ml: 0.5, color: 'text.secondary', fontSize: '0.75rem' }}
                >
                  ({item.securities_code})
                </Box>
              </TableCell>
              <TableCell>{item.industry}</TableCell>
              <TableCell align="right">{fmt(item.total_score)}</TableCell>
              <TableCell align="right">{fmt(item.structure_score)}</TableCell>
              <TableCell align="right">{fmt(item.event_score)}</TableCell>
              <TableCell align="right">
                {item.unrealized_gain != null ? item.unrealized_gain.toLocaleString() : '—'}
              </TableCell>
              <TableCell>
                <Chip
                  label={item.confidence}
                  color={CONFIDENCE_COLORS[item.confidence]}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip
                  label={item.has_event ? 'あり' : 'なし'}
                  variant="outlined"
                  size="small"
                  color={item.has_event ? 'primary' : 'default'}
                />
              </TableCell>
            </TableRow>
          ))}
          {items.length === 0 && (
            <TableRow>
              <TableCell colSpan={COLUMNS.length} align="center">
                データがありません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
