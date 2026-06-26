import { render, screen } from '@testing-library/react'

import { RecentEventsBanner } from './RecentEventsBanner'
import type { RecentEventSchema } from '../api'

const sampleEvents: RecentEventSchema[] = [
  {
    company_id: '11111111-1111-1111-1111-111111111111',
    securities_code: '7203',
    company_name: 'トヨタ自動車',
    event_type: 'new_disclosure',
    occurred_at: '2026-06-25',
    event_score: 72.5,
  },
  {
    company_id: '22222222-2222-2222-2222-222222222222',
    securities_code: '6758',
    company_name: 'ソニーグループ',
    event_type: 'large_shareholding',
    occurred_at: '2026-06-24',
    event_score: null,
  },
]

describe('RecentEventsBanner', () => {
  it('イベントカード（企業名・証券コード・種別ラベル・発生日）を表示する', () => {
    render(<RecentEventsBanner events={sampleEvents} isLoading={false} />)
    expect(screen.getByText('トヨタ自動車')).toBeInTheDocument()
    expect(screen.getByText(/7203/)).toBeInTheDocument()
    expect(screen.getByText('開示')).toBeInTheDocument()
    expect(screen.getByText('大量保有')).toBeInTheDocument()
    expect(screen.getByText('2026-06-25')).toBeInTheDocument()
  })

  it('各カードが企業詳細へのリンクを持つ', () => {
    render(<RecentEventsBanner events={sampleEvents} isLoading={false} />)
    const link = screen.getByRole('link', { name: /トヨタ自動車/ })
    expect(link).toHaveAttribute(
      'href',
      '/companies/11111111-1111-1111-1111-111111111111',
    )
  })

  it('イベントが空のときは何も表示しない', () => {
    const { container } = render(
      <RecentEventsBanner events={[]} isLoading={false} />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('ローディング中は何も表示しない', () => {
    const { container } = render(
      <RecentEventsBanner events={[]} isLoading={true} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
