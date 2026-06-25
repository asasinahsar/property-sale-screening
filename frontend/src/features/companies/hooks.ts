/**
 * Companies feature - Business Logic Layer
 *
 * スクリーニング実行 + ポーリング のカスタム hook。
 */

'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useTriggerScreening, companyKeys } from './api'
import type { ScreeningStatus } from './types'

export interface ScreeningPipelineResult {
  triggerScreening: () => Promise<void>
  isRunning: boolean
  progress: number
  status: ScreeningStatus | null
  error: string | null
}

/**
 * スクリーニング実行 + ポーリング hook
 *
 * 1. POST /api/v1/screenings でスクリーニングをキック
 * 2. 返ってきた run_id で status を 1 秒間隔でポーリング
 * 3. status が 'success' になったら companies クエリを再取得
 * 4. status が 'failed' になったらエラー状態に遷移
 */
export function useScreeningPipeline(): ScreeningPipelineResult {
  const queryClient = useQueryClient()
  const triggerMutation = useTriggerScreening()

  const [runId, setRunId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<ScreeningStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!runId) return

    pollingRef.current = setInterval(async () => {
      try {
        const res = await queryClient.fetchQuery({
          queryKey: companyKeys.screeningStatus(runId),
          queryFn: async () => {
            const baseURL =
              process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
            const response = await fetch(
              `${baseURL}/api/v1/screenings/${runId}`,
              { credentials: 'include' },
            )
            if (!response.ok)
              throw new Error(`polling failed: ${response.status}`)
            return response.json()
          },
          staleTime: 0,
        })

        setProgress(res.progress ?? 0)
        setStatus(res.status)

        if (res.status === 'success') {
          stopPolling()
          setIsRunning(false)
          setRunId(null)
          // companies を再取得
          await queryClient.invalidateQueries({ queryKey: companyKeys.all })
        } else if (res.status === 'failed') {
          stopPolling()
          setIsRunning(false)
          setError('Screening failed')
          setRunId(null)
        }
      } catch (err) {
        stopPolling()
        setIsRunning(false)
        setError(err instanceof Error ? err.message : 'Unknown error')
        setRunId(null)
      }
    }, 1000)

    return () => stopPolling()
  }, [runId, queryClient, stopPolling])

  const triggerScreening = useCallback(async () => {
    setError(null)
    setProgress(0)
    setStatus('pending')
    setIsRunning(true)

    try {
      const result = await triggerMutation.mutateAsync()
      setRunId(result.run_id)
    } catch (err) {
      setIsRunning(false)
      setStatus(null)
      setError(err instanceof Error ? err.message : 'Failed to trigger screening')
    }
  }, [triggerMutation])

  return {
    triggerScreening,
    isRunning,
    progress,
    status,
    error,
  }
}
