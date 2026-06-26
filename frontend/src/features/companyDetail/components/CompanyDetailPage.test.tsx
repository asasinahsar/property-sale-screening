import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import type { CompanyDetail } from '../types'

import { CompanyDetailPage } from './CompanyDetailPage'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock('../hooks', () => ({
  useCompanyDetail: jest.fn(),
  useGenerateReport: jest.fn(() => ({
    mutate: jest.fn(),
    isPending: false,
  })),
  useFileStatus: jest.fn(() => ({
    data: undefined,
    isLoading: false,
  })),
}))

import { useCompanyDetail } from '../hooks'

const mockUseCompanyDetail = useCompanyDetail as jest.MockedFunction<
  typeof useCompanyDetail
>

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

const mockCompanyDetail: CompanyDetail = {
  company_id: 'uuid-123',
  securities_code: '1234',
  name: 'テスト不動産株式会社',
  industry: '不動産業',
  market_cap: 50000000000,
  scoring: {
    structure_score: 72.5,
    event_score: 65.0,
    total_score: 85.0,
    event_boost: 1.2,
    confidence: 'high',
    ai_judgment: 'この企業は売却可能性が高い',
    judgment_refs: null,
    score_breakdown: null,
  },
  financial: {
    as_of_date: '2024-03-31',
    revenue: 100000000000,
    pbr: 0.65,
    adjusted_pbr: 0.55,
    equity_ratio: 0.45,
    re_market_value: 80000000000,
    re_book_value: 60000000000,
    unrealized_gain: 20000000000,
    unrealized_gain_ratio: 0.4,
    roic: 0.03,
    wacc: 0.05,
    stock_price: 1200,
    roic_wacc_gap: -0.02,
  },
  signals_support: [
    {
      signal_id: 'sig-1',
      signal_type: 'activist_proposal',
      stance: 'support',
      strength: 0.85,
      quote_text: 'アクティビスト投資家が売却を提案した',
      source_page: 12,
      document: {
        document_id: 'doc-1',
        document_type: 'yuho',
        disclosed_at: '2024-01-15',
        source_url: 'https://example.com/doc/1',
      },
    },
  ],
  signals_counter: [],
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** react-query の useQuery 戻り値を最小限満たすモックを生成する。 */
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
  } as unknown as ReturnType<typeof useCompanyDetail>
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <CompanyDetailPage company_id="uuid-123" />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  jest.clearAllMocks()
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CompanyDetailPage', () => {
  describe('正常系', () => {
    beforeEach(() => {
      mockUseCompanyDetail.mockReturnValue(
        buildQueryResult({ data: mockCompanyDetail }),
      )
    })

    it('企業名が表示される', () => {
      renderPage()
      expect(screen.getByText('テスト不動産株式会社')).toBeInTheDocument()
    })

    it('証券コードが表示される', () => {
      renderPage()
      expect(screen.getByText(/1234/)).toBeInTheDocument()
    })

    it('総合スコアが表示される', () => {
      renderPage()
      expect(screen.getByText(/85(\.0)?/)).toBeInTheDocument()
    })

    it('定性シグナル（support）が表示される', () => {
      renderPage()
      expect(
        screen.getByText('アクティビスト投資家が売却を提案した'),
      ).toBeInTheDocument()
    })

    it('レポート出力ボタンが存在する', () => {
      renderPage()
      const button = screen.getByRole('button', { name: /レポート|PDF/i })
      expect(button).toBeInTheDocument()
    })

    it('ROIC < WACC のとき ROIC と WACC が表示される', () => {
      renderPage()
      expect(screen.getByText(/ROIC/i)).toBeInTheDocument()
      expect(screen.getByText(/WACC/i)).toBeInTheDocument()
    })
  })

  describe('ローディング', () => {
    it('ローディング中はローディング表示になり企業名は表示されない', () => {
      mockUseCompanyDetail.mockReturnValue(
        buildQueryResult({ data: undefined, isLoading: true }),
      )
      renderPage()
      expect(
        screen.queryByText('テスト不動産株式会社'),
      ).not.toBeInTheDocument()
    })
  })

  describe('エラー', () => {
    it('エラー時はエラーメッセージが表示される', () => {
      mockUseCompanyDetail.mockReturnValue(
        buildQueryResult({
          data: undefined,
          isError: true,
          error: new Error('Not found'),
        }),
      )
      renderPage()
      expect(screen.getByText(/error|エラー|not found/i)).toBeInTheDocument()
    })
  })
})
