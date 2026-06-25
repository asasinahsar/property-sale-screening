import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { LoginForm } from './LoginForm'

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

const loginMock = jest.fn()
jest.mock('../hooks', () => ({
  useAuth: () => ({
    login: loginMock,
    isLoggingIn: false,
  }),
}))

function renderForm() {
  const queryClient = new QueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <LoginForm />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  pushMock.mockReset()
  loginMock.mockReset()
})

describe('LoginForm', () => {
  it('入力フィールドとボタンを表示する', () => {
    renderForm()
    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument()
    expect(screen.getByLabelText('パスワード')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'ログイン' })).toBeInTheDocument()
  })

  it('空入力で送信するとバリデーションエラーを表示する', async () => {
    const user = userEvent.setup()
    renderForm()
    await user.click(screen.getByRole('button', { name: 'ログイン' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'メールアドレスとパスワードを入力してください',
    )
    expect(loginMock).not.toHaveBeenCalled()
  })

  it('正しい入力でログイン成功するとダッシュボードに遷移する', async () => {
    loginMock.mockResolvedValueOnce(undefined)
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('メールアドレス'), 'a@example.com')
    await user.type(screen.getByLabelText('パスワード'), 'password123')
    await user.click(screen.getByRole('button', { name: 'ログイン' }))

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        login_email: 'a@example.com',
        password: 'password123',
      })
    })
    expect(pushMock).toHaveBeenCalledWith('/dashboard')
  })

  it('401エラー時に認証エラーメッセージを表示する', async () => {
    loginMock.mockRejectedValueOnce(new Error('401'))
    const user = userEvent.setup()
    renderForm()

    await user.type(screen.getByLabelText('メールアドレス'), 'a@example.com')
    await user.type(screen.getByLabelText('パスワード'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'ログイン' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'メールアドレスまたはパスワードが正しくありません',
    )
    expect(pushMock).not.toHaveBeenCalled()
  })
})
