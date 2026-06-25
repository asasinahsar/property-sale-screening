import { render, screen } from '@testing-library/react'

import { KpiCard } from './KpiCard'

describe('KpiCard', () => {
  it('タイトルと数値を表示する', () => {
    render(<KpiCard title="対象企業数" value={42} />)
    expect(screen.getByText('対象企業数')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('文字列の値も表示できる', () => {
    render(<KpiCard title="平均スコア" value="0.0" />)
    expect(screen.getByText('0.0')).toBeInTheDocument()
  })
})
