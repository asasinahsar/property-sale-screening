/**
 * CompanyDetail feature - Business Logic Layer
 *
 * 企業詳細・レポート生成・ファイルステータス のカスタム hooks。
 */

import { useQuery, useMutation } from '@tanstack/react-query'

import {
  companyDetailKeys,
  fetchCompanyDetail,
  generateReport,
  fetchFileStatus,
} from './api'
import type {
  CompanyDetail,
  FileStatusResponse,
  ReportGenerateResponse,
  FileStatus,
} from './types'

// ---------------------------------------------------------------------------
// useCompanyDetail
// ---------------------------------------------------------------------------

/**
 * 企業詳細情報を取得する hook。
 *
 * @param companyId - 取得対象の企業 ID
 */
export function useCompanyDetail(companyId: string) {
  return useQuery<CompanyDetail, Error>({
    queryKey: companyDetailKeys.detail(companyId),
    queryFn: () => fetchCompanyDetail(companyId),
    enabled: !!companyId,
  })
}

// ---------------------------------------------------------------------------
// useGenerateReport
// ---------------------------------------------------------------------------

/**
 * レポート生成をキックする mutation hook。
 */
export function useGenerateReport() {
  return useMutation<
    ReportGenerateResponse,
    Error,
    { companyId: string; format: 'pdf' }
  >({
    mutationFn: ({ companyId, format }) => generateReport(companyId, format),
  })
}

// ---------------------------------------------------------------------------
// useFileStatus
// ---------------------------------------------------------------------------

/** pending / processing のときにポーリングする間隔（ms） */
const POLLING_INTERVAL_MS = 2000

const isInProgress = (status: FileStatus): boolean =>
  status === 'pending' || status === 'processing'

/**
 * ファイル生成ステータスを取得する hook。
 *
 * - `fileId` が null のときはクエリを実行しない。
 * - status が `pending` または `processing` の間は 2 秒ごとにポーリングする。
 *
 * @param fileId - 監視対象のファイル ID（null の場合は無効）
 */
export function useFileStatus(fileId: string | null) {
  return useQuery<FileStatusResponse, Error>({
    queryKey: companyDetailKeys.fileStatus(fileId ?? ''),
    queryFn: () => fetchFileStatus(fileId!),
    enabled: fileId !== null,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return false
      return isInProgress(data.status) ? POLLING_INTERVAL_MS : false
    },
  })
}
