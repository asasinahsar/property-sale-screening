/**
 * Longlist feature - Business Logic Layer
 *
 * TanStack Query を用いたロングリスト管理のカスタム hooks。
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'

import {
  addToLonglist,
  deleteFromLonglist,
  exportLonglist,
  getLonglist,
  setApproval,
  updateLonglist,
} from './api'
import type {
  LonglistExportResponse,
  LonglistItemSchema,
  LonglistListResponse,
  LonglistUpdateRequest,
} from './api'
import type { ApprovalAction } from './types'

export const longlistKeys = {
  all: ['longlist'] as const,
  list: () => [...longlistKeys.all, 'list'] as const,
}

/** ロングリスト一覧を取得 */
export function useLonglist(): UseQueryResult<LonglistListResponse, Error> {
  return useQuery({
    queryKey: longlistKeys.list(),
    queryFn: getLonglist,
  })
}

/** 企業をロングリストに追加 */
export function useAddToLonglist() {
  const queryClient = useQueryClient()
  return useMutation<LonglistItemSchema, Error, { companyId: string }>({
    mutationFn: ({ companyId }) => addToLonglist(companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: longlistKeys.list() })
    },
  })
}

/** メモ・ステータスを更新 */
export function useUpdateLonglist() {
  const queryClient = useQueryClient()
  return useMutation<
    LonglistItemSchema,
    Error,
    { itemId: string; body: LonglistUpdateRequest }
  >({
    mutationFn: ({ itemId, body }) => updateLonglist(itemId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: longlistKeys.list() })
    },
  })
}

/** 承認 / 却下（manager のみ） */
export function useSetApproval() {
  const queryClient = useQueryClient()
  return useMutation<
    LonglistItemSchema,
    Error,
    { itemId: string; action: ApprovalAction }
  >({
    mutationFn: ({ itemId, action }) => setApproval(itemId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: longlistKeys.list() })
    },
  })
}

/** ロングリストから削除 */
export function useDeleteFromLonglist() {
  const queryClient = useQueryClient()
  return useMutation<void, Error, { itemId: string }>({
    mutationFn: ({ itemId }) => deleteFromLonglist(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: longlistKeys.list() })
    },
  })
}

/** CSV エクスポート */
export function useExportLonglist() {
  return useMutation<LonglistExportResponse, Error, void>({
    mutationFn: () => exportLonglist(),
  })
}
