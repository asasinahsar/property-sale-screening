import { render, screen, fireEvent } from '@testing-library/react'

import { SearchBox } from './SearchBox'

describe('SearchBox', () => {
  it('プレースホルダーを表示する', () => {
    render(<SearchBox onSearch={jest.fn()} />)
    expect(
      screen.getByPlaceholderText(/含み益500億以上の小売業/),
    ).toBeInTheDocument()
  })

  it('文字数カウンターを表示する', () => {
    render(<SearchBox onSearch={jest.fn()} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: 'あいうえお' } })
    expect(screen.getByText('5 / 200')).toBeInTheDocument()
  })

  it('200字を超える入力は切り詰める', () => {
    render(<SearchBox onSearch={jest.fn()} />)
    const input = screen.getByRole('textbox') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'あ'.repeat(250) } })
    expect(input.value.length).toBe(200)
    expect(screen.getByText('200 / 200')).toBeInTheDocument()
  })

  it('Enter で onSearch が分類済みクエリで呼ばれる（証券コード）', () => {
    const onSearch = jest.fn()
    render(<SearchBox onSearch={onSearch} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '7203' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSearch).toHaveBeenCalledWith({
      kind: 'securities_code',
      value: '7203',
    })
  })

  it('Enter で onSearch が自然言語クエリで呼ばれる', () => {
    const onSearch = jest.fn()
    render(<SearchBox onSearch={onSearch} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '含み益500億以上の小売業' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSearch).toHaveBeenCalledWith({
      kind: 'nl',
      value: '含み益500億以上の小売業',
    })
  })

  it('空入力での Enter は onSearch を呼ばず onClear を呼ぶ', () => {
    const onSearch = jest.fn()
    const onClear = jest.fn()
    render(<SearchBox onSearch={onSearch} onClear={onClear} />)
    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '   ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(onSearch).not.toHaveBeenCalled()
    expect(onClear).toHaveBeenCalled()
  })
})
