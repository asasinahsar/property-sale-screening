'use client'

import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import { useAddWorkLog } from '../hooks'
import type { TaskType } from '../types'

const TASK_TYPE_OPTIONS: { value: TaskType; label: string }[] = [
  { value: 'primary_screening', label: '一次スクリーニング' },
  { value: 'deep_dive', label: '深掘り分析' },
  { value: 'report', label: 'レポート作成' },
  { value: 'other', label: 'その他' },
]

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export function WorkLogForm() {
  const { addWorkLog, isPending, error } = useAddWorkLog()

  const [taskType, setTaskType] = useState<TaskType>('primary_screening')
  const [durationMin, setDurationMin] = useState<string>('')
  const [loggedOn, setLoggedOn] = useState<string>(today())
  const [success, setSuccess] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSuccess(false)
    setValidationError(null)

    const minutes = Number(durationMin)
    if (!durationMin || Number.isNaN(minutes) || minutes <= 0) {
      setValidationError('所要時間は1以上の数値で入力してください')
      return
    }

    try {
      await addWorkLog({
        task_type: taskType,
        duration_min: minutes,
        logged_on: loggedOn,
      })
      setSuccess(true)
      setDurationMin('')
    } catch {
      // error は hook 側で保持
    }
  }

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        工数ログ入力
      </Typography>
      <Box component="form" onSubmit={handleSubmit}>
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={2}
          alignItems={{ xs: 'stretch', sm: 'flex-start' }}
        >
          <TextField
            select
            label="タスク種別"
            size="small"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value as TaskType)}
            sx={{ minWidth: 180 }}
            inputProps={{ 'aria-label': 'タスク種別' }}
          >
            {TASK_TYPE_OPTIONS.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>
                {opt.label}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="所要時間（分）"
            type="number"
            size="small"
            value={durationMin}
            onChange={(e) => setDurationMin(e.target.value)}
            inputProps={{ min: 1, 'aria-label': '所要時間（分）' }}
          />
          <TextField
            label="記録日"
            type="date"
            size="small"
            value={loggedOn}
            onChange={(e) => setLoggedOn(e.target.value)}
            InputLabelProps={{ shrink: true }}
            inputProps={{ 'aria-label': '記録日' }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={isPending}
            sx={{ minWidth: 120 }}
          >
            {isPending ? '記録中...' : '記録する'}
          </Button>
        </Stack>
      </Box>

      {validationError && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          {validationError}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          記録に失敗しました
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          工数ログを記録しました
        </Alert>
      )}
    </Paper>
  )
}
