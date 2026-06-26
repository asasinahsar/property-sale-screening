/**
 * Longlist feature - Data Access Layer
 *
 * orval 生成の fetch 関数を wrap し、Cookie 認証（credentials: include）を付与する。
 * 生成コード（shared/api/generated）は編集禁止のため、ここで薄くラップする。
 */
import {
  getLonglistApiV1LonglistGet,
  addLonglistApiV1LonglistPost,
  updateLonglistApiV1LonglistItemIdPatch,
  approveLonglistApiV1LonglistItemIdApprovalPost,
  deleteLonglistApiV1LonglistItemIdDelete,
  exportLonglistApiV1LonglistExportPost,
} from '@/shared/api/generated/propertySaleScreeningAPI'
import type {
  LonglistListResponse,
  LonglistItemSchema,
  LonglistUpdateRequest,
  LonglistExportResponse,
} from '@/shared/api/generated/propertySaleScreeningAPI'

import type { ApprovalAction } from './types'

const withCredentials: RequestInit = { credentials: 'include' }

function ensureOk(status: number): void {
  if (status >= 400) {
    throw new Error(String(status))
  }
}

export async function getLonglist(): Promise<LonglistListResponse> {
  const res = await getLonglistApiV1LonglistGet(withCredentials)
  ensureOk(res.status)
  return res.data as LonglistListResponse
}

export async function addToLonglist(
  companyId: string,
): Promise<LonglistItemSchema> {
  const res = await addLonglistApiV1LonglistPost(
    { company_id: companyId },
    withCredentials,
  )
  ensureOk(res.status)
  return res.data as LonglistItemSchema
}

export async function updateLonglist(
  itemId: string,
  body: LonglistUpdateRequest,
): Promise<LonglistItemSchema> {
  const res = await updateLonglistApiV1LonglistItemIdPatch(
    itemId,
    body,
    withCredentials,
  )
  ensureOk(res.status)
  return res.data as LonglistItemSchema
}

export async function setApproval(
  itemId: string,
  action: ApprovalAction,
): Promise<LonglistItemSchema> {
  const res = await approveLonglistApiV1LonglistItemIdApprovalPost(
    itemId,
    { action },
    withCredentials,
  )
  ensureOk(res.status)
  return res.data as LonglistItemSchema
}

export async function deleteFromLonglist(itemId: string): Promise<void> {
  const res = await deleteLonglistApiV1LonglistItemIdDelete(
    itemId,
    withCredentials,
  )
  ensureOk(res.status)
}

export async function exportLonglist(): Promise<LonglistExportResponse> {
  const res = await exportLonglistApiV1LonglistExportPost(withCredentials)
  ensureOk(res.status)
  return res.data as LonglistExportResponse
}

export type {
  LonglistListResponse,
  LonglistItemSchema,
  LonglistUpdateRequest,
  LonglistExportResponse,
}
