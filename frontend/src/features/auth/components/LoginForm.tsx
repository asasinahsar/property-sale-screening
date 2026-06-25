'use client'

import { useState } from 'react'
import type { FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material'

import { useAuth } from '../hooks'

// i18n 未設定のため文字列定数として定義（JSX 内に日本語を直書きしない）
const LABELS = {
  title: 'ログイン',
  email: 'メールアドレス',
  password: 'パスワード',
  submit: 'ログイン',
  submitting: 'ログイン中...',
  errorRequired: 'メールアドレスとパスワードを入力してください',
  errorAuth: 'メールアドレスまたはパスワードが正しくありません',
  errorLocked: 'アカウントが一時的にロックされています。しばらくしてから再度お試しください',
  errorGeneric: 'ログインに失敗しました。時間をおいて再度お試しください',
} as const

function messageForStatus(status: string): string {
  switch (status) {
    case '401':
      return LABELS.errorAuth
    case '403':
      return LABELS.errorLocked
    default:
      return LABELS.errorGeneric
  }
}

export function LoginForm() {
  const router = useRouter()
  const { login, isLoggingIn } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password.trim()) {
      setError(LABELS.errorRequired)
      return
    }

    try {
      await login({ login_email: email, password })
      router.push('/dashboard')
    } catch (err) {
      const status = err instanceof Error ? err.message : ''
      setError(messageForStatus(status))
    }
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      noValidate
      sx={{ width: '100%' }}
    >
      <Typography variant="h5" fontWeight="bold" mb={3}>
        {LABELS.title}
      </Typography>

      <Stack spacing={2}>
        {error && (
          <Alert severity="error" role="alert">
            {error}
          </Alert>
        )}

        <TextField
          label={LABELS.email}
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
          autoComplete="email"
          disabled={isLoggingIn}
          inputProps={{ 'aria-label': LABELS.email }}
        />

        <TextField
          label={LABELS.password}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          fullWidth
          autoComplete="current-password"
          disabled={isLoggingIn}
          inputProps={{ 'aria-label': LABELS.password }}
        />

        <Button
          type="submit"
          variant="contained"
          size="large"
          fullWidth
          disabled={isLoggingIn}
          startIcon={
            isLoggingIn ? <CircularProgress size={18} color="inherit" /> : undefined
          }
        >
          {isLoggingIn ? LABELS.submitting : LABELS.submit}
        </Button>
      </Stack>
    </Box>
  )
}
