/**
 * CompanyDetail feature - Data Access Layer
 *
 * 企業詳細・レポート生成・ファイルステータス取得 の fetch wrapper。
 * orval 生成コードに該当エンドポイントが未追加のため直接 fetch で実装する。
 */

import type {
  CompanyDetail,
  ReportGenerateResponse,
  FileStatusResponse,
} from './types'

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
const withCredentials: RequestInit = { credentials: 'include' }

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const companyDetailKeys = {
  all: ['companyDetail'] as const,
  detail: (companyId: string) =>
    [...companyDetailKeys.all, companyId] as const,
  fileStatus: (fileId: string) => ['fileStatus', fileId] as const,
}

// ---------------------------------------------------------------------------
// Fetch functions
// ---------------------------------------------------------------------------

/**
 * GET /api/v1/companies/{companyId}
 * 企業詳細情報（スコア・財務・シグナル）を取得する。
 */
export async function fetchCompanyDetail(
  companyId: string,
): Promise<CompanyDetail> {
  const res = await fetch(
    `${baseURL}/api/v1/companies/${companyId}`,
    withCredentials,
  )
  if (!res.ok) throw new Error(`fetchCompanyDetail failed: ${res.status}`)
  return res.json() as Promise<CompanyDetail>
}

/**
 * POST /api/v1/companies/{companyId}/report
 * レポート生成をキックし、生成ジョブ情報を返す。
 */
export async function generateReport(
  companyId: string,
  format: 'pdf',
): Promise<ReportGenerateResponse> {
  const res = await fetch(`${baseURL}/api/v1/companies/${companyId}/report`, {
    ...withCredentials,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ format }),
  })
  if (!res.ok) throw new Error(`generateReport failed: ${res.status}`)
  return res.json() as Promise<ReportGenerateResponse>
}

/**
 * GET /api/v1/files/{fileId}
 * ファイル生成ステータスとダウンロード URL を取得する。
 */
export async function fetchFileStatus(
  fileId: string,
): Promise<FileStatusResponse> {
  const res = await fetch(`${baseURL}/api/v1/files/${fileId}`, withCredentials)
  if (!res.ok) throw new Error(`fetchFileStatus failed: ${res.status}`)
  return res.json() as Promise<FileStatusResponse>
}
