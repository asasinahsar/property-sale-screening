import { classifyQuery } from './searchQuery'

describe('classifyQuery', () => {
  it('空文字・空白のみは null を返す', () => {
    expect(classifyQuery('')).toBeNull()
    expect(classifyQuery('   ')).toBeNull()
  })

  it('4桁数字は証券コードとして扱う', () => {
    expect(classifyQuery('7203')).toEqual({
      kind: 'securities_code',
      value: '7203',
    })
  })

  it('短い企業名は完全一致（company_name）として扱う', () => {
    expect(classifyQuery('トヨタ自動車')).toEqual({
      kind: 'company_name',
      value: 'トヨタ自動車',
    })
  })

  it('条件キーワードを含む文は自然言語（nl）として扱う', () => {
    expect(classifyQuery('含み益500億以上の小売業')).toEqual({
      kind: 'nl',
      value: '含み益500億以上の小売業',
    })
  })

  it('PBR を含む文は自然言語として扱う', () => {
    expect(classifyQuery('PBR1倍割れ')).toEqual({
      kind: 'nl',
      value: 'PBR1倍割れ',
    })
  })

  it('空白を含む文は自然言語として扱う', () => {
    expect(classifyQuery('関西 不動産 含み益')).toEqual({
      kind: 'nl',
      value: '関西 不動産 含み益',
    })
  })

  it('前後の空白はトリムする', () => {
    expect(classifyQuery('  7203  ')).toEqual({
      kind: 'securities_code',
      value: '7203',
    })
  })
})
