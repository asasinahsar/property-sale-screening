import { render, screen } from '@testing-library/react'

import { KpiCards } from './KpiCards'
import type { KpiSnapshotSchema } from '../types'

const snapshot: KpiSnapshotSchema = {
  id: 'snap-1',
  period_from: '2025-06-01',
  period_to: '2025-06-30',
  universe_coverage: 100,
  traceability_rate: 80,
  avg_structure_score: 55.5,
  reproducibility_score: 55.5,
  total_workload_min: 1200,
  workload_reduction_rate: 96,
  created_at: '2025-06-30T00:00:00Z',
}

describe('KpiCards', () => {
  it('5種類のKPIタイトルを表示する', () => {
    render(<KpiCards snapshot={snapshot} />)
    expect(screen.getByText('工数削減率')).toBeInTheDocument()
    expect(screen.getByText('再現性スコア')).toBeInTheDocument()
    expect(screen.getByText('ユニバースカバレッジ')).toBeInTheDocument()
    expect(screen.getByText('トレース可能率')).toBeInTheDocument()
    expect(screen.getByText('平均構造スコア')).toBeInTheDocument()
  })

  it('スナップショットの値をフォーマットして表示する', () => {
    render(<KpiCards snapshot={snapshot} />)
    expect(screen.getByText('96.0%')).toBeInTheDocument()
    expect(screen.getByText('100.0%')).toBeInTheDocument()
    expect(screen.getByText('80.0%')).toBeInTheDocument()
    // avg_structure_score と reproducibility_score は同値 55.5 が2つ
    expect(screen.getAllByText('55.5')).toHaveLength(2)
  })

  it('スナップショットが無い場合はプレースホルダを表示する', () => {
    render(<KpiCards snapshot={null} />)
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(5)
  })
})
