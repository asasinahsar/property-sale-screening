/**
 * Auth feature - Business Logic Layer
 *
 * TanStack Query を用いた認証カスタム hooks。
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'

import { getMe, login, logout } from './api'
import type { LoginRequest, MeResponse } from './api'

export const authKeys = {
  me: ['auth', 'me'] as const,
}

/** 現在ログイン中のユーザー情報を取得 */
export function useGetMe(): UseQueryResult<MeResponse, Error> {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: getMe,
    retry: false,
  })
}

/** ログイン */
export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: LoginRequest) => login(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.me })
    },
  })
}

/** ログアウト */
export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => logout(),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: authKeys.me })
    },
  })
}

/**
 * 認証状態をまとめて扱うカスタムフック。
 */
export function useAuth() {
  const meQuery = useGetMe()
  const loginMutation = useLogin()
  const logoutMutation = useLogout()

  return {
    user: meQuery.data,
    isAuthenticated: !!meQuery.data,
    isLoading: meQuery.isLoading,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  }
}
