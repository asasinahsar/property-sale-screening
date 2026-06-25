'use client'

import { Box, Button, CircularProgress, LinearProgress, Typography } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'

export interface ScreeningButtonProps {
  onTrigger: () => void
  isRunning: boolean
  progress: number
}

export function ScreeningButton({
  onTrigger,
  isRunning,
  progress,
}: ScreeningButtonProps) {
  return (
    <Box>
      <Button
        variant="contained"
        color="primary"
        startIcon={isRunning ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
        onClick={onTrigger}
        disabled={isRunning}
      >
        {isRunning ? 'スクリーニング実行中...' : 'スクリーニング実行'}
      </Button>
      {isRunning && (
        <Box sx={{ mt: 1, maxWidth: 320 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="caption" color="text.secondary">
            {progress}%
          </Typography>
        </Box>
      )}
    </Box>
  )
}
