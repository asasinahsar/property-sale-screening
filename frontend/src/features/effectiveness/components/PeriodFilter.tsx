'use client'

import { Button, Paper, Stack, TextField, Typography } from '@mui/material'

import type { PeriodRange } from '../types'

export interface PeriodFilterProps {
  value: PeriodRange
  onChange: (range: PeriodRange) => void
  onReset: () => void
}

export function PeriodFilter({ value, onChange, onReset }: PeriodFilterProps) {
  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        期間フィルタ
      </Typography>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={2}
        alignItems={{ xs: 'stretch', sm: 'center' }}
      >
        <TextField
          label="開始"
          type="date"
          size="small"
          value={value.periodFrom ?? ''}
          onChange={(e) =>
            onChange({ ...value, periodFrom: e.target.value || undefined })
          }
          InputLabelProps={{ shrink: true }}
          inputProps={{ 'aria-label': '開始日' }}
        />
        <TextField
          label="終了"
          type="date"
          size="small"
          value={value.periodTo ?? ''}
          onChange={(e) =>
            onChange({ ...value, periodTo: e.target.value || undefined })
          }
          InputLabelProps={{ shrink: true }}
          inputProps={{ 'aria-label': '終了日' }}
        />
        <Button variant="outlined" size="small" onClick={onReset}>
          リセット
        </Button>
      </Stack>
    </Paper>
  )
}
