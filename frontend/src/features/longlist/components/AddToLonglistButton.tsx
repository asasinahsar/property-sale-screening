'use client'

import { useState } from 'react'
import { Button, Snackbar, Alert } from '@mui/material'

import { useAddToLonglist } from '../hooks'

interface AddToLonglistButtonProps {
  companyId: string
  variant?: 'text' | 'outlined' | 'contained'
  size?: 'small' | 'medium' | 'large'
}

/**
 * 企業をロングリストに追加するボタン。
 * ダッシュボード・企業詳細から利用する。
 */
export function AddToLonglistButton({
  companyId,
  variant = 'outlined',
  size = 'small',
}: AddToLonglistButtonProps) {
  const { mutate, isPending } = useAddToLonglist()
  const [feedback, setFeedback] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    mutate(
      { companyId },
      {
        onSuccess: () =>
          setFeedback({ type: 'success', message: 'Added to longlist' }),
        onError: (err) => {
          const isDuplicate = err.message === '409'
          setFeedback({
            type: 'error',
            message: isDuplicate
              ? 'Already in longlist'
              : 'Failed to add to longlist',
          })
        },
      },
    )
  }

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={handleClick}
        disabled={isPending}
        aria-label="Add to longlist"
      >
        Add to longlist
      </Button>
      <Snackbar
        open={feedback !== null}
        autoHideDuration={3000}
        onClose={() => setFeedback(null)}
      >
        <Alert
          severity={feedback?.type ?? 'success'}
          onClose={() => setFeedback(null)}
        >
          {feedback?.message}
        </Alert>
      </Snackbar>
    </>
  )
}
