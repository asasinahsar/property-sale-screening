import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import type { LonglistItemSchema } from '../types'

import { LonglistTable } from './LonglistTable'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock('../hooks', () => ({
  useLonglist: jest.fn(),
  useAddToLonglist: jest.fn(() => ({ mutate: jest.fn(), isPending: false })),
  useUpdateLonglist: jest.fn(() => ({ mutate: jest.fn(), isPending: false })),
  useSetApproval: jest.fn(() => ({ mutate: jest.fn(), isPending: false })),
  useDeleteFromLonglist: jest.fn(() => ({ mutate: jest.fn(), isPending: false })),
  useExportLonglist: jest.fn(() => ({ mutate: jest.fn(), isPending: false })),
}))

jest.mock('@/features/auth', () => ({
  useGetMe: jest.fn(),
}))

import { useLonglist } from '../hooks'
import { useGetMe } from '@/features/auth'

const mockUseLonglist = useLonglist as jest.MockedFunction<typeof useLonglist>
const mockUseGetMe = useGetMe as jest.MockedFunction<typeof useGetMe>

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const mockItem: LonglistItemSchema = {
  id: 'item-1',
  company_id: 'company-1',
  securities_code: '1234',
  name: 'テスト不動産株式会社',
  industry: '不動産業',
  total_score: 85.0,
  structure_score: 72.5,
  event_score: 65.0,
  unrealized_gain: 400.0,
  status: 'candidate',
  reason_memo: '含み益が大きい',
  created_by: 'user-1',
  created_at: '2025-06-25T09:00:00',
  approved_by: null,
  approved_at: null,
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildQueryResult<T>(
  overrides: Partial<{
    data: T | undefined
    isLoading: boolean
    isError: boolean
    error: Error | null
  }>,
) {
  return {
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    ...overrides,
  } as unknown as ReturnType<typeof useLonglist>
}

function setRole(role: 'analyst' | 'manager') {
  mockUseGetMe.mockReturnValue({
    data: { id: 'user-1', role },
  } as unknown as ReturnType<typeof useGetMe>)
}

function renderTable() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <LonglistTable />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  jest.clearAllMocks()
  setRole('analyst')
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('LonglistTable', () => {
  describe('正常系', () => {
    beforeEach(() => {
      mockUseLonglist.mockReturnValue(
        buildQueryResult({ data: { items: [mockItem], total: 1 } }),
      )
    })

    it('企業名が表示される', () => {
      renderTable()
      expect(screen.getByText('テスト不動産株式会社')).toBeInTheDocument()
    })

    it('総合スコアが表示される', () => {
      renderTable()
      expect(screen.getByText(/85(\.0)?/)).toBeInTheDocument()
    })

    it('ステータスバッジが表示される', () => {
      renderTable()
      expect(screen.getByText(/candidate/i)).toBeInTheDocument()
    })

    it('エクスポートボタンが存在する', () => {
      renderTable()
      expect(
        screen.getByRole('button', { name: /export/i }),
      ).toBeInTheDocument()
    })

    it('analyst では承認ボタンが無効になっている', () => {
      setRole('analyst')
      renderTable()
      const approveBtn = screen.getByRole('button', { name: /approve/i })
      expect(approveBtn).toBeDisabled()
    })

    it('manager では承認ボタンが有効になっている', () => {
      setRole('manager')
      renderTable()
      const approveBtn = screen.getByRole('button', { name: /approve/i })
      expect(approveBtn).toBeEnabled()
    })

    it('削除ボタンをクリックすると確認ダイアログが表示される', () => {
      renderTable()
      const deleteBtn = screen.getByRole('button', { name: /delete/i })
      fireEvent.click(deleteBtn)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  describe('ローディング', () => {
    it('ローディング中は企業名が表示されない', () => {
      mockUseLonglist.mockReturnValue(
        buildQueryResult({ data: undefined, isLoading: true }),
      )
      renderTable()
      expect(
        screen.queryByText('テスト不動産株式会社'),
      ).not.toBeInTheDocument()
    })
  })

  describe('空状態', () => {
    it('項目が0件のとき空メッセージが表示される', () => {
      mockUseLonglist.mockReturnValue(
        buildQueryResult({ data: { items: [], total: 0 } }),
      )
      renderTable()
      expect(screen.getByText(/no items|empty|データがありません/i)).toBeInTheDocument()
    })
  })
})
